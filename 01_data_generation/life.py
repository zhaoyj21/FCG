import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt
import math
from scipy.interpolate import interpolate
import os

directory = r"D:/Dataset/coordinate"
cut_directory = "D:/Dataset/life/"
sample_list = os.listdir(directory)
os.chdir(directory)
for sample in sample_list:
    # read data from a file
    x = []
    y = []
    z = []
    filename = sample
    f = open(filename, encoding='utf-8')
    lines = f.readlines()[2:]
    for line in lines:
        s = line.strip().split('\t')
        x.append(float(s[1]))
        y.append(float(s[2]))
        z.append(math.sqrt(float(s[3]) ** 2 + float(s[4]) ** 2))

    f.close()

    x = np.array(x)
    y = np.array(y)
    z = np.array(z)

    # fit the path and obtain the crack tip coordinate
    fit_xy = interpolate.interp1d(x, y, kind='linear')
    x_tip = np.linspace(1.0, 8.6, 41)
    y_tip = fit_xy(x_tip)

    # plt.plot(x,y,"k")
    # plt.plot(x_tip,y_tip,"r*")
    # plt.show()

    #### ================================= crack length and crack tip ====================================
    # calculate the crack extension
    crack_inc = []  # crack increment in each picture
    crack_length = []  # crack length in each picture (last point)
    a_sum = 0
    for j in range(len(x_tip) - 1):
        crack_inc.append(math.sqrt((x_tip[j + 1] - x_tip[j]) ** 2 + (y_tip[j + 1] - y_tip[j]) ** 2))
        a_sum = a_sum + math.sqrt((x_tip[j + 1] - x_tip[j]) ** 2 + (y_tip[j + 1] - y_tip[j]) ** 2)
        crack_length.append(a_sum)

    crack_length_median = []  # crack length in each picture (median point in crack increment)
    for j in range(len(crack_inc)):
        crack_length_median.append(crack_length[j] - crack_inc[j] / 2.0)

    # print(crack_inc)
    # print(crack_length_median)
    # print(crack_length)

    #### ================================= stress intensity factor ====================================
    a_sum = 0
    new_x = [0, ]  # 裂纹长度
    new_y = [z[0], ]  # 有效应力强度因子
    for j in range(len(x) - 1):
        a_sum = a_sum + math.sqrt((x[j + 1] - x[j]) ** 2 + (y[j + 1] - y[j]) ** 2)
        new_x.append(a_sum)
        new_y.append(z[j + 1])

    f = interpolate.interp1d(new_x, new_y, kind='linear')
    Keff = f(crack_length_median)

    #### ================================= life ====================================
    C = 9.7 * 10 ** (-12)
    m = 3.0
    N = []
    for j in range(len(crack_length_median)):
        N.append(int(crack_inc[j] / C / (Keff[j]) ** m))

    fout = open(cut_directory+filename,"w")
    for j in range(len(crack_length_median)):
        fout.write(str(j+1)+"\t"+str(N[j])+"\n")
    fout.close()
