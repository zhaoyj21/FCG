#!/usr/bin/python
# -*- coding: utf-8 -*-
# python version: 3.9

"""
Fatigue Crack Propagation simulation using ABAQUS XFEM
Author: Liu Yong, Tsinghua University
Date: 2022-4-16
Compared with v1.0, this version using the crack length increment instead of x-increment.Besides, try...except is used to avoid the stop of loop when abaqus is aborted
"""

import math
import numpy as np
from abaqus import mdb, session
import regionToolset, displayGroupMdbToolset as dgm, part, assembly, step, interaction, load, mesh, job, \
    connectorBehavior
from abaqusConstants import *
import os


def model(width, height, thickness, crack_tip, model_name, part_name, mat_name, elastic_mod, nu, num_contour,
          tensile_load, shear_load, element_size):
    # ==== create new CAE ====
    myModel = mdb.Model(name=model_name, modelType=STANDARD_EXPLICIT)
    # ======================= Create plate part ===========================
    plateSketch = myModel.ConstrainedSketch(name='plate', sheetSize=200.0)
    line1 = plateSketch.Line(point1=(0.0, 0.0), point2=(width, 0.0))
    line2 = plateSketch.Line(point1=(width, 0.0), point2=(width, height))
    line3 = plateSketch.Line(point1=(0.0, height), point2=(width, height))
    line4 = plateSketch.Line(point1=(0.0, height), point2=(0.0, 0.0))
    myPart = myModel.Part(dimensionality=THREE_D, name=part_name, type=DEFORMABLE_BODY)
    myPart.BaseSolidExtrude(sketch=plateSketch, depth=thickness)
    plateSketch.unsetPrimaryObject()
    # ======================= Partition plate part ========================
    d1 = myPart.DatumPointByCoordinate(coords=(0.0, 1.0 / 4.0 * height, 0.0))
    d2 = myPart.DatumPointByCoordinate(coords=(width, 1.0 / 4.0 * height, 0.0))
    d3 = myPart.DatumPointByCoordinate(coords=(width, 1.0 / 4.0 * height, thickness))
    dplane1 = myPart.DatumPlaneByThreePoints(point1=myPart.datums[d1.id], point2=myPart.datums[d2.id],
                                             point3=myPart.datums[d3.id])
    pickedCells = myPart.cells
    myPart.PartitionCellByDatumPlane(datumPlane=myPart.datums[dplane1.id], cells=pickedCells)
    d4 = myPart.DatumPointByCoordinate(coords=(0.0, 3.0 / 4.0 * height, 0.0))
    d5 = myPart.DatumPointByCoordinate(coords=(width, 3.0 / 4.0 * height, 0.0))
    d6 = myPart.DatumPointByCoordinate(coords=(width, 3.0 / 4.0 * height, thickness))
    dplane2 = myPart.DatumPlaneByThreePoints(point1=myPart.datums[d4.id], point2=myPart.datums[d5.id],
                                             point3=myPart.datums[d6.id])
    pickedCells = myPart.cells
    myPart.PartitionCellByDatumPlane(datumPlane=myPart.datums[dplane2.id], cells=pickedCells)
    # ======================= Create crack part (update) ===========================
    pointsOnCrack = tuple(crack_tip)
    crackSketch = myModel.ConstrainedSketch(name='crack', sheetSize=200.0)
    crackSketch.Spline(points=pointsOnCrack)
    myCrack = myModel.Part(name='crack', dimensionality=THREE_D, type=DEFORMABLE_BODY)
    myCrack.BaseShellExtrude(sketch=crackSketch, depth=thickness)
    # =======================       Material       ==================================
    myModel.Material(name=mat_name)
    myModel.materials[mat_name].Elastic(table=((elastic_mod, nu),))
    myModel.HomogeneousSolidSection(name='Section-1', material=mat_name, thickness=None)
    cells = myPart.cells
    region = regionToolset.Region(cells=cells)
    myPart.SectionAssignment(region=region, sectionName='Section-1', offset=0.0,
                             offsetType=MIDDLE_SURFACE, offsetField='',
                             thicknessAssignment=FROM_SECTION)
    # ===================   Assembly and Interaction   ===============================
    instanceName = part_name + '-1'
    myAssembly = myModel.rootAssembly
    plateInstance = myAssembly.Instance(name=instanceName, part=myPart, dependent=ON)
    crackInstance = myAssembly.Instance(name='crack-1', part=myCrack, dependent=ON)
    myAssembly.translate(instanceList=('crack-1',), vector=(0.0, 0.0, 0.0))
    # crack definition-xfem
    crackFace = crackInstance.faces
    myAssembly.Set(faces=crackFace, name='crackFace')
    crackDomain = plateInstance.cells.findAt(((width / 2.0, height / 2.0, 0.0),))
    myAssembly.Set(cells=crackDomain, name='crackDomain')
    myAssembly.engineeringFeatures.XFEMCrack(name='Crack-1', crackDomain=myAssembly.sets['crackDomain'],
                                             allowCrackGrowth=False, crackLocation=myAssembly.sets['crackFace'])
    # ==========================       Step        ==================================
    myModel.StaticStep(name='Step-1', previous='Initial', maxNumInc=10000,
                       initialInc=0.001, minInc=1e-08, maxInc=0.1)
    myModel.fieldOutputRequests['F-Output-1'].setValues(variables=('S', 'LE', 'U', 'PHILSM',
                                                                   'PSILSM', 'STATUS', 'STATUSXFEM'))
    myModel.historyOutputRequests['H-Output-1'].setValues(contourIntegral='Crack-1', sectionPoints=DEFAULT,
                                                          rebar=EXCLUDE, numberOfContours=num_contour,
                                                          contourType=K_FACTORS, kFactorDirection=MERR,
                                                          frequency=LAST_INCREMENT)
    # ==========================      Load     ======================================
    bottomFace = plateInstance.faces.getByBoundingBox(0.0, -0.000001, 0.0, width, +0.00001, thickness)
    region = regionToolset.Region(faces=bottomFace)
    myModel.DisplacementBC(name='BC-bottom', createStepName='Initial',
                           region=region, u1=SET, u2=SET, u3=SET, ur1=SET, ur2=SET, ur3=SET,
                           amplitude=UNSET, distributionType=UNIFORM, fieldName='', localCsys=None)
    topFace = plateInstance.faces.getByBoundingBox(0.0, height - 0.000001, 0.0, width, height + 0.00001, thickness)
    region = regionToolset.Region(side1Faces=topFace)
    myModel.SurfaceTraction(name='top-TenLOAD', createStepName='Step-1',
                            region=region, magnitude=tensile_load, directionVector=((0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
                            distributionType=UNIFORM, field='', localCsys=None, traction=GENERAL)
    if shear_load != 0:
        region = regionToolset.Region(side1Faces=topFace)
        myModel.SurfaceTraction(name='top-ShearLOAD', createStepName='Step-1',
                                region=region, magnitude=shear_load, directionVector=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
                                distributionType=UNIFORM, field='', localCsys=None, traction=GENERAL)
    # ==========================      Mesh      =====================================
    myPart.seedPart(size=element_size, deviationFactor=0.1, minSizeFactor=0.1)
    myPart.generateMesh()
    # ==========================     Submit     =====================================
    myAssembly.regenerate()
    myJob = mdb.Job(name=model_name, model=myModel, description='', type=ANALYSIS, atTime=None,
                    waitMinutes=0, waitHours=0, queue=None, memory=90, memoryUnits=PERCENTAGE,
                    getMemoryFromAnalysis=True, explicitPrecision=SINGLE,
                    nodalOutputPrecision=SINGLE, echoPrint=OFF, modelPrint=OFF,
                    contactPrint=OFF, historyPrint=OFF, userSubroutine='', scratch='',
                    resultsFormat=ODB, multiprocessingMode=DEFAULT, numCpus=5, numDomains=5)
    myJob.submit(consistencyChecking=OFF)
    myJob.waitForCompletion()
    # messageType = myJob.messages[(-1)].type
    # if messageType == ABORTED or messageType == ERROR:
    #     return False
    # if messageType == JOB_COMPLETED:
    #     return True


def read(wd, model_name):
    file_name = model_name + ".dat"
    abs_path = os.path.join(wd, file_name)
    f = open(abs_path, "r")
    lines = f.readlines()
    datContent = [i.strip() for i in lines]
    #  =======================      read SIF      ==============================
    for i in datContent:
        if 'XFEM_1       K1:' in i:
            row_num = datContent.index(i)
    SIFI = (float(datContent[row_num].split()[3]) + float(datContent[row_num].split()[4]) + float(
        datContent[row_num].split()[5]) + float(datContent[row_num].split()[6])) / 4.0
    SIFII = (float(datContent[row_num + 1].split()[2]) + float(datContent[row_num + 1].split()[3]) + float(
        datContent[row_num + 1].split()[4]) + float(datContent[row_num + 1].split()[5])) / 4.0
    #  ====================    read crack vector     ==============================
    for i in datContent:
        if 'LOCAL DIRECTION OF VIRTUAL CRACK PROPAGATION' in i:
            row_direction = datContent.index(i)
            break
    VECTOR = (float(datContent[row_direction].split()[-3]), float(datContent[row_direction].split()[-2]),
              float(datContent[row_direction].split()[-1]))
    f.close()
    return SIFI, SIFII, VECTOR


def angle(KI, KII, vector):
    # calculate the current crack propagation angle
    # 逆时针为正，顺时针为负
    cur_angle = math.degrees(
        math.atan2(vector[1], vector[0]))  # the first parameter-y, the second-x. obtain the angle with positive x
    # 根据KII判断偏转角度正负，KII<0,相对于原扩展方向顺时针旋转，deflect_angle<0; KII>0, deflect_angle>0 (与ABAQUS中的定义相反）
    if KII >= 0:
        deflect_angle = math.acos(
            (3 * KII ** 2 + math.sqrt(KI ** 4 + 8 * KI ** 2 * KII ** 2)) / (KI ** 2 + 9 * KII ** 2))
        deflect_angle = math.degrees(deflect_angle)
    else:
        deflect_angle = -math.acos(
            (3 * KII ** 2 + math.sqrt(KI ** 4 + 8 * KI ** 2 * KII ** 2)) / (KI ** 2 + 9 * KII ** 2))
        deflect_angle = math.degrees(deflect_angle)
    global_angle = cur_angle + deflect_angle
    print('cur:', cur_angle)
    return global_angle


def tip(crack_tip, angle_global, delta_a):
    original_x = crack_tip[-1][0]
    original_y = crack_tip[-1][1]
    new_x = original_x + delta_a * math.cos(math.radians(angle_global))
    new_y = original_y + delta_a * math.sin(math.radians(angle_global))
    new_tip = (new_x, new_y)
    return new_tip


if __name__ == '__main__':
    # # ===== Constant Parameters =====
    width_def = 10  # 板宽
    height_def = 20  # 板高
    thickness_def = 0.1  # 板厚名称
    part_name_def = 'plate'  # 平板名称
    mat_name_def = 'Ni'  # 材料名称
    num_contour_def = 5  # 围道数量
    element_size_def = 0.11  # 网格尺寸
    delta_a = 0.3  # 裂纹扩展增量
    num_sample = 1  # 需要模拟的路径个数
    x_boundary = 9.0  # x方向的边界
    ymin_boundary = 0.0  # y方向最小值
    ymax_boundary = height_def  # y方向最大值
    # # ==== 根工作目录 ====
    base_directory = "D:/temp/ABAQUS2021/xfemV1-1/"
    # # ==== 样本控制参数 ====
    total_sample = 30  # 样本数量
    for i in range(1, total_sample + 1):
        # # ===== 为每个样本创建一个路径 =====
        work_directory = base_directory + "sample" + str(i)
        os.mkdir(work_directory)
        os.chdir(work_directory)
        Mdb()
        # # ===== 每个样本之间变化的参数 =====
        boundary_flag = True  # 用于判断当前样本是否结束
        load_boundary_flag = True  # 用于判断载荷是否变化
        ith_sample = 1  # 当前是第i个样本
        increment = 0  # 当前是第i个样本的第increment扩展步
        load_boundary = 2.0  # 用于判断裂纹尖端是否到底载荷边界
        num_load = 8  # 载荷变化次数
        crack_tip_def = [(0.0, 10.0), (1.0, 10.0)]
        elastic_mod_def = 200000
        nu_def = 0.31
        # # ===== 输出结果到result.txt文件中
        output = open('result.txt', 'w')
        output.write("sample" + str(i) + "\n")
        output.write("Incre\tTip_x\tTip_y\tKI\tKII\tTensile\tShear\n")
        while boundary_flag:
            # # ==== 在载荷变化时需要改变的参数 ====
            tensile_load_def = float(np.random.normal(loc=200.0, scale=50.0, size=1))  # 高斯分布-拉伸载荷
            shear_load_def = float(np.random.normal(loc=100.0, scale=50.0, size=1))  # 高斯分布-剪切载荷
            while load_boundary_flag:
                try:
                    # # ===== Build FE Model =====
                    model_name_def = 'Sample' + str(i) + 'Incre' + str(increment)
                    model(width_def, height_def, thickness_def, crack_tip_def, model_name_def, part_name_def, mat_name_def,
                          elastic_mod_def, nu_def, num_contour_def, tensile_load_def, shear_load_def, element_size_def)
                    # # ==== Read the Calculated SIF ====
                    KI, KII, vector = read(work_directory, model_name_def)
                    # # ==== Calculate the angle ====
                    angle_global = angle(KI, KII, vector)
                    # # ==== Calculate the new crack tip ====
                    crack_tip_def.append(tip(crack_tip_def, angle_global, delta_a))
                    # # ==== Output the result of each increment ====
                    output.write(
                        str(increment) + "\t" + str(crack_tip_def[-2][0]) + "\t" + str(crack_tip_def[-2][1]) + "\t" + str(
                            KI) + "\t" + str(KII) + "\t" + str(tensile_load_def) + "\t" + str(shear_load_def) + "\n")
                    # # ==== Judge the crack tip and geometry boundary ====
                    if (crack_tip_def[-1][0] > x_boundary) or (crack_tip_def[-1][1] < ymin_boundary) or (
                            crack_tip_def[-1][1] > ymax_boundary):
                        print('The crack has reached the defined boundary and this sample is finished')
                        boundary_flag = False
                        break
                    else:
                        increment = increment + 1
                        if crack_tip_def[-1][0] < load_boundary:
                            continue
                        else:
                            print('the crack has reached the load boundary and the load will be changed')
                            load_boundary = load_boundary + 1.0
                            break
                except:
                    output_bug = open("D:/temp/ABAQUS2021/xfemV1-1/bug.txt",'a')
                    output_bug.write("sample" + str(i) + "\n")
                    output_bug.close()
                    boundary_flag = False
                    break
        # save the cae file
        cae_name = "sample" + str(i)
        path_name = os.path.join(work_directory, cae_name)
        output.close()
        mdb.saveAs(pathName=path_name)
