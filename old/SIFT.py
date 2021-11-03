import cv2
from scipy import stats
from matplotlib import pyplot as plt
from PIL import Image
from numpy import average, dot, linalg


# 对图片进行统一化处理
def get_thum(image, size=(64, 64), greyscale=False):
    # 利用image对图像大小重新设置, Image.ANTIALIAS为高质量的
    image = image.resize(size, Image.ANTIALIAS)
    if greyscale:
        # 将图片转换为L模式，其为灰度图，其每个像素用8个bit表示
        image = image.convert('L')
    return image


# 计算图片的余弦距离
def image_similarity_vectors_via_numpy(image1, image2):
    image1 = get_thum(image1)
    image2 = get_thum(image2)
    images = [image1, image2]
    vectors = []
    norms = []
    for image in images:
        vector = []
        for pixel_tuple in image.getdata():
            vector.append(average(pixel_tuple))
        vectors.append(vector)
        # linalg=linear（线性）+algebra（代数），norm则表示范数
        # 求图片的范数？？
        norms.append(linalg.norm(vector, 2))
    a, b = vectors
    a_norm, b_norm = norms
    # dot返回的是点积，对二维数组（矩阵）进行计算
    res = dot(a / a_norm, b / b_norm)
    return res


def compare_img_hist(img1, img2):
    '''
    直方图比较法
    :param img1: 图片1
    :param img2: 图片2
    :return:
    '''
    img1_hist = cv2.calcHist([img1], [1], None, [256], [0, 256])
    img1_hist = cv2.normalize(img1_hist, img1_hist, 0, 1, cv2.NORM_MINMAX, -1)
    img2_hist = cv2.calcHist([img2], [1], None, [256], [0, 256])
    img2_hist = cv2.normalize(img2_hist, img2_hist, 0, 1, cv2.NORM_MINMAX, -1)
    similarity = cv2.compareHist(img1_hist, img2_hist, 0)
    print('similarity:', similarity)
    return similarity


def sift_kp(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sift = cv2.xfeatures2d.SIFT_create(nfeatures=10)
    kp, des = sift.detectAndCompute(image, None)  # 特征值，特征点
    kp_image = cv2.drawKeypoints(gray_image, kp, image, flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)  # 画特征点
    for i in range(len(kp)):
        print("关键点", i)
        print("关键点坐标:", kp[i].pt)
        print("邻域直径:", kp[i].size)
        print("方向:", kp[i].angle)
        # print("response:", kp[i].response)

        # print("所在的图像金字塔的组:", kp1[i].octave)
        print("================")
    return kp_image, kp, des


list1 = ['Capacity', 'Border']
for i in range(2):
    image1 = Image.open('./ICON/Cap.png')
    image2 = Image.open('./ICON/{}.png'.format(list1[i]))
    similarity = image_similarity_vectors_via_numpy(image1, image2)
    print('Cap与的{}相似度:{}'.format(list1[i], similarity))

plt.subplot(121), plt.imshow(image1), plt.axis('off')
plt.title('similarity:{}'.format(similarity))
plt.subplot(122), plt.imshow(image2), plt.axis('off')
# plt.title('Destination'), plt.axis('off')
plt.show()
exit(0)

kp_image1, kp1, des1 = sift_kp(image1)
kp_image2, kp2, des2 = sift_kp(image2)
print(des1.shape, des2.shape)
print(des1, des2)
similarity = stats.pearsonr(des1[0, :], des2[0, :])
similarity = [round(i, 3) for i in similarity]
print(similarity)

plt.subplot(121), plt.imshow(kp_image1), plt.axis('off')
plt.title('similarity:{}'.format(similarity))
plt.subplot(122), plt.imshow(kp_image2), plt.axis('off')
# plt.title('Destination'), plt.axis('off')
plt.show()
