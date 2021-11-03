import json


class node:
    def __init__(self, x, y, width, height, Type, name):
        self.x = x
        self.y = y
        self.w = width
        self.h = height
        self.type = Type
        self.n = name


def readsketch(f):
    with open(f, 'r', encoding='UTF-8') as load_f:
        data = json.load(load_f)
    icons = []

    def traverse(tree):
        # print('\ntree', tree)
        frame = tree["frame"]
        # print('frame', frame)
        h = frame["height"]
        w = frame["width"]
        x = frame["x"]
        y = frame["y"]
        if "layers" in tree.keys():
            # print(tree['name'])
            # if "merge" in tree['name']:
            for layer in tree['layers']:
                traverse(layer)
            for layer in tree['layers']:
                if ('layers' not in layer.keys()):
                    icons.append({'name': tree['name'], 'bbox': [x, y, h, w]})

    traverse(data)
    for icon in icons:
        print('\n', icon)
    return icons


def test_traverse(file_name):
    with open(file_name, 'r', encoding='UTF-8') as load_f:
        data = json.load(load_f)
    icons = []

    def traverse(tree, nodes, if_append=False):
        if 'layers' in tree.keys():
            layers = []
            for child in tree['layers']:
                print('\nchild', child)
                traverse(child, layers, if_append=True)
            icons.append({'name': tree['name']})

    traverse(data, [])
    print(icons)


# test_traverse('4CC6454F-D5F0-4AC4-858D-D1EE15A63E6E.json')
# exit(0)

def visJson(file_name):
    with open(file_name, 'r', encoding='UTF-8') as load_f:
        data = json.load(load_f)
    icons = []

    def traverse(tree, level=0):
        print("---" * level + tree['name'])
        if 'layers' in tree.keys():
            for child in tree['layers']:
                traverse(child, level + 1)

    traverse(data, 0)
    return icons


icons = visJson('sketch文件/划算排行/pages/4CC6454F-D5F0-4AC4-858D-D1EE15A63E6E.json')
print(icons)
exit(0)
# load json
# with open("EF39CF0E-F3F9-468B-BF2F-C51E794011CF.json",'r',encoding='UTF-8') as load_f:
#     load_dict = json.load(load_f)
with open("sketch文件/划算排行/pages/demo.json", 'r', encoding='UTF-8') as load_f:
    load_dict = json.load(load_f)
# ******************如何读取所有图层信息*************************
# 因字典的value为列表，故需要再次转换
if isinstance(load_dict['layers'], list):
    for i in range(len(load_dict['layers'])):
        for key, value in load_dict['layers'][i].items():
            if key == 'name' or key == 'frame':
                print(key, value)
# print(load_dict['layers'])
