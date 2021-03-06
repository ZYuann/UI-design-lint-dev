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
    shape_list = ['slice', 'shapePath', 'text', 'symbolInstance', 'bitmap', 'oval']
    return t in shape_list


def convert2rectangle(node: dict, count, fill_dict):
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
            "fills": fill_dict,
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
    # ??????????????????
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


def fix_merge(node: dict, count, fill_dict):
    if 'merge' in node['name'] or 'merge-back' in node['name']:
        return convert2rectangle(node, count, fill_dict)
    else:
        return node


def preprocessing(tree: dict):
    '''
    ?????????????????????????????????
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
        zip_list = zip_file.namelist()  # ??????????????????????????????
        for f in zip_list:
            zip_file.extract(f, file_name)  # ?????????????????????????????????
        zip_file.close()  # ???????????????????????????????????????
        print('????????????')
    except:
        print('????????????')


# ???????????????????????????????????? + 1?????????
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


def process_rectangle(node: dict, count, fill_dict):
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
            "fills": fill_dict
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


def generate_color_map(tree: dict, is_merge: bool):
    def process_layer(node: dict, fill_dict, count):

        process_shapeGroup(node)  # ??????shapeGroup
        node = fix_radius(node)  # ????????????
        if is_merge:
            node = fix_merge(node, count, fill_dict)  # ???????????????????????????
        # ???????????????
        if is_shape_two(node) and ('layers' not in node.keys() or len(node['layers']) == 0):
            node = convert2rectangle(node, count, fill_dict)
        # ????????????gradient
        elif node['_class'] == 'rectangle':
            node = process_rectangle(node, count, fill_dict)
        else:
            if 'style' in node.keys() and 'fills' in node['style'].keys():
                node['style']['fills'] = fill_dict

        return node

    # ?????????????????????
    @CallingCounter
    def traverse(node, level=0):
        global layer_reduce_count
        count = traverse.count - 1 + layer_reduce_count
        # 1. ????????????????????????
        # 2. ??????????????????
        # 3. ??????????????????
        fill_dict_blue = [{"_class": "fill",
                           "isEnabled": True, "fillType": 0,
                           "color": {"_class": "color", "alpha": 1, "blue": 1,
                                     "green": 0, "red": 0}}]
        fill_dict_red = [{"_class": "fill",
                          "isEnabled": True, "fillType": 0,
                          "color": {"_class": "color", "alpha": 1, "blue": 0,
                                    "green": 0, "red": 1}}]
        fill_dict_green = [{"_class": "fill",
                            "isEnabled": True, "fillType": 0,
                            "color": {"_class": "color", "alpha": 1, "blue": 0,
                                      "green": 1, "red": 0}}]

        if node['isVisible'] and 'merge' in node['name']:
            c = count_len(node)
        if 'merge-back' in node['name']:
            print(node['name'], count, count + c - 1)
            node = process_layer(node, fill_dict_green, count + c - 1)
        elif 'merge' in node['name']:
            # print(node['name'])
            node = process_layer(node, fill_dict_red, count + c - 1)
        else:
            node = process_layer(node, fill_dict_blue, count)
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
    ????????????????????????name boundingbox color layers???json??????
    :param tree: ??????json
    :return: new json
    '''
    json_file: list = []

    def dfs(node: dict, current_position, relation_position):
        name = node['name']
        # node['frame']['x'], node['frame']['y'] = node['frame']['x'] + current_position[0], node['frame']['y'] + current_position[1]
        if (node['frame']['x'], node['frame']['y']) != relation_position:
            node['frame']['x'], node['frame']['y'] = node['frame']['x'] + current_position[
                0] - relation_position[0], node['frame']['y'] + current_position[1] - relation_position[1]
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
        print('????????????')
    return tree


def process(json_list):
    is_merge = True
    for i in range(len(json_list)):
        global merge_count, layer_reduce_count
        file_path = json_list[i].split('/', 2)
        file_name = file_path[0] + '/' + file_path[1]
        unzip_file(file_name=file_name, zip_name=file_name + '.zip')  # ????????????
        print('open file: ', file_name)
        tree = json.load(open(json_list[i], encoding='utf-8'))
        preprocessing(tree)  # ?????????????????????
        new_tree = generate_color_map(tree, is_merge)
        # generate_json(new_tree)  # ???????????????????????????
        print('merge_count', merge_count)
        print('layer_reduce_count', layer_reduce_count)
        merge_count = 0
        layer_reduce_count = 0
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
        # 'sketch??????/baby/pages/DCA074DE-7085-4DC8-B038-E82ED277267A.json',
        # 'sketch??????/??????????????????-????????????/pages/4B0C7F70-87CF-4F89-B3C2-89537D5B4C7E.json',
        # 'sketch??????/??????????????????-????????????/pages/5B48DB31-FEC1-4228-8407-2685D926EF14.json',
        # 'sketch??????/??????????????????-?????????/pages/DCA074DE-7085-4DC8-B038-E82ED277267A.json',
        'sketch??????/????????????2/pages/ACD24EC7-29B4-4469-834E-04A0331CFDEA.json',
    ]
    process(json_list)
