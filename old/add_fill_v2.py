import json
import os
import random
import shutil
import uuid
import zipfile
import cv2
import numpy as np


def unzip_file(file_name, zip_name):
    try:
        zip_file = zipfile.ZipFile(zip_name)
        zip_list = zip_file.namelist()  # 得到压缩包里所有文件
        for f in zip_list:
            zip_file.extract(f, file_name)  # 循环解压文件到指定目录
    except:
        zip_file.close()  # 关闭文件，必须有，释放内存


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
    shutil.copy(zip_name, 'temp.zip')
    if os.path.exists(sketch_name):
        os.remove(sketch_name)
    os.rename(zip_name, sketch_name)
    print('saved in {}'.format(sketch_name))


def is_shape(node):
    # 需要对子节点填充的shape
    t = node['_class']
    return t == 'rectangle' or t == 'Mask'


def add_fill(tree):

    def traverse(tree, level=0):
        random.seed(level)
        fill_dict = [{"_class": "fill",
                      "isEnabled": True, "fillType": 0,
                      "color": {"_class": "color", "alpha": 1, "blue": np.random.rand(),
                                "green": np.random.rand(), "red": np.random.rand()}}]


        if 'layers' in tree.keys():
            for i in range(len(tree['layers'])):
                child = tree['layers'][i]
                tree['layers'][i] = traverse(child, level + 1)
                # 如果为字，进行矩形填充的替换
                if child['_class'] == 'text':
                    height = child['frame']['height']
                    width = child['frame']['width']
                    x = child['frame']['x']
                    y = child['frame']['y']
                    rectangle_fill = {
                        "_class": "rectangle",
                        "do_objectID": str(uuid.uuid1()),
                        "booleanOperation": -1,
                        "isFixedToViewport": False,
                        "isFlippedHorizontal": False,
                        "isFlippedVertical": False,
                        "isLocked": False,
                        "isVisible": True,
                        "layerListExpandedType": 0,
                        "name": '矩形填充颜色位置',
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
                                        "alpha": 1,
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
                    # rectangle_fill = {
                    #     "_class": "rectangle",
                    #     "do_objectID": do_objectID,
                    #     "booleanOperation": -1,
                    #     "isFixedToViewport": False,
                    #     "isFlippedHorizontal": False,
                    #     "isFlippedVertical": False,
                    #     "isLocked": False,
                    #     "isVisible": True,
                    #     "layerListExpandedType": 0,
                    #     "name": "矩形",
                    #     "nameIsFixed": False,
                    #     "resizingConstraint": 63,
                    #     "resizingType": 0,
                    #     "rotation": 0,
                    #     "shouldBreakMaskChain": False,
                    #     "exportOptions": {
                    #         "_class": "exportOptions",
                    #         "includedLayerIds": [],
                    #         "layerOptions": 0,
                    #         "shouldTrim": False,
                    #         "exportFormats": []
                    #     },
                    #     "frame": {
                    #         "_class": "rect",
                    #         "constrainProportions": False,
                    #         "height": height,
                    #         "width": width,
                    #         "x": x,
                    #         "y": y
                    #     },
                    #     "clippingMaskMode": 0,
                    #     "hasClippingMask": False,
                    #     "style": {
                    #         "_class": "style",
                    #         "do_objectID": style_objectID,
                    #         "endMarkerType": 0,
                    #         "miterLimit": 0,
                    #         "startMarkerType": 0,
                    #         "windingRule": 1,
                    #         "blur": {
                    #             "_class": "blur",
                    #             "isEnabled": False,
                    #             "center": "{0.5, 0.5}",
                    #             "motionAngle": 0,
                    #             "radius": 10,
                    #             "saturation": 1,
                    #             "type": 0
                    #         },
                    #         "borderOptions": {
                    #             "_class": "borderOptions",
                    #             "isEnabled": True,
                    #             "dashPattern": [],
                    #             "lineCapStyle": 0,
                    #             "lineJoinStyle": 0
                    #         },
                    #         "borders": [],
                    #         "colorControls": {
                    #             "_class": "colorControls",
                    #             "isEnabled": True,
                    #             "brightness": 0,
                    #             "contrast": 1,
                    #             "hue": 0,
                    #             "saturation": 1
                    #         },
                    #         "contextSettings": {
                    #             "_class": "graphicsContextSettings",
                    #             "blendMode": 0,
                    #             "opacity": 1
                    #         },
                    #         "fills": [
                    #             {
                    #                 "_class": "fill",
                    #                 "isEnabled": False,
                    #                 "fillType": 0,
                    #                 "color": {
                    #                     "_class": "color",
                    #                     "alpha": 1,
                    #                     "blue": np.random.rand(),
                    #                     "green": np.random.rand(),
                    #                     "red": np.random.rand()
                    #                 }
                    #             }
                    #         ],
                    #         "innerShadows": [],
                    #         "shadows": []
                    #     },
                    #     "fixedRadius": 0,
                    #     "needsConvertionToNewRoundCorners": False,
                    #     "hasConvertedToNewRoundCorners": True
                    #
                    # }

                    tree['layers'].append(rectangle_fill)
                if 'layers' not in child.keys():
                    # 对其父节点进行填充
                    tree['style']['fills'] = fill_dict  # 色块填充
                    if is_shape(child):
                        child['style']['fills'] = fill_dict  # 色块填充
        return tree

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
    # json_path = 'D:/STUDY/UI_design_issues/问题/sketchfiles/关联图层合并-亲宝贝/pages/DCA074DE-7085-4DC8-B038-E82ED277267A.json'
    load_path = 'sketch文件/关联图层合并-亲宝贝/pages/DCA074DE-7085-4DC8-B038-E82ED277267A.json'
    unzip_file(file_name='sketch文件/关联图层合并-亲宝贝', zip_name='sketch文件/关联图层合并-亲宝贝.zip')
    tree = json.load(open(load_path, encoding='utf-8'))
    # 返回填充颜色后的json
    new_tree = add_fill(tree)
    with open(load_path, 'w') as f:
        json.dump(new_tree, f)
    # 得到一个sketch文件查看设计稿和zip文件查看json
    convert2sketch('sketch文件/关联图层合并-亲宝贝', 'test.zip', 'baby-test.sketch')

    # cal_white('tmp1.png')
