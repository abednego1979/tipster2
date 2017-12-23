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
    
    
    ####决策树的主要算法########################################################
    
    #计算香农信息熵,dataSet的最后一列是lables
    def calcShannonEnt(self, dataSet):
        numEntries = len(dataSet)
        labelCounts = {}
        for featVec in dataSet: #the the number of unique elements and their occurance
            currentLabel = featVec[-1]
            if currentLabel not in labelCounts.keys(): labelCounts[currentLabel] = 0
            labelCounts[currentLabel] += 1
        shannonEnt = 0.0
        for key in labelCounts:
            prob = float(labelCounts[key])/numEntries
            shannonEnt -= prob * math.log(prob,2) #log base 2
        return shannonEnt
    
    #划分数据集，对dataSet各条数据的第axis列数据，如果数值等于value就提取出来。
    #如果第axis列数据，有value1，value2，...，valueN几种情况，那么N次调用本函数可以将dataSet划分为N个子集
    def splitDataSet(self, dataSet, axis, value):
        retDataSet = []
        for featVec in dataSet:
            if featVec[axis] == value:
                reducedFeatVec = featVec[:axis]     #chop out axis used for splitting
                reducedFeatVec.extend(featVec[axis+1:])
                retDataSet.append(reducedFeatVec)
        return retDataSet
    
    #对每一列数据用splitDataSet划分数据集并用calcShannonEnt计算划分以后的熵增益，确认用哪列去划分数据最优
    def chooseBestFeatureToSplit(self, dataSet):
        numFeatures = len(dataSet[0]) - 1      #the last column is used for the labels
        baseEntropy = self.calcShannonEnt(dataSet)
        bestInfoGain = 0.0; bestFeature = -1
        for i in range(numFeatures):        #iterate over all the features
            featList = [example[i] for example in dataSet]#create a list of all the examples of this feature
            uniqueVals = set(featList)       #get a set of unique values
            newEntropy = 0.0
            for value in uniqueVals:
                subDataSet = self.splitDataSet(dataSet, i, value)
                prob = len(subDataSet)/float(len(dataSet))
                newEntropy += prob * self.calcShannonEnt(subDataSet)     
            infoGain = baseEntropy - newEntropy     #calculate the info gain; ie reduction in entropy
            if (infoGain > bestInfoGain):       #compare this to the best gain so far
                bestInfoGain = infoGain         #if better than current best, set to best
                bestFeature = i
        return bestFeature                      #returns an integer
    
    #
    def majorityCnt(self, classList):
        classCount={}
        for vote in classList:
            if vote not in classCount.keys(): classCount[vote] = 0
            classCount[vote] += 1
        sortedClassCount = sorted(classCount.iteritems(), key=operator.itemgetter(1), reverse=True)
        return sortedClassCount[0][0]
    
    #这里的参数labels是各列数据的标题
    def createTree(self, dataSet,labels):
        classList = [example[-1] for example in dataSet]
        if classList.count(classList[0]) == len(classList): 
            return classList[0]#stop splitting when all of the classes are equal
        if len(dataSet[0]) == 1: #stop splitting when there are no more features in dataSet
            return self.majorityCnt(classList)
        bestFeat = self.chooseBestFeatureToSplit(dataSet)
        bestFeatLabel = labels[bestFeat]
        myTree = {bestFeatLabel:{}}
        del(labels[bestFeat])
        featValues = [example[bestFeat] for example in dataSet]
        uniqueVals = set(featValues)
        for value in uniqueVals:
            subLabels = labels[:]       #copy all of labels, so trees don't mess up existing labels
            myTree[bestFeatLabel][value] = self.createTree(self.splitDataSet(dataSet, bestFeat, value),subLabels)
        return myTree
    
    
    #构造决策树
    def createDecisionTrees(self, calcData, calcDataTitles, startIndex, refDataLen, labels):
        dataSet=np.hstack((calcData, labels[:calcData.shape[0]][:,np.newaxis]))
        dataSet=dataSet[startIndex:startIndex+refDataLen, :]
        #createTree接受的数据是list形式
        return self.createTree(dataSet.tolist(), calcDataTitles)
    
    def classify(self, inputTree,featLabels,testVec):
        firstStr = inputTree.keys()[0]
        secondDict = inputTree[firstStr]
        featIndex = featLabels.index(firstStr)
        key = testVec[featIndex]
        valueOfFeat = secondDict[key]
        if isinstance(valueOfFeat, dict): 
            classLabel = self.classify(valueOfFeat, featLabels, testVec)
        else: classLabel = valueOfFeat
        return classLabel
    
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
        #如果当前是周末，就重新构造决策树
        
        
        #决策树需要数据是分类的，但是我们的就只是数据。为了即将数据分类，又避免只考虑当前数据不考虑趋势信息。需要将基本数据转化，每个指标数据
        #取相邻的三个数据点，三个数据点组成的折线可能是1.升降，2.升升，3.降升，4.降降，所以加工以后的数据分为4类，图形上恰好和拼音音调的4声对应，
        #所以就叫1声，2声，3声，4声吧
        
        #对self.stocks中所列举的股票进行计算
        myGlobal.logger.info("newTicker for DecisionTrees:%s" % (self.stock))
        
        
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
        assert calcData.dtype==np.float32
        
        #对数据进行分类
        tone=[]
        for i in range(calcPastDays):
            #根据数据间的对比关系得出声调
            temp=np.vstack((((calcData[i+0]-calcData[i+1])>0.0), ((calcData[i+1]-calcData[i+2])>0.0)))
            tone_line=[]
            for j in range(calcData.shape[1]):
                if temp[1,j]==True and temp[0,j]==False:
                    #1声
                    tone_line.append(1)
                elif temp[1,j]==True and temp[0,j]==True:
                    #2声
                    tone_line.append(2)
                elif temp[1,j]==False and temp[0,j]==True:
                    #3声
                    tone_line.append(3)
                else:   #temp[1,j]==False and temp[0,j]==False:
                    #4声
                    tone_line.append(4)
                    
            tone.append(tone_line)
        calcData=np.array(tone)
        
        #labels也要离散化
        labels=labels>0.0
            
        #下面开始构造决策树
        #用index从（forecastDataLen+testDataLen）到calcPastDays的数据构造决策树
        calcDataTitles=self.refTargetItem
        self.DecisionTree=self.createDecisionTrees(calcData, calcDataTitles, forecastDataLen+testDataLen, createTreeDataLen, labels)
        self.TreeCreateTime=datetime.datetime.today()

        
        #用index从（forecastDataLen）到（forecastDataLen+testDataLen）的数据计算决策树的预测准确率
        rightCount=0
        for i in range(forecastDataLen, forecastDataLen+testDataLen):
            #用calcData[i]预测，用labels[i]检查预测是否正确，计算总正确率
            temp_forecast=self.classify(self.DecisionTree, calcDataTitles, calcData[i].tolist)
            if not(temp_forecast ^ labels[i]):
                rightCount+=1
        
        self.tipsterRightRate=1.0*rightCount/testDataLen
                
        #用决策树预测
        #用calcData[0]预测
        self.tipsterIncrease=self.classify(self.DecisionTree, calcDataTitles, calcData[0].tolist)

        return
        

class observer_Tipster_DecisionTrees(Observer):
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