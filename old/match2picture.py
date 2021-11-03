import cv2
import time
from scipy import stats
import matplotlib.pyplot as plt

image1 = cv2.imread('./ICON/signal.png')
image2 = cv2.imread('./ICON/signal-2.png')

plt.figure()
plt.imshow(image1)
# plt.savefig('image1.png', dpi = 300)

plt.figure()
plt.imshow(image2)
# plt.savefig('image2.png', dpi = 300)
#  计算特征点提取&生成描述时间
start = time.time()
sift = cv2.xfeatures2d.SIFT_create()
#  使用SIFT查找关键点key points和描述符descriptors
kp1, des1 = sift.detectAndCompute(image1, None)
kp2, des2 = sift.detectAndCompute(image2, None)
end = time.time()
print("特征点提取&生成描述运行时间:%.2f秒" % (end - start))

kp_image1 = cv2.drawKeypoints(image1, kp1, None)
kp_image2 = cv2.drawKeypoints(image2, kp2, None)

print("关键点数目:", len(kp1))

for i in range(len(kp1)):
    print("关键点", i)
    print("关键点坐标:", kp1[i].pt)
    print("邻域直径:", kp1[i].size)
    print("方向:", kp1[i].angle)
    # print("所在的图像金字塔的组:", kp1[i].octave)
    print("================")

for i in range(len(kp2)):
    print("关键点", i)
    print("关键点坐标:", kp2[i].pt)
    print("邻域直径:", kp2[i].size)
    print("方向:", kp2[i].angle)
    # print("所在的图像金字塔的组:", kp1[i].octave)
    print("================")
#  查看描述
print("描述的shape:", des1.shape)
for i in range(len(kp1)):
    print("描述", i)
    print(des1[i])
