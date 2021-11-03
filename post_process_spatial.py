import json

import cv2
import numpy as np
import pandas


def is_bg_merge(img, bbox_region, threshold_w=700):
    '''
    1. 判断为背景图合并情况还是其他情况
    :param img: 分割后的色块图 default [750,750]
    :param bbox_region: 输入的一个没有归一化的[w1, w2, h1, h2]
    :param threshold_w: 宽度阈值
    :return: true or false
    '''
    x1, x2, y1, y2 = bbox_region[0], bbox_region[1], bbox_region[2], bbox_region[3]
    img_box = img[x1:x2, y1:y2].shape  # [x, y, channel]
    w, h, _ = img_box
    print('w:{}, h:{}'.format(w, h))
    if w <= threshold_w:
        print('其他合并情况')
        return False
    else:
        print('背景图合并')
        return True


def de_normalize(bbox, width, height):
    '''
    取消归一化, 计算图层中心点
    :param bbox: 归一化的 bbox
    :return: [x_l,x_r,y_l,y_r] 左上角 右下角
    '''
    x_center, y_center, w, h = bbox[1] * width, bbox[2] * height, bbox[3] * width, bbox[4] * height
    bbox_region = (int(x_center - w / 2), int(x_center + w / 2), int(y_center - h / 2), int(y_center + h / 2))
    bbox_region = np.array(bbox_region)
    # bbox_region[bbox_region < 0] = 0  # 处理边界情况
    print('box_region', bbox_region)
    return bbox_region


def get_layer_in_bbox(flatten_json, bbox_region, index, is_bg_layer: bool):
    '''
    得到标注框内的图层name
    :param flatten_json: 打平后的设计稿，带绝对位置
    :param bbox_region: 标注框空间范围 (未归一化)
    :param is_bg_layer: 是否为背景图
    :return: 图层name
    '''
    name_list = []
    spatial_list = []
    x1, x2, y1, y2 = bbox_region[0], bbox_region[1], bbox_region[2], bbox_region[3]
    tree = flatten_json
    threshold = 5
    def traverse(node: dict):

        # if 'merge' in node['name']:
        height = node['frame']['height']
        width = node['frame']['width']
        x = node['frame']['x']  # 图层左上角的坐标 绝对坐标
        y = node['frame']['y']
        name = node['name']
        layer_class = node['_class']
        # print('\nname:{}-height:{} width:{} x:{} y:{}'.format(node['name'], height, width, x, y))
        if not is_bg_layer:
            if (x1 - threshold <= abs(x + width / 2) <= x2 + threshold) \
                    and (y1 - threshold + 750 * index <= abs(y + height / 2) <= y2 + threshold + 750 * index):
                name_list.append(name)
        else:
            # 左上角
            if (x1 - threshold <= abs(x) <= x2 + threshold) and (y1 - threshold <= abs(y) <= y2 + threshold):
                spatial_list.append((width, height, name, layer_class))
            # 右上角
            elif (x1 - threshold <= abs(x + width) <= x2 + threshold) and (y1 - threshold <= abs(y) <= y2 + threshold):
                spatial_list.append((width, height, name, layer_class))
            # 左下角
            elif (x1 - threshold <= abs(x) <= x2 + threshold) and (y1 - threshold <= abs(y + height) <= y2 + threshold):
                spatial_list.append((width, height, name, layer_class))
            # 右下角
            elif (x1 - threshold <= abs(x + width) <= x2 + threshold) and (
                    y1 - threshold <= abs(y + height) <= y2 + threshold):
                spatial_list.append((width, height, name, layer_class))

        if 'layers' in node.keys():
            for i in range(len(node['layers'])):
                child = node['layers'][i]
                node['layers'][i] = traverse(child)

        return node

    def handle_bg_layer(spatial_lists):
        '''
        找出背景图中的Mask，然后输出其一个编组的所有图层
        :param spatial_lists: [width, height, name, layer_class]
        :return:
        '''
        mask = 0
        bg_layer = []
        append_flag = 0
        # 找到背景图的mask 或 最底图层
        for list in spatial_lists:
            w, h, name, layer_class = list
            if (x2 - x1) == w and (y2 - y1) == h and layer_class != 'group':
                # if w * h > v and 'rectangle' in layer_class:
                mask = list
        print('mask', mask)
        # 处于同编组的图层进行合并
        for list in spatial_lists:
            w, h, name, layer_class = list
            if mask == list:
                append_flag = 1
            if layer_class == 'group':
                append_flag = 0
            if append_flag == 1:
                bg_layer.append(list)

        print('bg_layer', bg_layer)
        return bg_layer

    traverse(tree)
    print('name:', name_list)
    print('spatial:', spatial_list)
    if is_bg_layer:
        handle_bg_layer(spatial_list)
    return name_list


def get_layer_id(img_path, label_path, json_file, index=0):
    '''
    读取 box 色块图，得到图层 spatial info
    读取 label.txt
    :param json_file: 打平的设计稿
    :return:
    '''
    img = cv2.imread(img_path)  # h,w,c[BGR]
    h, w, _ = img.shape
    bbox_list = pandas.read_csv(label_path, sep=' ', encoding='utf-8', header=None)
    bbox_list.drop_duplicates(inplace=True)  # 去除重复行
    bbox_list = bbox_list.values
    for bbox in bbox_list:
        print('bbox', bbox)
        de_box = de_normalize(bbox, w, h)
        # 不是背景图的情况
        if not is_bg_merge(img, de_box):
            get_layer_in_bbox(json_file, de_box, index, is_bg_layer=False)
            print('\n')
        # 是背景图的情况
        else:
            get_layer_in_bbox(json_file, de_box, index, is_bg_layer=True)
            print('\n')


if __name__ == '__main__':
    index = 2  # 分割图片的序号
    img_path = './images/baby{}.png'.format(index)
    label_path = './labels/baby{}.txt'.format(index)
    json_list = [
        # 'sketch文件/关联图层合并-天猫特选/pages/4B0C7F70-87CF-4F89-B3C2-89537D5B4C7E.json',
        # 'sketch文件/关联图层合并-划算排行/pages/5B48DB31-FEC1-4228-8407-2685D926EF14.json',
        'sketch文件/关联图层合并-亲宝贝/pages/DCA074DE-7085-4DC8-B038-E82ED277267A.json',
        # 'sketch文件/洋淘大赏2/pages/ACD24EC7-29B4-4469-834E-04A0331CFDEA.json',
        # 'sketch文件/关联图层合并-聚划算/pages/B9AE0C64-2E86-457C-AFBB-FEA85DDEEB94.json',
        # 'sketch文件/天猫U先中间页二期优化视觉终稿_20201218/pages/43DDA08B-1869-4321-964B-E182C34D8837.json',
    ]
    flatten_tree = json.load(open(json_list[0], encoding='utf-8'))

    get_layer_id(img_path, label_path, flatten_tree, index)
