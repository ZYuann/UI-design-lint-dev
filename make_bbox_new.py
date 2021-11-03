# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import Callable, List

import numpy as np
from traverse_utils import DrawAndLabelHandler, DrawAndLabelHandlerOption, CreateBaseTraverseHandlerOption, PreProcess

if __name__ == "__main__":
    color_list: List[List[int]] = list(np.load("/Users/zhangyuan/Documents/设计稿/python/UI-design-lint-dev/color.npy"))
    folder_name = '/Users/zhangyuan/Documents/设计稿/ske1'
    file_filter: Callable[[str], bool] = lambda x: x.endswith('.sketch')
    sketch_lst = [os.path.join(folder_name, f) for f in os.listdir(folder_name) if
                  os.path.isfile(os.path.join(folder_name, f)) and file_filter(f)]
    preProcess = PreProcess(sketch_lst, CreateBaseTraverseHandlerOption(DrawAndLabelHandler, {
        "options": DrawAndLabelHandlerOption(color_list, '.cache', 'images', 'labels')
    }))
    preProcess.process()
    # format_yolo2coco(img_folder_path='images', label_folder_path='labels', out_file='train.json',
    #                  sub_images=('filled.png', 'default.png'))
