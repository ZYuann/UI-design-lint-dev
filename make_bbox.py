import decimal
import os
import random
import shutil
import uuid
import zipfile

import matplotlib.image
from matplotlib import pyplot as plt

from post_process_spatial import *

def convert2sketch(dir_path, zip_name, sketch_name):
    zip = zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(dir_path):

        fpath = path.replace(dir_path, '')
        for filename in filenames:
            zip.write(os.path.join(path, filename), os.path.join(fpath, filename))
    zip.close()
    if os.path.exists(sketch_name):
        os.remove(sketch_name)
    os.rename(zip_name, sketch_name)
    print('saved in {}'.format(sketch_name))


def is_shape_two(tree):
    t = tree['_class']
    shape_list = ['slice', 'shapePath', 'text', 'symbolInstance', 'bitmap', 'oval']
    return t in shape_list


def convert2rectangle(node: dict, count):
    global merge_count
    if 'layers' in node.keys():
        merge_count += count_len(node) - 1
    name = '#' + node['name'] + '#'
    height = node['frame']['height']
    width = node['frame']['width']
    x = node['frame']['x']
    y = node['frame']['y']
    alpha = 1
    rotation = node['rotation']
    if 'style' in node.keys():
        if 'fills' in node['style'].keys() and node['style']['fills']:
            alpha = node['style']['fills'][0]['color']['alpha']
    isVisible = node['isVisible']
    return {
        "_class": "rectangle",
        "do_objectID": str(uuid.uuid1()),
        "booleanOperation": -1,
        "isFixedToViewport": False,
        "isFlippedHorizontal": False,
        "isFlippedVertical": False,
        "isLocked": False,
        "isVisible": isVisible,
        "layerListExpandedType": 0,
        "name": name,
        "nameIsFixed": False,
        "resizingConstraint": 63,
        "resizingType": 0,
        "rotation": rotation,
        "shouldBreakMaskChain": False,
        "exportOptions": {
            "_class": "exportOptions",
            "includedLayerIds": [],
            "layerOptions": 0,
            "shouldTrim": False,
            "exportFormats": []
        },
        "frame": {
            "_class": "rect",
            "constrainProportions": False,
            "height": height,
            "width": width,
            "x": x,
            "y": y
        },
        "clippingMaskMode": 0,
        "hasClippingMask": False,
        "style": {
            "_class": "style",
            "do_objectID": str(uuid.uuid1()),
            "endMarkerType": 0,
            "miterLimit": 0,
            "startMarkerType": 0,
            "windingRule": 1,
            "fills": [
                {
                    "_class": "fill",
                    "isEnabled": True,
                    "fillType": 0,
                    "color": {
                        "_class": "color",
                        "alpha": alpha,
                        "blue": color_list[0][count],
                        "green": color_list[1][count],
                        "red": color_list[2][count]
                    }
                }
            ]
        },
        "edited": False,
        "isClosed": True,
        "pointRadiusBehaviour": 1,
        "points": [
            {
                "_class": "curvePoint",
                "cornerRadius": 0,
                "curveFrom": "{0, 0}",
                "curveMode": 1,
                "curveTo": "{0, 0}",
                "hasCurveFrom": False,
                "hasCurveTo": False,
                "point": "{0, 0}"
            },
            {
                "_class": "curvePoint",
                "cornerRadius": 0,
                "curveFrom": "{1, 0}",
                "curveMode": 1,
                "curveTo": "{1, 0}",
                "hasCurveFrom": False,
                "hasCurveTo": False,
                "point": "{1, 0}"
            },
            {
                "_class": "curvePoint",
                "cornerRadius": 0,
                "curveFrom": "{1, 1}",
                "curveMode": 1,
                "curveTo": "{1, 1}",
                "hasCurveFrom": False,
                "hasCurveTo": False,
                "point": "{1, 1}"
            },
            {
                "_class": "curvePoint",
                "cornerRadius": 0,
                "curveFrom": "{0, 1}",
                "curveMode": 1,
                "curveTo": "{0, 1}",
                "hasCurveFrom": False,
                "hasCurveTo": False,
                "point": "{0, 1}"
            }
        ],
        "fixedRadius": 0,
        "needsConvertionToNewRoundCorners": False,
        "hasConvertedToNewRoundCorners": True,
        "layers": []
    }


def random_color(n_colors):
    # 生成随机颜色
    print('颜色字典生成.......')
    r_list, g_list, b_list, color_list = [], [], [], []
    levels = range(32, 256)
    for _ in range(n_colors):
        red, green, blue = tuple(random.choice(levels) for _ in range(3))
        r_list.append(red)
        g_list.append(green)
        b_list.append(blue)
    color_list.append(r_list)
    color_list.append(g_list)
    color_list.append(b_list)
    np.save('color.npy', color_list)
    return r_list, g_list, b_list


# random_color(10000)
# cc = np.load('color.npy').T
# print(cc[0])
# exit(0)
def fix_radius(tree: dict):
    if 'fixedRadius' in tree.keys():
        tree['fixedRadius'] = 0
    if 'points' in tree.keys():
        for point in tree['points']:
            point['cornerRadius'] = 0
    return tree


class CallingCounter(object):
    def __init__(self, func):
        self.func = func
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        return self.func(*args, **kwargs)


def fix_merge(node: dict, count):
    if node['isVisible'] and '#merge#' in node['name']:
        return convert2rectangle(node, count)
    else:
        return node


def preprocessing(tree: dict):
    '''
    预处理，删除不可见图层
    :param tree:
    :return:
    '''
    if 'layers' not in tree.keys():
        return
    remove_indexes = []
    for index, child in enumerate(tree['layers']):
        if not child['isVisible']:
            remove_indexes.append(index)
        else:
            preprocessing(child)
    tree['layers'] = [child for i, child in enumerate(tree['layers']) if i not in remove_indexes]


def unzip_file(file_name, zip_name):
    if os.path.exists(file_name):
        shutil.rmtree(file_name)
    try:
        zip_file = zipfile.ZipFile(zip_name)
        zip_list = zip_file.namelist()  # 得到压缩包里所有文件
        for f in zip_list:
            zip_file.extract(f, file_name)  # 循环解压文件到指定目录
        zip_file.close()  # 关闭文件，必须有，释放内存
        print('解压成功')
    except:
        print('解压失败')


# 计算任意一个节点的子节点 + 1的数目
def count_len(tree: dict):
    def dfs(node: dict):
        total_len = 0
        if node is None or 'layers' not in node.keys():
            return 0
        total_len += len(node['layers'])
        for child in node['layers']:
            total_len += dfs(child)
        return total_len

    return dfs(tree) + 1


def process_rectangle(node: dict, count):
    name = '*' + node['name'] + '*'
    height = node['frame']['height']
    width = node['frame']['width']
    x = node['frame']['x']
    y = node['frame']['y']
    alpha = 1
    rotation = node['rotation']
    gradient = {}
    fillType = 0
    if 'style' in node.keys():
        if 'fills' in node['style'].keys() and node['style']['fills']:
            fillType = node['style']['fills'][0]['fillType']
            alpha = node['style']['fills'][0]['color']['alpha']
            if 'gradient' in node['style']['fills'][0].keys():
                gradient = node['style']['fills'][0]['gradient']
    isVisible = node['isVisible']
    hasClippingMask = node['hasClippingMask']
    return {
        "_class": "rectangle",
        "do_objectID": str(uuid.uuid1()),
        "booleanOperation": -1,
        "isFixedToViewport": False,
        "isFlippedHorizontal": False,
        "isFlippedVertical": False,
        "isLocked": False,
        "isVisible": isVisible,
        "layerListExpandedType": 0,
        "name": name,
        "nameIsFixed": False,
        "resizingConstraint": 63,
        "resizingType": 0,
        "rotation": rotation,
        "shouldBreakMaskChain": False,
        "exportOptions": {
            "_class": "exportOptions",
            "includedLayerIds": [],
            "layerOptions": 0,
            "shouldTrim": False,
            "exportFormats": []
        },
        "frame": {
            "_class": "rect",
            "constrainProportions": False,
            "height": height,
            "width": width,
            "x": x,
            "y": y
        },
        "clippingMaskMode": 0,
        "hasClippingMask": hasClippingMask,
        "style": {
            "_class": "style",
            "do_objectID": str(uuid.uuid1()),
            "endMarkerType": 0,
            "miterLimit": 10,
            "startMarkerType": 0,
            "windingRule": 1,
            "fills": [
                {
                    "_class": "fill",
                    "isEnabled": True,
                    "fillType": fillType,
                    "color": {
                        "_class": "color",
                        "alpha": alpha,
                        "blue": color_list[0][count],
                        "green": color_list[1][count],
                        "red": color_list[2][count]
                    },
                    "gradient": gradient,
                    "noiseIndex": 0,
                    "noiseIntensity": 0,
                    "patternFillType": 1,
                    "patternTileScale": 1,
                }
            ]
        },
        "edited": False,
        "isClosed": True,
        "pointRadiusBehaviour": 1,
        "points": [
            {
                "_class": "curvePoint",
                "cornerRadius": 0,
                "curveFrom": "{0, 0}",
                "curveMode": 1,
                "curveTo": "{0, 0}",
                "hasCurveFrom": False,
                "hasCurveTo": False,
                "point": "{0, 0}"
            },
            {
                "_class": "curvePoint",
                "cornerRadius": 0,
                "curveFrom": "{1, 0}",
                "curveMode": 1,
                "curveTo": "{1, 0}",
                "hasCurveFrom": False,
                "hasCurveTo": False,
                "point": "{1, 0}"
            },
            {
                "_class": "curvePoint",
                "cornerRadius": 0,
                "curveFrom": "{1, 1}",
                "curveMode": 1,
                "curveTo": "{1, 1}",
                "hasCurveFrom": False,
                "hasCurveTo": False,
                "point": "{1, 1}"
            },
            {
                "_class": "curvePoint",
                "cornerRadius": 0,
                "curveFrom": "{0, 1}",
                "curveMode": 1,
                "curveTo": "{0, 1}",
                "hasCurveFrom": False,
                "hasCurveTo": False,
                "point": "{0, 1}"
            }
        ],
        "fixedRadius": 0,
        "needsConvertionToNewRoundCorners": False,
        "hasConvertedToNewRoundCorners": True,
        "layers": []
    }


def process_shapeGroup(node: dict):
    if node['_class'] == 'shapeGroup':
        node['_class'] = 'group'
        node['resizingConstraint'] = 63
        node['layerListExpandedType'] = 0
        node['style'] = {
            "_class": "style",
            "do_objectID": str(uuid.uuid1()),
            "endMarkerType": 0,
            "miterLimit": 10,
            "startMarkerType": 0,
            "windingRule": 1,
            "fills": []
        }


def generate_color_map(tree: dict, is_merge: bool):
    def process_layer(node: dict, fill_dict, count):
        process_shapeGroup(node)
        fix_radius(node)
        if is_merge:
            fix_merge(node, count)
        # 是shape two类型 并且 是叶子节点
        if is_shape_two(node) and ('layers' not in node.keys() or len(node['layers']) == 0):
            node = convert2rectangle(node, count)
        # 处理考虑gradient
        elif node['_class'] == 'rectangle':
            node = process_rectangle(node, count)
        else:
            if 'style' in node.keys() and 'fills' in node['style'].keys() and node['_class'] != 'group':
                print('class', node['_class'])
                if len(node['style']['fills']):
                    node['style']['fills'] = fill_dict
        return node

    # 图层填充色修正
    @CallingCounter
    def traverse(node, level=0):
        global layer_reduce_count
        count = traverse.count - 1 + layer_reduce_count
        fill_dict = [{"_class": "fill",
                      "isEnabled": True, "fillType": 0,
                      "color": {"_class": "color", "alpha": 1, "blue": color_list[0][count],
                                "green": color_list[1][count], "red": color_list[2][count]}}]

        if node['isVisible'] and 'merge' in node['name']:
            c = count_len(node)
        if 'merge' in node['name']:
            # print(node['name'], count, count+c-1)
            node = process_layer(node, fill_dict, count + c - 1)
        else:
            node = process_layer(node, fill_dict, count)
        # print('count:{} name:{}'.format(count, node['name']))

        if node['isVisible'] and 'merge' in node['name']:
            c -= count_len(node)
            layer_reduce_count += c

        if 'layers' in node.keys():
            for i in range(len(node['layers'])):
                child = node['layers'][i]
                node['layers'][i] = traverse(child, level + 1)

        return node

    tree = traverse(tree, 0)

    return tree


def generate_json(tree: dict):
    '''
    生成一个生成包含name bounding box color layers的json文件
    :param tree: 原生json
    :return: new json
    '''
    json_file: list = []

    def dfs(node: dict, current_position, relation_position):
        name = node['name']
        # node['frame']['x'], node['frame']['y'] = node['frame']['x'] + current_position[0], node['frame']['y'] + current_position[1]
        if (node['frame']['x'], node['frame']['y']) != relation_position:
            node['frame']['x'], node['frame']['y'] = node['frame']['x'] + current_position[0] \
                                                     - relation_position[0], node['frame']['y'] + current_position[1] - \
                                                     relation_position[1]
        frame = {
            'height': node['frame']['height'],
            'width': node['frame']['height'],
            'x': node['frame']['x'],
            'y': node['frame']['y'],
        }
        if len(node['style']['fills']):
            color = {
                "blue": node['style']['fills'][0]['color']['blue'],
                "green": node['style']['fills'][0]['color']['green'],
                "red": node['style']['fills'][0]['color']['red']
            }
        else:
            color = {}
        json_file.append({
            'name': name,
            'frame': frame,
            'color': color
        })
        if 'layers' in node.keys():
            for child in node['layers']:
                dfs(child, (node['frame']['x'] + current_position[0], node['frame']['y'] + current_position[1]),
                    relation_position)

    for root in tree['layers']:
        root_position = (root['frame']['x'], root['frame']['y'])
        dfs(root, (0, 0), root_position)

    try:
        with open('post_process.json', 'w') as f:
            json.dump(json_file, f)
    except:
        print('保存失败')
    return tree


def normalize(pos1, pos2, new_img_size=(750, 750)):
    def handle(value):
        value = str(value)
        value = decimal.Decimal("%.6f" % float(value))
        return value

    pos1 = [pos1[0], pos1[1]]
    pos2 = [pos2[0], pos2[1]]

    max_h, max_w = new_img_size
    w = abs(pos1[0] - pos2[0])
    h = abs(pos1[1] - pos2[1])
    print('w:{}h:{}'.format(w, h))
    pos_center = [pos1[0] + w / 2, pos1[1] + h / 2]
    raw = [handle(pos_center[0]), handle(pos_center[1]), handle(w), handle(h)]

    # raw = [handle(pos_center[0] / max_w), handle(pos_center[1] / max_h), handle(w / max_w), handle(h / max_h)]
    # norm = [float(i)/sum(raw) for i in raw]
    return raw


def flatten(tree: dict):
    '''
    打平设计稿，消除层级结构
    :param tree: json
    :return: layers_list
    '''
    result = []
    top_layer_list = []
    bottom_layer_list = []

    def dfs(search_root: dict, current_position, relation_position):
        if not search_root['isVisible']:
            return
        if 'layers' in search_root.keys():
            for child in search_root['layers']:
                dfs(child, (
                    search_root['frame']['x'] + current_position[0], search_root['frame']['y'] + current_position[1]),
                    relation_position)
        if (search_root['frame']['x'], search_root['frame']['y']) != relation_position and search_root['isVisible']:

            search_root['layers'] = []

            if search_root['_class'] == 'text' or str(search_root['name']).find('蒙版') != -1 or str(
                    search_root['name']).strip() == '蒙版':
                # Text和蒙版 放顶层
                search_root['frame']['x'], search_root['frame']['y'] = search_root['frame']['x'] + current_position[
                    0], search_root['frame']['y'] + current_position[1]
                top_layer_list.append(search_root)
            else:
                search_root['frame']['x'], search_root['frame']['y'] = search_root['frame']['x'] + current_position[0] \
                                                                       - relation_position[0], search_root['frame'][
                                                                           'y'] + current_position[1] - \
                                                                       relation_position[1]
                if str(search_root['name']).find('白底') == -1 or str(search_root['name']).find('编组') == -1 or str(
                        search_root['name']).find('Group') == -1:
                    result.append(search_root)
                else:
                    bottom_layer_list.append(search_root)
        # print(search_root['name'],search_root['do_objectID'],search_root['frame']['x'], search_root['frame']['y'])

    for root in tree['layers']:
        root_position = (root['frame']['x'], root['frame']['y'])
        dfs(root, (0, 0), root_position)
        result = [*bottom_layer_list, *result]
        root['layers'] = result

    tree['layers'] = [*tree['layers'], *top_layer_list]

    return tree


def generate_bbox(tree: dict, figure_name):
    '''
    生成bounding box 标注
    :param tree: 得到绝对位置的图层
    :return:
    '''
    bbox_list = []

    def traverse(node: dict):

        if 'merge' in node['name']:
            height = node['frame']['height']
            width = node['frame']['width']
            x = node['frame']['x']
            y = node['frame']['y']
            print('\nname:{}-height:{} width:{} x:{} y:{}'.format(node['name'], height, width, x, y))
            raw = normalize([x, y], [x + width, y + height])
            bbox = [0, *raw]
            bbox_list.append(bbox)
        if 'layers' in node.keys():
            for i in range(len(node['layers'])):
                child = node['layers'][i]
                node['layers'][i] = traverse(child)

        return node

    tree = traverse(tree)
    with open("./labels/{}.txt".format(figure_name), 'w') as file:
        for idx, row in enumerate(bbox_list):
            s = " ".join(map(str, row))
            file.write(s + '\n')
    return tree


def process(json_list):
    is_merge = False
    for i in range(len(json_list)):
        global merge_count, layer_reduce_count
        file_path = json_list[i].split('/', 2)
        file_name = file_path[0] + '/' + file_path[1]
        unzip_file(file_name=file_name, zip_name=file_name + '.zip')
        print('open file: ', file_name)
        tree = json.load(open(json_list[i], encoding='utf-8'))
        preprocessing(tree)  # 预处理
        new_tree = generate_color_map(tree, is_merge)  # 合并merge
        if get_bbox:
            flatten(new_tree)  # 得到打平结构的设计稿
            print('取消层级结构！')
            # todo 修复两个相同设计稿会出现两次 例: 宝贝
            # 得到标注的 bbox
            generate_bbox(new_tree, figure_name=saved_name)  # 保存bbox的txt文件
        print('merge_count', merge_count)
        print('layer_reduce_count', layer_reduce_count)
        merge_count = 0
        layer_reduce_count = 0
        with open(json_list[i], 'w') as f:
            # json.dump(new_tree, f)
            json.dump(new_tree, f)
        if is_merge:
            convert2sketch(file_name, 'test.zip', file_path[1] + '-merge.sketch')
        else:
            convert2sketch(file_name, 'test.zip', file_path[1] + '.sketch')


def image_split(im_path, label_path):
    # 归一化为yolo格式
    def normalize_labels(label, new_img_size=(750, 750)):
        def handle(value):
            value = str(value)
            value = decimal.Decimal("%.6f" % float(value))
            return value

        max_h, max_w = new_img_size
        pos_center = [label[1], label[2]]
        w, h = label[3], label[4]
        raw = [handle(pos_center[0] / max_w), handle(pos_center[1] / max_h), handle(w / max_w), handle(h / max_h)]
        # print(raw_list)
        return raw

    # 删除空标签
    def delete_null_file():
        files = os.listdir('./labels/')
        for file in files:
            if os.path.getsize('./labels/' + file) == 0:
                os.remove('./labels/' + file)
                print(file + ' deleted.')

    # 宽度固定，根据高度分割
    def split_label_height(img, label_path, new_img_size=(750, 750)):
        step = 0
        new_h, new_w = new_img_size
        h, w = img.shape[0], img.shape[1]

        # 1. 读取原始的label文件
        labels_array = pandas.read_csv(label_path, sep=' ', encoding='utf-8', header=None)
        labels_array.drop_duplicates(inplace=True)  # 去除重复行
        # print(labels_array[2].values)
        for i in range(0, h, new_h):
            label_list = []
            for value in labels_array.values:
                if 750 * step < value[2] < 750 * (step + 1):
                    value[2] = value[2] - 750 * step
                    # print('value:', value)
                    value = normalize_labels(value, new_img_size)
                    label_list.append(value)
            with open("./labels/{}{}.txt".format(saved_name, step), 'w') as file:
                for idx, row in enumerate(label_list):
                    s = " ".join(map(str, [0, *row]))
                    file.write(s + '\n')
            step += 1

    def split_img_height(img, new_img_size=(750, 750)):
        h, w = img.shape[0], img.shape[1]
        new_h, new_w = new_img_size
        step = 0
        for i in range(0, h, new_h):
            matplotlib.image.imsave('./images/{}{}.png'.format(saved_name, step),
                                    img[step * new_h: new_h * (step + 1), :, :])
            step += 1

    # 1. 保存分割后图片
    images = plt.imread(im_path)
    new_size = (750, 750)
    split_img_height(images, new_img_size=new_size)

    # 2. 保存分割后的标签
    split_label_height(images, label_path, new_img_size=new_size)  # todo 根据实际情况调整

    # print('label_list', labels_array)
    # 3. 删除空文件
    delete_null_file()


if __name__ == '__main__':
    color_list = np.load('color.npy').tolist()
    merge_count = 0
    layer_reduce_count = 0
    json_list = [
        # 'sketch文件/洋淘大赏2/pages/ACD24EC7-29B4-4469-834E-04A0331CFDEA.json',
        'sketch文件/关联图层合并-天猫特选/pages/4B0C7F70-87CF-4F89-B3C2-89537D5B4C7E.json',
        # 'sketch文件/关联图层合并-划算排行/pages/5B48DB31-FEC1-4228-8407-2685D926EF14.json',
        # 'sketch文件/关联图层合并-亲宝贝/pages/DCA074DE-7085-4DC8-B038-E82ED277267A.json',
        # 'sketch文件/洋淘大赏2/pages/ACD24EC7-29B4-4469-834E-04A0331CFDEA.json',
        # 'sketch文件/关联图层合并-聚划算/pages/B9AE0C64-2E86-457C-AFBB-FEA85DDEEB94.json',
        # 'sketch文件/天猫U先中间页二期优化视觉终稿_20201218/pages/43DDA08B-1869-4321-964B-E182C34D8837.json',
    ]
    saved_name = 'texuan'
    get_bbox = True
    process(json_list)

    if get_bbox:
        im_path = './images/{}.png'.format(saved_name)
        label_path = './labels/{}.txt'.format(saved_name)
        image_split(im_path, label_path)
        ##### 后处理部分
        # img_path = './images/baby0.png'
        # label_path = './labels/baby0.txt'
        # flatten_tree = json.load(open(json_list, encoding='utf-8'))
        # get_layer_id(img_path, label_path, flatten_tree)