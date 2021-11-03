import json
import os
import random
import shutil
import uuid
import zipfile

import numpy as np


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
    shape_list = ['slice', 'shapePath', 'shapeGroup', 'text', 'symbolInstance', 'bitmap', 'oval']
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
    r_list, g_list, b_list, color_list = [], [], [], []
    levels = range(32, 256)
    for _ in range(n_colors):
        red, green, blue = tuple(random.choice(levels) for _ in range(3))
        # red /= 256
        # blue /= 256
        # green /= 256
        r_list.append(red)
        g_list.append(green)
        b_list.append(blue)
    color_list.append(r_list)
    color_list.append(g_list)
    color_list.append(b_list)
    np.save('color.npy', color_list)
    return r_list, g_list, b_list


# random_color(10000)
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
    if node['isVisible'] and 'merge' in node['name']:
        # print(node['name'])
        return convert2rectangle(node, count)
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


def generate_color_map(tree: dict, is_merge: bool):
    def process_layer(node: dict, fill_dict, count):
        if is_merge:
            node = fix_merge(node, count)
        node = fix_radius(node)
        # 对图层处理
        if is_shape_two(node) and ('layers' not in node.keys() or len(node['layers']) == 0):
            node = convert2rectangle(node, count)
        # 处理考虑gradient
        elif node['_class'] == 'rectangle':
            node = process_rectangle(node, count)
        else:
            if 'style' in node.keys() and len(node['style']['fills']):
                node['style']['fills'] = fill_dict
        return node

    # 图层填充色修正
    @CallingCounter
    def traverse(node, level=0):
        global layer_reduce_count
        count = traverse.count - 1 + layer_reduce_count
        print('count:{} name:{}'.format(count, node['name']))
        fill_dict = [{"_class": "fill",
                      "isEnabled": True, "fillType": 0,
                      "color": {"_class": "color", "alpha": 1, "blue": color_list[0][count],
                                "green": color_list[1][count], "red": color_list[2][count]}}]

        if node['isVisible'] and 'merge' in node['name']:
            c = count_len(node)
        node = process_layer(node, fill_dict, count)
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


def flatten(tree: dict):
    '''
    打平设计稿，消除层级结构
    :param tree: json
    :return: layers_list
    '''
    layers_list = []

    # below_root_list = []
    # for root in tree['layers']:
    #     below_root_list.append([])
    #     if 'layers' in root.keys():
    #         below_root_list[-1].extend([node['do_objectID'] for node in root['layers']])
    #
    # # 判断是否在设计稿的root下面一层
    # def is_below_root(node: dict, index: int):
    #     return node['do_objectID'] in below_root_list[index]

    #
    # # DFS 和 DP
    # # 区别：DP是有记忆的DFS
    # # node['_class']

    # search_root ->> target

    # search_root
    #      |
    # target_object_id
    #      |
    # xx
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
    # root['frame']['x'], root['frame']['y'] = root_position

    # # 计算叶子节点的绝对位置
    # def get_all_leaf(tree: dict, position: dict):
    #
    #     if 'layers' not in tree.keys() or len(tree['layers']) == 0:
    #         tree['frame']['x'] = position['x']
    #         tree['frame']['y'] = position['y']
    #         layers_list.append(tree)
    #
    #     else:
    #         for child in tree['layers']:
    #             print(child['name'])
    #             print('position', position)
    #             get_all_leaf(child, {'x': child['frame']['x'] + position['x'], 'y': child['frame']['y'] + position['y']})

    # print('before tree[layers]', count_len(tree))
    # get_all_leaf(tree, {'x': 0, 'y': 0})
    # tree['layers'][0]['layers'] = layers_list
    # print('after tree[layers]', count_len(tree))

    return tree


def process(json_list):
    is_merge = True
    for i in range(len(json_list)):
        file_path = json_list[i].split('/', 2)
        file_name = file_path[0] + '/' + file_path[1]
        unzip_file(file_name=file_name, zip_name=file_name + '.zip')
        print('open file: ', file_name)
        tree = json.load(open(json_list[i], encoding='utf-8'))
        flatten(tree)
        with open(json_list[i], 'w') as f:
            json.dump(tree, f)
        convert2sketch(file_name, 'test.zip', file_path[1] + '-flatten.sketch')

        exit(0)
        preprocessing(tree)
        new_tree = generate_color_map(tree, is_merge)
        with open(json_list[i], 'w') as f:
            json.dump(new_tree, f)
        if is_merge:
            convert2sketch(file_name, 'test.zip', file_path[1] + '-merge.sketch')
        else:
            convert2sketch(file_name, 'test.zip', file_path[1] + '.sketch')


if __name__ == '__main__':
    color_list = np.load('color.npy')
    color_list = color_list.tolist()
    merge_count = 0
    layer_reduce_count = 0
    json_list = [
        # 'sketch文件/baby-test/pages/D2D26594-067C-4E4D-B9F0-98654C24D350.json'
        # 'sketch文件/关联图层合并-天猫特选/pages/4B0C7F70-87CF-4F89-B3C2-89537D5B4C7E.json',
        # 'sketch文件/关联图层合并-划算排行/pages/5B48DB31-FEC1-4228-8407-2685D926EF14.json',
        'sketch文件/关联图层合并-亲宝贝/pages/DCA074DE-7085-4DC8-B038-E82ED277267A.json',
        # 'sketch文件/洋淘大赏2/pages/ACD24EC7-29B4-4469-834E-04A0331CFDEA.json',
        # 'sketch文件/亲宝贝-flatten/pages/DCA074DE-7085-4DC8-B038-E82ED277267A.json'
    ]
    process(json_list)
    print('merge_count', merge_count)
    print('layer_reduce_count', layer_reduce_count)
