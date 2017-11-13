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
class PriceFluctuation_Actor(MyDbEx, BaseFunc):
    def __init__(self, stocks, meanLen, threshold, StockClass=''):   #T:时间均线的时间长度，N:买卖点百分比阈值
        self.stocks=stocks
        self.StockClass=StockClass
        self.meanLen=meanLen
        self.threshold=threshold
        self.LoggerPrefixString='<%s><%s><mean:%d><Th:%f>' % (self.StockClass, json.dumps(self.stocks), self.meanLen, self.threshold)
        
        
        self.curStockNo=''
        self.curStockAmount=0
        self.curCash=10000.0        
        self.curProperty=self.curCash
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
        
        calcPastDays=90
        
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
        otherStock=self.stocks[1]

        #然后计算各股与第一个股票的收盘价比值
        CloseRate=Close.copy(deep=True)
        for stock in reversed(self.stocks):
            CloseRate[stock]=CloseRate[stock]/CloseRate[refStock]
            
        #剔除inf量,由于前面在合并数据时已经剔除了各个股票的停牌日，所以这一本来就不应该有无效值
        assert not CloseRate.isnull().values.any()
        CloseRate=CloseRate[['Date', otherStock]]

        #计算比值的meanLen天均值--均比值
        rateMeans=CloseRate.copy(deep=True)
        rateMeans[otherStock]=rateMeans[otherStock].rolling(window=self.meanLen,center=False).mean()
        rateMeans.fillna(value=1.0, inplace=True)

        #求比值相对于比值均值的波动
        rateFluctuation=rateMeans.copy(deep=True)
        rateFluctuation[otherStock]=CloseRate[otherStock]-rateMeans[otherStock]
        
        #保存到文件中  Close,CloseRate,rateMeans,rateFluctuation
        saveData=pd.merge(Close, CloseRate.rename(index=str, columns={otherStock: "CloseRate"}), on='Date')
        saveData=pd.merge(saveData, rateMeans.rename(index=str, columns={otherStock: "rateMeans"}), on='Date')
        saveData=pd.merge(saveData, rateFluctuation.rename(index=str, columns={otherStock: "rateFluctuation"}), on='Date')
        saveData.to_csv('bank_pricerate_fluctuation_'+'_'.join(self.stocks)+'_'+str(self.meanLen)+'.csv')
        
        
        saveData=saveData.sort_values(by=['Date'])[['Date', refStock, otherStock, "rateFluctuation"]]
        #取最后90天
        opeData=saveData[-90:].to_dict('list')
        title=list(opeData.keys())
        opeData=np.array(list(opeData.values())).T
        
        for day in range(opeData.shape[0]):
            
            self.selfLogger ('debug', 'Data:%s' % (self.num2datestr(opeData[day,title.index('Date')])))
            
            #第day天
            if opeData[day,title.index('rateFluctuation')]<=-self.threshold:
                #如果比值低于-self.threshold,则买入目标股票，卖出参考股票
                #sell ref stock
                self.selfLogger ('debug', 'rateFluctuation is lower than threshold(%f<=%f)' % (opeData[day,title.index('rateFluctuation')], -self.threshold))
                
                if self.curStockNo==refStock:
                    tempPrice=opeData[day,title.index(refStock)]
                    self.curCash += (self.curStockAmount*tempPrice)*0.999     #千分之一的印花税
                    self.selfLogger ('debug', "<Sell>:<%s><%s><%d@%f><%s>" % (self.curStockNo, self.num2datestr(opeData[day,title.index('Date')]), self.curStockAmount, tempPrice, self.curCash))
                    self.curStockAmount=0
                    self.curStockNo=""
                    self.curProperty=self.curCash#记录一下最新一次变为现金的情况
                #buy obj stock
                if self.curStockAmount==0:
                    self.curStockNo=otherStock
                    tempPrice=opeData[day,title.index(otherStock)]
                    self.curStockAmount=int(self.curCash/tempPrice)
                    self.curCash -= self.curStockAmount*tempPrice
                    self.selfLogger ('debug', "<Buy>:<%s><%s><%d@%f><%s>" % (self.curStockNo, self.num2datestr(opeData[day,title.index('Date')]), self.curStockAmount, tempPrice, self.curCash))                
            elif opeData[day,title.index('rateFluctuation')]>=self.threshold:
                #如果比值高于self.threshold，则卖出目标股票，买入参考股票
                #sell obj stock
                self.selfLogger ('debug', 'rateFluctuation is higher than threshold(%f>=%f)' % (opeData[day,title.index('rateFluctuation')], self.threshold))
                if self.curStockNo==otherStock:
                    tempPrice=opeData[day,title.index(otherStock)]
                    self.curCash += (self.curStockAmount*tempPrice)*0.999     #千分之一的印花税
                    self.selfLogger ('debug', "<Sell>:<%s><%s><%d@%f><%s>" % (self.curStockNo, self.num2datestr(opeData[day,title.index('Date')]), self.curStockAmount, tempPrice, self.curCash))
                    self.curStockAmount=0
                    self.curStockNo=""
                    self.curProperty=self.curCash#记录一下最新一次变为现金的情况   
                #buy ref stock
                if self.curStockAmount==0:
                    self.curStockNo=refStock
                    tempPrice = opeData[day,title.index(refStock)]
                    self.curStockAmount=int(self.curCash/tempPrice)
                    self.curCash -= self.curStockAmount*tempPrice
                    self.selfLogger ('debug', "<Buy>:<%s><%s><%d@%f><%s>" % (self.curStockNo, self.num2datestr(opeData[day,title.index('Date')]), self.curStockAmount, tempPrice, self.curCash))                                    
            else:
                #do nothing
                self.selfLogger ('debug', 'rateFluctuation is between threshold(%f<=%f<=%f)' % (-self.threshold, opeData[day,title.index('rateFluctuation')], self.threshold))
                pass
        

class observer_PriceFluctuation(Observer):
    def __init__(self):
        #some my code here
        #init actor(self.actors)
        self.actors=[]
        meanLenArray=[5,8,10,12,20] #days
        thresholdArray=[0.005,0.010,0.015,0.020]
        
        #bank stock
        stockListTemp=[item[0] for item in config.stockList['Bank']]

        #用n个stock的组合，进行模拟计算
        refStock=[stockListTemp[0]]
        otherStocks=stockListTemp[1:]
        for selectStocks in BaseFunc().selectElementFromList(otherStocks, 1):#任选1个股票与参考股票组合
            paraArray=[(refStock+selectStocks, meanLen, threshold) for meanLen in meanLenArray for threshold in thresholdArray]
            self.actors+=[PriceFluctuation_Actor(item[0], item[1], item[2], 'Bank') for item in paraArray]

        self.threadpool = ThreadPoolExecutor(max_workers=8)
        
        super(observer_PriceFluctuation, self).__init__()
        
    def end_opportunity_finder(self):
        result=[]
        for actor in self.actors:
            try:
                actor.selfLogger ('info', "<end><meanlen:%d><Property:%f>" % (actor.meanLen, actor.curProperty))
                result.append([json.dumps(actor.stocks), actor.meanLen, actor.curProperty, actor.curStockNo])
            except Exception as err:
                print (err)
                print(traceback.format_exc())
                #actor.selfLogger ('error', err)
        #排序result
        result.sort(key=lambda x:x[2], reverse=True)
        myGlobal.logger.info("Best policy is stocks=%s, mean=%d, best gain is %f, the stock should buy currently is %s" % (result[0][0], result[0][1], result[0][2], result[0][3]))
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