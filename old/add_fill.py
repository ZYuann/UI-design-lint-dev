import json
import os
import random
import shutil
import zipfile

import cv2
import numpy as np


def convert2sketch(dir_path, zip_name, sketch_name):
    """
    压缩指定文件夹
    :param dir_path: 目标文件夹路径
    :param zip_name: 压缩文件保存路径+xxxx.zip
    :param sketch_name: 转换成sketch的名字
    :return: 无
    """
    zip = zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(dir_path):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(dir_path, '')
        for filename in filenames:
            zip.write(os.path.join(path, filename), os.path.join(fpath, filename))
    zip.close()
    shutil.copy(zip_name, 'copy.zip')
    if os.path.exists(sketch_name):
        os.remove(sketch_name)
    os.rename(zip_name, sketch_name)
    print('saved in {}'.format(sketch_name))


def is_shape(node):
    # 需要对子节点填充的shape
    t = node['_class']
    return t == 'rectangle' or t == 'Mask'

def add_fill(tree):
    # def traverse(tree):
    #
    #     if 'layers' in tree.keys():
    #         for layer in tree['layers']:
    #             traverse(layer)
    #
    #         for layer in tree['layers']:
    #
    #             if 'layers' not in layer.keys():
    #                 print(layer['name'])
    #                 style = layer['style']
    #                 gradient = style['borders'][0]['gradient']
    #                 print(gradient)
    #                 fills = style['fills']
    #                 if fills: # 判断列表是否为空
    #                     color = fills[0]['color']
    #                     color['red'] = 0
    #                     color['green'] = 0
    #                     color['blue'] = 0
    #                     if fills['borders']:
    #                         pass
    #                 # gradient = fills['gradient']
    #                 # stops1 = gradient['stops'][0]['color']
    # def traverse(tree, level=0):
    #
    #     if 'layers' in tree.keys():
    #         for child in tree['layers']:
    #             traverse(child, level + 1)
    #     else:
    #         if 'style' not in tree.keys():
    #             print(tree['name'])
    #         else:
    #             tree['style']['fills'].append({"_class": "fill",
    #                                            "isEnabled": True, "fillType": 0,
    #                                            "color": {"_class": "color", "alpha": 1, "blue": np.random.rand(),
    #                                                      "green": np.random.rand(), "red": np.random.rand()},
    #                                            "contextSettings": {"_class": "graphicsContextSettings",
    #                                                                "blendMode": 0, "opacity": 1},
    #                                            "gradient": {"_class": "gradient", "elipseLength": 0,
    #                                                         "from": "{0.5, 0}",
    #                                                         "gradientType": 0,
    #                                                         "to": "{0.5, 1}",
    #                                                         "stops": [{"_class": "gradientStop", "position": 0,
    #                                                                    "color": {"_class": "color", "alpha": 1,
    #                                                                              "blue": 1, "green": 1, "red": 1}},
    #                                                                   {"_class": "gradientStop", "position": 1,
    #                                                                    "color": {"_class": "color", "alpha": 1,
    #                                                                              "blue": 0, "green": 0, "red": 0}}]},
    #                                            "noiseIndex": 0, "noiseIntensity": 0, "patternFillType": 1,
    #                                            "patternTileScale": 1})
    # fill_dict = [{"_class": "fill",
    #               "isEnabled": True,
    #               "fillType": 0,
    #               "color": {
    #                   "_class": "color",
    #                   "alpha": 1,
    #                   "blue": 0.5,
    #                   "green": 0.5,
    #                   "red": 0.5}}]

    def traverse(tree, level=0):
        random.seed(level)
        fill_dict = [{"_class": "fill",
                      "isEnabled": True, "fillType": 0,
                      "color": {"_class": "color", "alpha": 1, "blue": np.random.rand(),
                                "green": np.random.rand(), "red": np.random.rand()}}]
        # 如果为字，进行矩形填充的替换
        if tree['_class'] == 'text':
            print(type(tree))
            print(tree['name'])
            height = tree['frame']['height']
            width = tree['frame']['height']
            x = tree['frame']['x']
            y = tree['frame']['y']
            do_objectID = tree['do_objectID']
            style_objectID = tree['style']['do_objectID']
            rectangle_fill = {
                "_class": "rectangle",
                "do_objectID": do_objectID,
                "booleanOperation": -1,
                "isFixedToViewport": False,
                "isFlippedHorizontal": False,
                "isFlippedVertical": False,
                "isLocked": False,
                "isVisible": True,
                "layerListExpandedType": 0,
                "nameIsFixed": False,
                "resizingConstraint": 63,
                "resizingType": 0,
                "rotation": 0,
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
                    "do_objectID": style_objectID,
                    "endMarkerType": 0,
                    "miterLimit": 0,
                    "startMarkerType": 0,
                    "windingRule": 1,
                    "fills": [
                        {
                            "_class": "fill",
                            "isEnabled": False,
                            "fillType": 0,
                            "color": {
                                "_class": "color",
                                "alpha": 1,
                                "blue": np.random.rand(),
                                "green": np.random.rand(),
                                "red": np.random.rand()
                            }
                        }
                    ]
                },
                "edited": False,
                "isClosed": False,
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
                "hasConvertedToNewRoundCorners": False
            }
            tree = rectangle_fill
            return tree
        if 'layers' in tree.keys():
            for child in tree['layers']:
                traverse(child, level + 1)
            for child in tree['layers']:
                # 判断是否为叶子节点
                if 'layers' not in child.keys():
                    # 对其父节点进行填充
                    tree['style']['fills'] = fill_dict  # 色块填充
                    if is_shape(child):
                        child['style']['fills'] = fill_dict  # 色块填充

    traverse(tree, 0)
    return tree


def cal_white(imageName):
    # 计算背景白色的位置
    image = cv2.imread(imageName)
    print(image)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(image, (5, 5), 0)  # 阈值一定要设为 0 ！高斯模糊
    ret3, th3 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)  # 二值化 0 = black ; 1 = white
    height, width = th3.shape
    print(height, width)
    temp = np.zeros((height, width))
    print(temp.shape)
    sum = 0
    list_x = []
    list_y = []
    for h in range(height):
        for w in range(width):
            if th3[h, w] == 255:
                list_x.append(w)
                list_y.append(h)
    start = 0
    stop = 0
    for i in range(len(list_x)):
        if list_x[i + 1] - list_x[i] < 5:
            stop = stop + i
        else:
            start = i
        print('start:{}stop:{}'.format(start, stop))


if __name__ == '__main__':
    # 加载json文件
    load_path = 'sketch文件/关联图层合并-亲宝贝/pages/DCA074DE-7085-4DC8-B038-E82ED277267A.json'
    tree = json.load(open(load_path, encoding='utf-8'))
    # 返回填充颜色后的json
    new_tree = add_fill(tree)
    with open(load_path, 'w') as f:
        json.dump(new_tree, f)
    # 得到一个sketch文件查看设计稿和zip文件查看json
    convert2sketch('sketch文件/关联图层合并-亲宝贝', 'test.zip', 'baby-test.sketch')
    # cal_white('tmp1.png')
