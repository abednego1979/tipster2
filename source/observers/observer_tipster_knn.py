#*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

import os
import sys
import logging
import json
import traceback
from .observer import Observer
import myGlobal
import config
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, wait

from BaseFunc import BaseFunc
from database.DB_Ex import MyDbEx
from CalcEngine_CPU import *

#在两个股票中间，根据每日收盘价寻找套利机会
class Tipster_Knn_Actor(MyDbEx, BaseFunc):
    def __init__(self, stock, refTargetItem, refTargetCurveLen, calcEngine, StockClass=''):   #T:时间均线的时间长度，N:买卖点百分比阈值
        self.stock=stock
        self.StockClass=StockClass
        self.refTargetItem=refTargetItem
        self.refTargetCurveLen=refTargetCurveLen
        self.LoggerPrefixString='<%s><%s><KNN>' % (self.StockClass, self.stock)
        
        self.calcEngine=calcEngine

        self.tipsterRightRate=0.0
        self.tipsterIncrease=False
        pass
    
    def autoNorm(self, dataSet):
        #'''利用cpu或gpu进行数据的归一化'''
        minVals=[]
        maxVals=[]
        ranges=[]
        #获取各个数据的最大最小值
        for i in range(dataSet.shape[1]):
            max_temp, min_temp = self.calcEngine.algorithm_vector_max_min(dataSet[:,i])
            minVals.append(min_temp)
            maxVals.append(max_temp)
        
        minVals=np.array(minVals)
        maxVals=np.array(maxVals)
        ranges=maxVals-minVals
        m=dataSet.shape[0]
        
        #进行矩阵的复制,normDataSet=dataSet.copy()
        normDataSet = self.calcEngine.algorithm_matrix_copy(dataSet)
        
        #矩阵减,normDataSet=normDataSet-np.tile(minVals,(m,1))
        normDataSet = self.calcEngine.algorithm_matrix_vector_sub(normDataSet, minVals)
        
        #矩阵除,normDataSet=normDataSet/np.tile(ranges,(m,1))
        normDataSet = self.calcEngine.algorithm_matrix_vector_div(normDataSet, ranges)
        
        return normDataSet,ranges,minVals
    
    #kNN,求baseData对比refData中的前512条数据，计算距离最小的50个数据的labels中上涨和下跌的个数
    def tipster_kNN(self, baseData, refData, refDataLen, labels, leastDistNum):
        #KNN算法
        #求distance
        distances=[]
        for i in range(refDataLen):
            #求baseData和refData[i]的距离
            temp_data=baseData-refData[i]
            temp_data=temp_data*temp_data
            distance = math.sqrt(np.sum(temp_data))
    
            distances.append((distance, labels[i]))
    
        #基于距离进行排序
        distances.sort(key=lambda x:x[0], reverse=False)
    
        #距离最小的50个向量对应的涨幅
        distances=distances[:leastDistNum]
        distances=[distances[1] for item in distances]
        #统计预测上涨和下跌的个数
        distances_increase=[item for item in distances if item>0]
        distances_decrease=[item for item in distances if item<0]        
        
        return len(distances_increase), len(distances_decrease)
    
    def selfLogger(self, level, OutString):
        try:
            if level=='info':
                myGlobal.logger.info(self.LoggerPrefixString+OutString)
            elif level=='debug':
                myGlobal.logger.debug(self.LoggerPrefixString+OutString)
            elif level=='error':
                myGlobal.logger.error(self.LoggerPrefixString+OutString)
        except Exception as err:
            print (err)
            print(traceback.format_exc())
    
    def newTicker(self):
        #对self.stocks中所列举的股票进行计算
        myGlobal.logger.info("newTicker:%s" % (self.stock))
        
        calcPastDays=90
        
        #取出这个股票的各个参考信息
        #计算最近calcPastDays天的预测准确率
        #取出self.stock的self.refTargetItem各项数据
        #多取的两列，Date是为了排序的需要，PriceIncreaseRate是作为kNN的分类标签
        getItemTitle=['Date', 'PriceIncreaseRate']+self.refTargetItem
        bData=self.DbEx_GetDataByTitle(self.stock, getItemTitle, outDataFormat=np.float32)
        
        if bData.shape[0]<640:
            assert 0
            return None      
        
        #只取一定数量条数据计算
        dateTime=bData[:640,0]
        labels=bData[:640,1]
        calcData=bData[:640,2:]
        #进行数据归一化
        calcData,ranges,minVals=self.autoNorm(calcData)
        assert calcData.dtype==np.float32
        
        newestDateTime=dateTime[0]
        newestLabel=labels[0]

        dateTime=dateTime[1:]
        labels=labels[1:]
        
        #由于用曲线做KNN的计算基本数据，所以先将数据基本单元变为曲线（数组）
        temp_calcData=[]
        for index in range(640-self.refTargetCurveLen+1):
            temp_line=[]
            for col in range(len(self.refTargetItem)):
                temp_line.append(calcData[index:index+self.refTargetCurveLen, col])
            temp_calcData.append(temp_line)
        calcData=temp_calcData
        
        newestCalcData=calcData[0]
        calcData=calcData[1:]
        
        #求出预测准确率
        #用第N个数据，与N+1到N+512的数据做KNN比较，预测第N数据的走势
        tipsterRightNum=0
        tipsterRightRate=0.0
        for index in range(calcPastDays):
            baseData=calcData[index]
            refData=calcData[index+1:]
            
            increase_num, decrease_num=self.tipster_kNN(baseData, refData, 512, labels[index+1:], 50)
            
            #预测上涨还是下跌
            temp_factor=(increase_num-decrease_num)*labels[index]
            if temp_factor>0:#预测的涨跌和实际的涨跌方向一致
                tipsterRightNum+=1
            
        self.tipsterRightRate = tipsterRightNum*1.0/calcPastDays        #预测成功率
        
        #对最新一组数据进行预测
        baseData=newestCalcData
        refData=calcData
        increase_num, decrease_num=self.tipster_kNN(baseData, refData, 512, labels, 50)
            
        if (len(distances_increase)-len(distances_decrease))>0:
            #预测会上涨
            self.tipsterIncrease=True
            pass

        return
        

class observer_Tipster_Knn(Observer):
    def __init__(self):
        #some my code here
        #init actor(self.actors)
        self.actors=[]
        #参考的数据，如Volume#3代表要参考Volume，而距离是使用3天曲线之间的距离。
        refTargetItem=['Volume', 'Volume', 'mean_3_RatePrice', 'mean_5_RatePrice', 'mean_10_RatePrice', 'mean_20_RatePrice', 'mean_30_RatePrice']
        
        
        calcEngine_type='CPU'
        if config.g_opencl_accelerate:
            OC = OpenCL_Cap()
            if len(OC.handles):
                #calcEngine = opencl_algorithms_engine(device_index=0, kernelFile='opencl/myKernels.cl')
                calcEngine_type='OpenCL'
        
        #bank stock
        stockListTemp=[item[0] for item in config.stockList['Bank']]
        
        #创建actor列表
        if calcEngine_type=='CPU':
            self.actors+=[Tipster_Knn_Actor(item, refTargetItem, 5, cpu_algorithms_engine(), 'Bank') for item in stockListTemp]
        elif calcEngine_type=='OpenCL':
            self.actors+=[Tipster_Knn_Actor(item, refTargetItem, 5, opencl_algorithms_engine(device_index=0, kernelFile='opencl/myKernels.cl'), 'Bank') for item in stockListTemp]
        else:
            assert 0
        
        self.threadpool = ThreadPoolExecutor(max_workers=8)
        
        super(observer_Tipster_Knn, self).__init__()
        
    def end_opportunity_finder(self):
        result=[]
        for actor in self.actors:
            try:
                actor.selfLogger ('info', "<end><meanlen:%d><Property:%f>" % (actor.meanLen, actor.curProperty))
                result.append([json.dumps(actor.stocks), actor.meanLen, actor.curProperty, actor.curStockNo, actor.threshold])
                pass
            except Exception as err:
                print (err)
                print(traceback.format_exc())
                #actor.selfLogger ('error', err)

        pass
                
                
    def opportunity(self):
        if False:
            futures = []
            for actor in self.actors:
                futures.append(self.threadpool.submit(actor.newTicker))
            wait(futures)
        else:
            for actor in self.actors:
                try:
                    actor.newTicker()
                except Exception as err:
                    print (err)
                    print(traceback.format_exc())
                    actor.selfLogger ('error', err)