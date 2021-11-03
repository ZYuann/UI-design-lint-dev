import json

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas


def count_layer(img_box):
    '''
    计算 box 里的图层数，根据颜色值
    但
    :param img_box: 标注框部分的色块图矩阵 numpy array
    :return: layer number
    '''
    # print(np.unique(img_box, axis=0, return_counts=True))
    return np.unique(img_box, axis=0, return_counts=True)


def is_bg_merge(img, bbox_region):
    '''
    1. 判断为背景图合并情况还是其他情况
    :param img: 分割后的色块图 default [750,750]
    :param bbox_region: 输入的一个没有归一化的[w1, w2, h1, h2]
    :return: true or false
    '''
    w1, w2, h1, h2 = bbox_region[0], bbox_region[1], bbox_region[2], bbox_region[3]
    img_box = np.reshape(img[w1:w2, h1:h2], ((w2 - w1) * (h2 - h1), -1))  # 变2维
    values, counts = count_layer(img_box)  # 计算图层数
    if len(counts) < 20:
        print('其他合并情况')
        return False
    else:
        print('背景图合并')
        return True


def get_color_id(img, bbox_region, color_list='color.npy'):
    '''
    根据颜色查找字典，得到颜色 id
    :param img:
    :param bbox_region:
    :param color_list
    :return:
    '''
    w1, w2, h1, h2 = bbox_region[0], bbox_region[1], bbox_region[2], bbox_region[3]
    plt.imshow(img[w1:w2, h1:h2, ::-1])
    plt.show()
    img_box = np.reshape(img[w1:w2, h1:h2], ((w2 - w1) * (h2 - h1), -1))
    color_list = np.load(color_list)
    color_list = color_list.T
    print(color_list.shape)
    img_box = np.unique(img_box, axis=0)  # 去重
    for w in range(img_box.shape[0]):
        for index, color in enumerate(color_list):
            if sum(abs(img_box[w, :] - color)) < 6:
                print('img_box[w, :]', img_box[w, :])
                print('index', index)
                break


def de_normalize(bbox, width, height):
    '''
    取消归一化
    :param bbox: 归一化的 bbox
    :return: [x_l,x_r,y_l,y_r] 左上角 右下角
    '''
    x_center, y_center, w, h = bbox[1] * width, bbox[2] * height, bbox[3] * width, bbox[4] * height
    bbox_region = (int(x_center - w / 2), int(x_center + w / 2), int(y_center - h / 2), int(y_center + h / 2))
    bbox_region = np.array(bbox_region)
    bbox_region[bbox_region < 0] = 0  # 处理边界情况

    return bbox_region


def get_layer_in_bbox(flatten_json, bbox_region):
    '''
    得到标注框内的图层name
    :param flatten_json: 打平后的设计稿，带绝对位置
    :param bbox_region: 标注框空间范围 (未归一化)
    :return: 图层name
    '''
    name_list = []
    x1, x2, y1, y2 = bbox_region[0], bbox_region[1], bbox_region[2], bbox_region[3]
    tree = json.load(open(flatten_json, encoding='utf-8'))

    def traverse(node: dict):

        if 'merge' in node['name']:
            height = node['frame']['height']
            width = node['frame']['width']
            x = node['frame']['x']
            y = node['frame']['y']
            name = node['name']
            print('\nname:{}-height:{} width:{} x:{} y:{}'.format(node['name'], height, width, x, y))
            if (x1 < x < x2) and (y1 < y < y2):
                name_list.append(name)
        if 'layers' in node.keys():
            for i in range(len(node['layers'])):
                child = node['layers'][i]
                node['layers'][i] = traverse(child)

        return node

    traverse(tree)
    print('name:', name_list)
    return name_list

def get_layer_id(img_path, label_path):
    '''
    读取 box 色块图，得到图层颜色 id
    读取 label.txt
    :param img_path:
    :param label_path:
    :return:
    '''
    img = cv2.imread(img_path)  # h,w,c[BGR]
    # img = cv2.dilate(img, kernel=np.ones((5, 5), 'uint8')) 处理颜色问题
    # plt.imshow(img[:, :, ::-1])
    # plt.show()
    img = np.transpose(img, (1, 0, 2))  # w,h,c[BGR]
    w, h, _ = img.shape
    bbox_list = pandas.read_csv(label_path, sep=' ', encoding='utf-8', header=None)
    bbox_list.drop_duplicates(inplace=True)  # 去除重复行
    bbox_list = bbox_list.values
    de_box = de_normalize(bbox_list[2], w, h)
    print('de_box', de_box)
    # 不是背景图的情况
    if not is_bg_merge(img, de_box):
        get_layer_in_bbox()

        # get_color_id(img, de_box)


if __name__ == '__main__':
    img_path = './images/baby0.png'
    label_path = './labels/baby0.txt'
    get_layer_id(img_path, label_path)
