# -*- coding: utf-8 -*-

#Python 3.5.x

import numpy as np


__metaclass__ = type


#将cpu的数据计算函数移到这里，组成类



class cpu_algorithms_engine():
    
    def __init__(self, device_index=0, kernelFile=''):
        return
    
    def delete_engine(self):
        return
    
    def cl_algorithm_showClMemStruct(self):
        print('This is CPU calcEngine')              
        return
    
    #实现各种算法
    #求numpy一维数据中的最大值和最小值    
    def algorithm_vector_max_min(self, a_np):
        max_np = a_np.max()
        min_np = a_np.min()
        
        return max_np, min_np
    
    #实现矩阵的复制
    def algorithm_matrix_copy(self, a_np):
        return a_np.copy()
    
    #矩阵的每一行减去一个向量
    def algorithm_matrix_vector_sub(self, a_np, b_np):
        return a_np-b_np
    
    
    def algorithm_matrix_vector_curve_distance(self, dataSet, daysLenList, calcLen):
        distance_array=[]
        for col_index in range(dataSet.shape[1]):
            curve=dataSet[:,col_index]
            daysLen=daysLenList[col_index]
            temp_dist=[]
            for offset_index in range(calcLen):
                #curve[0:daysLen]和curve[offset_index+1:offset_index+1+daysLen]之间的平均距离
                temp_dist.append(abs(curve[0:daysLen]-curve[offset_index+1:offset_index+1+daysLen]).sum()/daysLen)
            distance_array.append(temp_dist)
        
        distance_array = np.array(distance_array).T
        return distance_array
    
    #矩阵的每一行除一个向量
    def algorithm_matrix_vector_div(self, a_np, b_np):
        return a_np/b_np
    
    def algorithm_matrix_mul_k_float(self, a_np, b_np):
        return a_np*b_np
    
    def algorithm_matrix_element_square_float(self, a_np):      
        return a_np**2
    
    def algorithm_matrix_rowadd_rooting(self, a_np):
        temp=a_np.sum(axis=1)    #axis=1方向求和，axis=1----行, axis=0----列
        return temp**0.5
    
    #Returns the indices that would sort an array.
    #使用双调算法进行升序排序，返回排序索引
    #a_g是一个一维数组，并且长度是2的幂次
    def algorithm_argsort(self, a_np):
        return a_np.argsort()       #----argsort()----Returns the indices(index) that would sort an array.
    
    