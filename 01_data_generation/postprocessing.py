#!/usr/bin/python
# -*- coding: utf-8 -*-
# python version: 3.9

from abaqus import *
from abaqusConstants import *
from caeModules import *
import os

base_directory = r"D:\Dataset\xfemV1-1"
output_directory = r"D:\Dataset\picture"
# problem = [552,578,772,794,819,863,888,892,903,927]
# for i in problem:
for i in range(261, 262):
    sample_name = "sample" + str(i)
    sample_path = os.path.join(base_directory, sample_name)
    os.chdir(sample_path)
    files = os.listdir(sample_path)
    # # 寻找最后一个分析结果
    num_list = []
    for file in files:
        if os.path.splitext(file)[1] == '.odb':
            num = int(file.split('Incre')[1].split('.')[0])
            num_list.append(num)
    max_num = max(num_list)
    odb_name = "Sample" + str(i) + "Incre" + str(max_num) + ".odb"
    abs_path = os.path.join(sample_path, odb_name)
    # # 导出最后一个结果的图片
    o1 = session.openOdb(abs_path)
    myViewports = session.viewports['Viewport: 1']
    myViewports.setValues(displayedObject=o1)
    myViewports.viewportAnnotationOptions.setValues(triad=OFF, legend=OFF, title=OFF, state=OFF, annotations=OFF,
                                                    compass=OFF)
    myViewports.view.setValues(session.views['Front'])
    # cmap = myViewports.colorMappings['Material']
    # myViewports.setColor(colorMapping=cmap)
    # myViewports.disableMultipleColors()
    session.graphicsOptions.setValues(backgroundStyle=SOLID, backgroundColor='#FFFFFF')
    myViewports.odbDisplay.commonOptions.setValues(visibleEdges=FREE)
    myViewports.view.fitView()
    session.pngOptions.setValues(imageSize=(4096, 1870))
    session.printOptions.setValues(vpDecorations=OFF)
    img_name = os.path.join(output_directory,"Sample"+str(i)+".png")
    session.printToFile(fileName=img_name, format=PNG, canvasObjects=(myViewports,))
    o1.close()
