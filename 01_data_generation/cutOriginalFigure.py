import numpy as np
import cv2
import json
from matplotlib import pyplot as plt
import os

directory = r"D:\Dataset\picture1"
cut_directory = r"D:\Dataset\cut_picture1"

os.chdir(directory)
files = os.listdir('.')
m = 0
while m < len(files):
    image_src = cv2.imread(files[m])
    break_flag = False
    start_row = 0
    for i in image_src:
        start_col = 0
        for j in i:
            if list(j).count(254) != 3:
                break_flag = True
                break
            start_col += 1
        if break_flag:
            break
        start_row += 1
    print(start_row, start_col)

    break_flag = False
    end_row = image_src.shape[0]
    for i in reversed(image_src):
        end_col = image_src.shape[1]
        for j in reversed(i):
            if list(j).count(254) != 3:
                break_flag = True
                break
            end_col -= 1
        if break_flag:
            break
        end_row -= 1
    print(end_row, end_col)

    cropped = image_src[start_row:end_row, start_col:end_col]
    # print(cropped.shape)
    exportname = os.path.join(cut_directory, files[m])
    cv2.imwrite(exportname, cropped)
    m += 1
