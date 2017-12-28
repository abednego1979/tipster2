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



def loadDataSet():
    dataMat = []; labelMat = []
    fr = open('testSet.txt')
    for line in fr.readlines():
        lineArr = line.strip().split()
        dataMat.append([1.0, float(lineArr[0]), float(lineArr[1])])
        labelMat.append(int(lineArr[2]))
    return dataMat,labelMat

def sigmoid(inX):
    return 1.0/(1+np.exp(-inX))

def gradAscent(dataMatIn, classLabels):
    dataMatrix = np.mat(dataMatIn)             #convert to NumPy matrix
    labelMat = np.mat(classLabels).transpose() #convert to NumPy matrix
    m,n = np.shape(dataMatrix)
    alpha = 0.001
    maxCycles = 500
    weights = np.ones((n,1))
    for k in range(maxCycles):              #heavy on matrix operations
        h = sigmoid(dataMatrix*weights)     #matrix mult
        error = (labelMat - h)              #vector subtraction
        weights = weights + alpha * dataMatrix.transpose()* error #matrix mult
    return weights




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
    
    
    ####回归Logistic的主要算法########################################################
 
    
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

        return
        

class observer_Tipster_Logistic(Observer):
    def __init__(self):
        #some my code here
        #init actor(self.actors)
        self.actors=[]
        #参考的数据
        refTargetItem=['Volume', 'mean_3_RatePrice', 'mean_5_RatePrice', 'mean_10_RatePrice', 'mean_20_RatePrice', 'mean_30_RatePrice']
        
        
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
            self.actors+=[Tipster_Logistic_Actor(item, refTargetItem, cpu_algorithms_engine(), 'Bank') for item in stockListTemp]
        elif calcEngine_type=='OpenCL':
            self.actors+=[Tipster_Logistic_Actor(item, refTargetItem, opencl_algorithms_engine(device_index=0, kernelFile='opencl/myKernels.cl'), 'Bank') for item in stockListTemp]
        else:
            assert 0
        
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