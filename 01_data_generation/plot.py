import os
import matplotlib.pyplot as plt

filename = 'result.txt'
sample_path = 'D:/Dataset/xfemV1-1/'
#sample_path = 'C:/Users/Administrator/Desktop/lstm_data/coordinate_cut/'
sample_list = os.listdir(sample_path)
for sample in sample_list:
    path = sample_path + sample
    abs_path = os.path.join(path, filename)
    f = open(abs_path, "r")
    #f = open(path, "r")
    x = []
    y = []
    for j in f.readlines()[2:]:
        x.append(float(j.split()[1]))
        y.append(float(j.split()[2]))
        if float(j.split()[2]) > 11:
            print(sample)
    plt.plot(x, y)


plt.ylim((4, 14))
plt.ylabel('y coordinate [mm]', fontdict={'family' : 'Times New Roman', 'size'   : 16})
plt.xlabel('x coordinate [mm]', fontdict={'family' : 'Times New Roman', 'size'   : 16})
plt.yticks(fontproperties = 'Times New Roman', size = 14)
plt.xticks(fontproperties = 'Times New Roman', size = 14)
plt.show()


