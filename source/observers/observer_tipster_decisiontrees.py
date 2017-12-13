#*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

import os
import sys
import logging
import json
import traceback
import math
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
class Tipster_DecisionTrees_Actor(MyDbEx, BaseFunc):
    def __init__(self, stock, refTargetItem, calcEngine, StockClass=''):   #T:时间均线的时间长度，N:买卖点百分比阈值
        self.stock=stock
        self.StockClass=StockClass
        self.refTargetItem=refTargetItem    #参考的股票指标
        self.LoggerPrefixString='<%s><%s><DecisionTrees>' % (self.StockClass, self.stock)
        
        self.calcEngine=calcEngine
        
        #决策树和决策树的上次构造时间
        self.DecisionTree=None
        self.TreeCreateTime=None

        #当前使用的决策树的预测正确率和基于最新数据的预测结果
        self.tipsterRightRate=0.0
        self.tipsterIncrease=False
        pass
    
    #构造决策树
    def createDecisionTrees(self, calcData, startIndex, curveLen, refDataLen, labels, leastDistNum):
        assert 0
        return
    
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
        #如果当前是周末，就重新构造决策树
        
        
        #决策树需要数据是分类的，但是我们的就只是数据。为了即将数据分类，又避免只考虑当前数据不考虑趋势信息。需要将基本数据转化，每个指标数据
        #取相邻的三个数据点，三个数据点组成的折线可能是1.升降，2.升升，3.降升，4.降降，所以加工以后的数据分为4类，图形上恰好和拼音音调的4声对应，
        #所以就叫1声，2声，3声，4声吧
        
        #对self.stocks中所列举的股票进行计算
        myGlobal.logger.info("newTicker for DecisionTrees:%s" % (self.stock))
        
        calcPastDays=90
        
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
        assert calcData.dtype==np.float32
        
        #对数据进行分类
        for i in range(calcPastDays):
            #注意第一组数据没有涨跌幅，是需要预测的数据，所以不要参与决策树构建
            
            #第一组数据是
            calcData[i+1]
            #第二组数据是
            calcData[i+2]
            #第三组数据是
            calcData[i+3]
            
            #根据数据间的对比关系得出声调
            temp1=(calcData[i+1]-calcData[i+2])>0.0
            temp2=(calcData[i+2]-calcData[i+3])>0.0
            
            
        
        assert 0
        return
        

class observer_Tipster_DecisionTrees(Observer):
    def __init__(self):
        #some my code here
        #init actor(self.actors)
        self.actors=[]
        #参考的数据
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
            self.actors+=[Tipster_DecisionTrees_Actor(item, refTargetItem, cpu_algorithms_engine(), 'Bank') for item in stockListTemp]
        elif calcEngine_type=='OpenCL':
            self.actors+=[Tipster_DecisionTrees_Actor(item, refTargetItem, opencl_algorithms_engine(device_index=0, kernelFile='opencl/myKernels.cl'), 'Bank') for item in stockListTemp]
        else:
            assert 0
        
        self.threadpool = ThreadPoolExecutor(max_workers=8)
        
        super(observer_Tipster_DecisionTrees, self).__init__()
        
    def end_opportunity_finder(self):
        for actor in self.actors:
            try:
                actor.selfLogger ('info', "<end><stock:%s>" % (actor.stock))
                infoString="<%s>DecisionTrees Result is (RightRate:%f, Forecast:%s)" % (actor.stock, actor.tipsterRightRate, 'Increace' if actor.tipsterIncrease else 'Decreace')
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