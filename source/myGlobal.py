# -*- coding: utf-8 -*-

#Python 3.5.x


import logging
import config

logger=None
userChooseProxySet=None


#class signals():
    #signals={}
    
    #def __init__(self):
        #for marketname in config.markets:
            #self.signals[marketname]={}

    #def setSignal(self, market, signalName, signalValue):
        #logger.debug("<setSignal><%s, %s>=%s" % (market, signalName, str(signalValue)))
        #self.signals[market][signalName]=signalValue

    #def getSignal(self, market, signalName):
        #try:
            #return self.signals[market][signalName]
        #except KeyError:
            #return None

#sgl=signals()


column_Type_BaseData_Title=[]       #数据库中基本信息列标题
column_Type_Forecast_Title=[]       #数据库中预测信息列标题
column_Type_ExtendData_Title=[]     #数据库中扩展信息列标题


#代理服务器信息
proxies={}
