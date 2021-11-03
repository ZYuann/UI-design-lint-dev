import json
import os
import random
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
    # shutil.copy(zip_name, 'temp.zip')
    if os.path.exists(sketch_name):
        os.remove(sketch_name)
    os.rename(zip_name, sketch_name)
    print('saved in {}'.format(sketch_name))


def is_shape_one(tree):
    t = tree['_class']
    return t == 'rectangle' or t == 'Mask'


def is_shape_two(tree):
    t = tree['_class']
    shape_list = ['slice', 'shapePath', 'shapeGroup', 'text', 'symbolInstance', 'bitmap', 'oval']
    return (t in shape_list)


def convert2rectangle(tree):
    name = '#' + tree['name'] + '#'
    height = tree['frame']['height']
    width = tree['frame']['width']
    x = tree['frame']['x']
    y = tree['frame']['y']
    alpha = 1
    rotation = tree['rotation']
    if 'style' in tree.keys():
        if 'fills' in tree['style'].keys():
            alpha = tree['style']['fills'][0]['color']['alpha']
    isVisible = tree['isVisible']
    rectangle_fill = {
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
                        "blue": np.random.rand(),
                        "green": np.random.rand(),
                        "red": np.random.rand()
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
        "hasConvertedToNewRoundCorners": True
    }
    return rectangle_fill


def random_color(n_colors):
    # 生成随机颜色
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

def fix_radius(tree: dict):
    if 'fixedRadius' in tree.keys():
        tree['fixedRadius'] = 0
    if 'points' in tree.keys():
        for point in tree['points']:
            point['cornerRadius'] = 0
    return tree


def isshape(node):
    t = node['_class']
    return t == 'oval' or t == 'shapePath' or t == 'rectangle'


def preprocessing(tree):
    if 'layers' in tree.keys():
        ifshape = True
        for i in range(len(tree['layers'])):
            child = tree['layers'][i]
            tree['layers'][i] = preprocessing(child)
        for i in range(len(tree['layers'])):
            child = tree['layers'][i]
            if not isshape(child):
                ifshape = False
        if ifshape:
            tree = convert2rectangle(tree)

    return tree


def fix_shape(tree: dict):
    # 1. 判断当前节点是否有子节点
    # 2. 判断子节点下是否全为shape
    # 3. 将当前节点替换
    is_shape = True
    if 'layers' in tree.keys():
        for child in tree['layers']:
            if child['_class'] != 'rectangle':
                is_shape = False
    else:
        is_shape = False
    if is_shape:
        print(tree['name'])
        tree = convert2rectangle(tree)
        # tree['isleaf'] = True

    return tree


def add_fill(tree: dict):
    def traverse(tree, level=0):
        fill_dict = [{"_class": "fill",
                      "isEnabled": True, "fillType": 0,
                      "color": {"_class": "color", "alpha": 1, "blue": np.random.rand(),
                                "green": np.random.rand(), "red": np.random.rand()}}]
        # if tree['name'] == 'Mask':
        # 没有类型为mask
        #     print(tree['_class'])
        tree = fix_radius(tree)
        tree = fix_shape(tree)
        if is_shape_two(tree):
            tree = convert2rectangle(tree)
        else:
            # 如果有style字段，进行填充
            if 'style' in tree.keys():
                tree['style']['fills'] = fill_dict
        if 'layers' in tree.keys():
            # 遍历节点
            for i in range(len(tree['layers'])):
                child = tree['layers'][i]
                tree['layers'][i] = traverse(child, level + 1)

                if 'layers' not in child.keys():
                    # 判断是孩子节点，就对其父进行填充
                    if 'style' in tree.keys():
                        tree['style']['fills'] = fill_dict
                    else:
                        print(tree['name'])
                    # if is_shape_one(child):
                    #     # 判断孩子节点的shape，符合就对其填充
                    #     child['style']['fills'] = fill_dict

        return tree

    preprocessing(tree)
    traverse(tree, 0)
    return tree


def unzip_file(file_name, zip_name):
    try:
        zip_file = zipfile.ZipFile(zip_name)
        zip_list = zip_file.namelist()  # 得到压缩包里所有文件
        for f in zip_list:
            zip_file.extract(f, file_name)  # 循环解压文件到指定目录
        print('解压成功')
    except:
        zip_file.close()  # 关闭文件，必须有，释放内存


def generate_color_map(tree: dict):
    color_list = np.load('color.npy')
    color_list = color_list.tolist()

    def traverse(tree, level=0):
        global count
        print('count:{}'.format(count))
        fill_dict = [{"_class": "fill",
                      "isEnabled": True, "fillType": 0,
                      "color": {"_class": "color", "alpha": 1, "blue": color_list[0][count],
                                "green": color_list[1][count], "red": color_list[2][count]}}]
        tree = fix_radius(tree)
        tree = fix_shape(tree)
        if is_shape_two(tree):
            tree = convert2rectangle(tree)
        else:
            # 如果有style字段，进行填充
            if 'style' in tree.keys():
                tree['style']['fills'] = fill_dict
        if 'layers' in tree.keys():
            # 遍历节点
            for i in range(len(tree['layers'])):
                child = tree['layers'][i]
                tree['layers'][i] = traverse(child, level + 1)

                if 'layers' not in child.keys():
                    # 判断是孩子节点，就对其父进行填充
                    if 'style' in tree.keys():
                        tree['style']['fills'] = fill_dict
                    # else:
                    #     print(tree['name'])
        count = count + 1
        return tree

    # preprocessing(tree)
    traverse(tree, 0)
    return tree


def process(json_list):
    for i in range(len(json_list)):
        file_path = json_list[i].split('/', 2)
        file_name = file_path[0] + '/' + file_path[1]
        print('open file: ', file_name)
        unzip_file(file_name=file_name, zip_name=file_name + '.zip')
        tree = json.load(open(json_list[i], encoding='utf-8'))
        # new_tree = add_fill(tree)
        new_tree = generate_color_map(tree)
        with open(json_list[i], 'w') as f:
            json.dump(new_tree, f)
        convert2sketch(file_name, 'test.zip', file_path[1] + '.sketch')


if __name__ == '__main__':
    count = 0
    json_list = [
        'sketch文件/baby-test/pages/D2D26594-067C-4E4D-B9F0-98654C24D350.json'
        # 'sketch文件/关联图层合并-天猫特选/pages/4B0C7F70-87CF-4F89-B3C2-89537D5B4C7E.json',
        # 'sketch文件/关联图层合并-划算排行/pages/5B48DB31-FEC1-4228-8407-2685D926EF14.json',
        # 'sketch文件/关联图层合并-亲宝贝/pages/DCA074DE-7085-4DC8-B038-E82ED277267A.json',
        # 'sketch文件/洋淘大赏2/pages/ACD24EC7-29B4-4469-834E-04A0331CFDEA.json',
    ]
    process(json_list)
