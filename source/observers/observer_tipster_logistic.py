#*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

import os
import sys
import logging
import json
import traceback
import datetime
import math
import random
import operator
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
class Tipster_Logistic_Actor(MyDbEx, BaseFunc):
    def __init__(self, stock, refTargetItem, calcEngine, StockClass=''):   #T:时间均线的时间长度，N:买卖点百分比阈值
        self.stock=stock
        self.StockClass=StockClass
        self.refTargetItem=refTargetItem    #参考的股票指标
        self.LoggerPrefixString='<%s><%s><Logistic>' % (self.StockClass, self.stock)
        
        self.calcEngine=calcEngine
        
        #回归系数
        self.Weight=None
        self.WeightCreateTime=None

        #当前使用的回归方式的预测正确率和基于最新数据的预测结果
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
    
    
    ####回归Logistic的主要算法########################################################
    
    def sigmoid(self, inX):
        return 1.0/(1+np.exp(-inX))    
    
    def gradAscent(self, dataMatIn, classLabels):
        dataMatrix = np.mat(dataMatIn)             #convert to NumPy matrix
        labelMat = np.mat(classLabels).transpose() #convert to NumPy matrix
        m,n = np.shape(dataMatrix)
        alpha = 0.001
        maxCycles = 500
        weights = cones((n,1))
        for k in range(maxCycles):              #heavy on matrix operations
            h = self.sigmoid(dataMatrix*weights)     #matrix mult
            error = (labelMat - h)              #vector subtraction
            weights = weights + alpha * dataMatrix.transpose()* error #matrix mult
        return weights
    
    def stocGradAscent1(self, dataMatrix, classLabels, numIter=150):
        m,n = np.shape(dataMatrix)
        weights = np.ones(n)   #initialize to all ones
        for j in range(numIter):
            dataIndex = list(range(m))
            for i in range(m):
                alpha = 4/(1.0+j+i)+0.0001    #apha decreases with iteration, does not 
                randIndex = int(random.uniform(0,len(dataIndex)))#go to 0 because of the constant
                h = self.sigmoid(sum(dataMatrix[randIndex]*weights))
                error = classLabels[randIndex] - h
                weights = weights + alpha * error * dataMatrix[randIndex]
                del(dataIndex[randIndex])
        return weights    
 
    
    ############################################################
    
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
        myGlobal.logger.info("newTicker for Logistic:%s" % (self.stock))
        
        #某些局部变量的初始化
        forecastDataLen=1   #预测的数据长度，肯定为1
        testDataLen=20      #用于构造完决策树，测试正确率的数据量
        createTreeDataLen=90#用于构造决策树的数据量
        calcPastDays=forecastDataLen+testDataLen+createTreeDataLen

        #取出基本数据
        getItemTitle=['Date', 'PriceIncreaseRate']+self.refTargetItem
        bData=self.DbEx_GetDataByTitle(self.stock, getItemTitle, outDataFormat=np.float32)
        if bData.shape[0]<(calcPastDays+10):
            self.tipsterRightRate=0.0
            self.tipsterIncrease=False
            return
        
        
        
        #只取一定数量条数据计算
        dateTime=bData[:calcPastDays+10, 0]
        labels=bData[:calcPastDays+10, 1]
        calcData=bData[:calcPastDays+10, 2:]
        #进行数据归一化
        calcData,ranges,minVals=self.autoNorm(calcData)        
        #在calcData前增加一列1.0
        calcData = np.insert(calcData, 0, values=np.ones(calcData.shape[0], dtype=np.float32), axis=1)
        assert calcData.dtype==np.float32
        
        #labels也要离散化，这里离散化为1（涨）和0（跌）
        labels=np.where(labels > 0, 1, 0)
        
        #下面开始进行回归，求最佳W系数
        #用index从（forecastDataLen+testDataLen）到calcPastDays的数据回归
        weights = self.stocGradAscent1(calcData[forecastDataLen+testDataLen:calcPastDays], labels[forecastDataLen+testDataLen:calcPastDays])
        
        #显示计算得到的权重值
        #print (weights)
        
        #用index从（forecastDataLen）到（forecastDataLen+testDataLen）的数据计算回归算法的预测准确率
        rightCount=0
        errorCount=0
        uncertainCount=0
        for i in range(forecastDataLen, forecastDataLen+testDataLen):
            h = self.sigmoid(sum(calcData[i]*weights))
            temp_forecast=1 if h>0.5 else 0
            if not(temp_forecast ^ labels[i]):
                rightCount+=1
            else:
                errorCount+=1
        self.tipsterRightRate=1.0*rightCount/testDataLen
        
        #用回归算法预测
        #用calcData[0]预测
        h = self.sigmoid(sum(calcData[0]*weights))
        self.tipsterIncrease =1 if h>0.5 else 0

        return
        

class observer_Tipster_Logistic(Observer):
    def __init__(self):
        #some my code here
        #init actor(self.actors)
        self.actors=[]
        #参考的数据
        refTargetItem=['Volume', 'mean_3_RatePrice', 'mean_5_RatePrice', 'mean_10_RatePrice', 'mean_20_RatePrice', 'mean_30_RatePrice']
        
        
        for stockType in config.stockList.keys():
            #some type of stock
            stockListTemp=[item[0] for item in config.stockList[stockType]]
        
            #创建actor列表
            self.actors+=[Tipster_Logistic_Actor(item, refTargetItem, cpu_algorithms_engine(), stockType) for item in stockListTemp]
        
        self.threadpool = ThreadPoolExecutor(max_workers=8)
        
        super(observer_Tipster_Logistic, self).__init__()
        
    def end_opportunity_finder(self):
        for actor in self.actors:
            try:
                actor.selfLogger ('info', "<end><stock:%s>" % (actor.stock))
                infoString="<%s>Logistic Result is (RightRate:%f, Forecast:%s)" % (actor.stock, actor.tipsterRightRate, 'Increace' if actor.tipsterIncrease else 'Decreace')
                myGlobal.logger.info(infoString)
                
                try:
                    with open('MailOutInfo.txt', 'a') as pf:
                        pf.write(infoString+'\r\n')
                except:
                    pass
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