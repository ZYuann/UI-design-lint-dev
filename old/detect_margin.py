import cv2
import numpy as np
from PIL import Image
from matplotlib import pyplot as plt


def get_margin(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 将图像转化为灰度图像
    # 拉普拉斯边缘检测
    canny = cv2.Canny(img, 50, 150)
    return canny
    # plt.imshow(lap)
    # plt.show()


def fill_color_diffuse_water_from_img(task_out_dir, image, x, y, thres_up=(10, 10, 10), thres_down=(10, 10, 10),
                                      fill_color=(255, 255, 255)):
    """
    漫水填充：会改变图像
    """
    # 获取图片的高和宽
    h, w = image.shape[:2]

    # 创建一个h+2,w+2的遮罩层，
    # 这里需要注意，OpenCV的默认规定，
    # 遮罩层的shape必须是h+2，w+2并且必须是单通道8位，具体原因我也不是很清楚。
    mask = np.zeros([h + 2, w + 2], np.uint8)

    # 这里执行漫水填充，参数代表：
    # copyImg：要填充的图片
    # mask：遮罩层
    # (x, y)：开始填充的位置（开始的种子点）
    # (255, 255, 255)：填充的值，这里填充成白色
    # (100,100,100)：开始的种子点与整个图像的像素值的最大的负差值
    # (50,50,50)：开始的种子点与整个图像的像素值的最大的正差值
    # cv.FLOODFILL_FIXED_RANGE：处理图像的方法，一般处理彩色图象用这个方法
    cv2.floodFill(image, mask, (x, y), fill_color, thres_down, thres_up, cv2.FLOODFILL_FIXED_RANGE)
    cv2.imwrite(task_out_dir, image)
    # mask是非常重要的一个区域，这块区域内会显示哪些区域被填充了颜色
    # 对于UI自动化，mask可以设置成shape，大小以1最大的宽和高为准
    return image, mask


img = cv2.imread('baby.png')
img = get_margin(img)
fill_color_diffuse_water_from_img('./temp3.png', img, 100, 200)
