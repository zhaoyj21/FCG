# encoding:utf-8
import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

directory = r"D:\Dataset\cut_picture1"
binary_directory = r'D:\Dataset\binary_picture1'
#directory = r"C:/Users/Administrator/Desktop/pictest.png"
#binary_directory = r'C:/Users/Administrator/Desktop/pictest2.png'
os.chdir(directory)
files = os.listdir('.')
m = 0
while m < len(files):
    # 读取原始图像
    img_BGR = cv2.imread(files[m])
    # 灰度化处理
    img_BGR = img_BGR[492:1292,103:780]
    #img_BGR = img_BGR[:, :]
    img_GRAY = cv2.cvtColor(img_BGR, cv2.COLOR_BGR2GRAY)
    # 二值化处理，返回th-阈值，和图像img_BINARY
    th, img_BINARY = cv2.threshold(img_GRAY,100,255,cv2.THRESH_BINARY)
    # cv2.imshow("img_BINARY", img_BINARY)
    # #等待显示
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    exportname = os.path.join(binary_directory, files[m])
    cv2.imwrite(exportname,img_BINARY)
    #cv2.imwrite(exportname,img_GRAY)
    m+=1
