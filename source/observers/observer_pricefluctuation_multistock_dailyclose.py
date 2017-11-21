#*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

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

#这个Observer利用价格浮动寻找价格低点
#对于多个股票，以其中一个为基准，计算个股票的相对波动。并自动找出当前处于相对低值的股票
#
class PriceFluctuation_MultiStock_DailyClose_Actor(MyDbEx, BaseFunc):
    def __init__(self, stocks, meanLen, StockClass=''):   #T:时间均线的时间长度，N:买卖点百分比阈值
        self.stocks=stocks      #股票列表
        self.StockClass=StockClass      #股票分类
        self.meanLen=meanLen        #参考均线
        self.LoggerPrefixString='<%s><%s><mean:%d>' % (self.StockClass, json.dumps(self.stocks), self.meanLen)
        
        self.result=[]
        
        pass
    
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
        myGlobal.logger.info("newTicker:%s,meanLen:%d" % (json.dumps(self.stocks), self.meanLen))

        #取出各个股票收盘价
        #然后计算各股与第一个股票的收盘价比值
        #剔除inf量
        #计算比值的30天均值
        #计算比值相对比值均值的偏差
        
        #取出各个股票收盘价
        Close=None
        for stock in self.stocks:
            res=self.DbEx_GetDataByTitle(stock, ['Date', 'AdjClose'], outDataFormat=np.float32)
            #转化为pandas格式
            #tempData=pd.DataFrame(res[:,1], index=res[:,0].tolist(), columns=[stock])
            tempData=pd.DataFrame(res, columns=['Date', stock])

            try:
                if not Close:
                    Close=tempData
            except:
                #合并数据，以左右的index作为索引，由于没有指定"how"，所以保留左右数据的index的交集
                Close=pd.merge(Close, tempData, on='Date')
        
        Close = Close.sort_values(by=['Date'])
        
        refStock=self.stocks[0]

        #然后计算各股与第一个股票的收盘价比值
        CloseRate=Close.copy(deep=True)
        for stock in reversed(self.stocks):
            CloseRate[stock]=CloseRate[stock]/CloseRate[refStock]
            
        #剔除inf量,由于前面在合并数据时已经剔除了各个股票的停牌日，所以这一本来就不应该有无效值
        assert not CloseRate.isnull().values.any()

        #计算比值的meanLen天均值--均比值
        rateMeans=CloseRate.copy(deep=True)
        for stock in self.stocks:
            rateMeans[stock]=rateMeans[stock].rolling(window=self.meanLen,center=False).mean()
        rateMeans.fillna(value=1.0, inplace=True)

        #求比值相对于比值均值的波动
        rateFluctuation=rateMeans.copy(deep=True)
        for stock in self.stocks:
            rateFluctuation[stock]=CloseRate[stock]-rateMeans[stock]
        
        #保存到文件中  Close,CloseRate,rateMeans,rateFluctuation
        saveData=pd.merge(Close, CloseRate.rename(index=str, columns=dict(zip(self.stocks,map(lambda x:"CloseRate_"+x, self.stocks)))), on='Date')
        saveData=pd.merge(saveData, rateMeans.rename(index=str, columns=dict(zip(self.stocks,map(lambda x:"rateMeans_"+x, self.stocks)))), on='Date')
        saveData=pd.merge(saveData, rateFluctuation.rename(index=str, columns=dict(zip(self.stocks,map(lambda x:"rateFluctuation_"+x, self.stocks)))), on='Date')
        saveData.to_csv(self.StockClass+'_pricerate_fluctuation_multistock_'+str(self.meanLen)+'.csv')
        
        #到这里，需要的数据都已经计算并保存到文件中。
        #为了方便后期处理，这里将必要的数据进行处理
        self.result=[]
        for stock in self.stocks:
            self.result.append([stock, rateFluctuation[stock].tolist()[-1]])
        self.result.sort(key=lambda x:x[1], reverse=False)
        
        return

class observer_PriceFluctuation_MultiStock_DailyClose(Observer):
    def __init__(self):
        #some my code here
        self.actors=[]
        meanLenArray=[5,8,10,12,20] #days
        #thresholdArray=[0.005,0.010,0.015,0.020]
        
        #bank stock
        stockListTemp=[item[0] for item in config.stockList['Bank']]

        paraArray=[(stockListTemp, meanLen) for meanLen in meanLenArray]
        self.actors+=[PriceFluctuation_MultiStock_DailyClose_Actor(item[0], item[1], 'Bank') for item in paraArray]
        
        self.threadpool = ThreadPoolExecutor(max_workers=8)
        
        super(observer_PriceFluctuation_MultiStock_DailyClose, self).__init__()
        
    def end_opportunity_finder(self):
        result=[]
        for actor in self.actors:
            #每个actor的维度是（同类的一组股票，均线mean长度）
            try:
                actor.selfLogger ('info', "<end><meanlen:%d><stockClass:%s>" % (actor.meanLen, actor.StockClass))
                myGlobal.logger.info("Best policy for MultiStocks (meanLen=%d) is buy stock %s.(%s)", actor.meanLen, actor.result[0][0], json.dumps(actor.result))
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