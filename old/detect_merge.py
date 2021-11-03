import json
import numpy as np
import os


class node:
    def __init__(self, x, y, width, height, Type, name):
        self.x = x
        self.y = y
        self.w = width
        self.h = height
        self.type = Type
        self.n = name


def readsketch(f):
    data = json.load(f)
    icons = []

    def traverse(tree, nodes, ifappend=False):
        frame = tree["frame"]
        t = tree["_class"]
        h = frame["height"]
        w = frame["width"]
        x = frame["x"]
        y = frame["y"]
        if "layers" in tree.keys():
            if "merge" in tree['name']:
                layers = []
                for child in tree['layers']:
                    traverse(child, layers, ifappend=True)
                icons.append({'name': tree['name'], 'layers': layers, 'bbox': [x, y, h, w]})
            else:
                for child in tree['layers']:
                    traverse(child, nodes, ifappend=ifappend)
        else:
            if ifappend:
                nodes.append(node(x, y, w, h, t, tree['name']))

    traverse(data, [])
    return icons


def visjson(tree):
    def traverse(tree, level=0):
        print("--|" * level + tree['name'])
        if 'layers' in tree.keys():
            for child in tree['layers']:
                traverse(tree=child, level=level + 1)

    traverse(tree, 0)


def check_if_merge(bboxes):
    bboxes = np.array(bboxes)
    n = bboxes.shape[0]
    ifmerge = True
    for i in range(n):
        dist = bboxes[i:i + 1, :2] + bboxes[i:i + 1, 2:4] / 2 - bboxes[:, :2] - bboxes[:, 2:4] / 2
        dist = np.sum(np.sqrt(dist * dist), axis=1)
        ifmerge = (ifmerge and (dist < 70).all())
    return ifmerge


def isshape(node):
    t = node['_class']
    return True  # 暂时不进行类型检查
    # return t == 'oval' or t == 'shapePath' or t == 'rectangle' or t == 'shapeGroup' or t == 'slice'


def merge_detection(tree):
    def traverse(tree):
        correctness = 0
        totalmerge = 0
        # print(tree['name'])

        if 'layers' in tree.keys():
            for layer in tree['layers']:
                a, b = traverse(layer)
                correctness += a
                totalmerge += b
            bboxes = []
            ifmerge = True

            for layer in tree['layers']:

                if ('layers' not in layer.keys() and isshape(layer)) or ("isleaf" in layer.keys()):
                    frame = layer['frame']
                    h = frame["height"]
                    w = frame["width"]
                    x = frame["x"]
                    y = frame["y"]
                    bboxes.append([x, y, w, h])
                else:
                    ifmerge = False

            ifmerge = ifmerge and check_if_merge(bboxes)
            if "merge" in tree['name']:
                totalmerge += 1

            if ifmerge:
                Str = ""
                for layer in tree['layers']:
                    Str = Str + layer['name'] + " "
                print(Str + " is merged into " + tree['name'])

                if "merge" in tree['name']:
                    correctness += 1
                tree['isleaf'] = True
                # tree['name'] = '#merge#' + tree['name']
        return correctness, totalmerge

    correctness, totalmerge = traverse(tree)
    return correctness, totalmerge


if __name__ == '__main__':
    tree = json.load(open('sketch文件/关联图层合并-亲宝贝/pages/DCA074DE-7085-4DC8-B038-E82ED277267A.json', encoding='utf-8'))
    # tree = json.load(open('sketch文件/洋淘大赏2/pages/ACD24EC7-29B4-4469-834E-04A0331CFDEA.json', encoding='utf-8'))
    # visjson(tree)
    correctness, totalmerge = merge_detection(tree)
    print(correctness, ' ', totalmerge)
    # visjson(tree)
