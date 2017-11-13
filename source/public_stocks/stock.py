# -*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

import os
import time
import config
import logging
import requests
import sys
import random
from utils import log_exception
import myGlobal

import pandas as pd

from BaseFunc import BaseFunc
from CalcEngine_CPU import *
from database.DB_Ex import MyDbEx

#Stock基类
class Stock(MyDbEx, BaseFunc):
    def __init__(self, stockNo=None):
        self.stockNo = stockNo
        
    def __readDataFromCSV__(self):
        csvFile=os.path.join(config.csvDir, self.stockNo+'.csv')
        
        titleNameList=myGlobal.column_Type_BaseData_Title
        
        if not os.path.isfile(csvFile):
            return titleNameList,[]
        
        #read data from csv file
        df=pd.read_csv(csvFile, encoding='gbk')
        data=df.values.tolist()
        
        if config.stock_data_source=='yahoo':
            pass#data downloaded from yahoo need not to adjust
        elif config.stock_data_source=='netease':
            data = [[self.datestr2num(item[0]), float(item[6]), float(item[4]), float(item[5]), float(item[3]), float(item[11]), float(item[3])] for item in data]
        else:
            assert 0
            
        #剔除停盘日的数据
        data=[item for item in data if item[titleNameList.index('Volume')]>0.0]
        
        return titleNameList,data
    
    def __downloadSockBaseData__(self):
        try:
            if not os.path.exists(config.csvDir):
                os.makedirs(config.csvDir)
        except:
            pass
        
        stockNo=self.stockNo
        
        #构造URL
        if config.stock_data_source == "yahoo":
            urlbase=config.yahoo_stock_url
            fullurl=urlbase+'s='+stockNo.replace('_', '.')
        elif config.stock_data_source == "netease":
            urlbase=config.netease_stock_url
            fullurl=urlbase+'s='+stockNo.replace('_', '.')
            temp_stockNo = stockNo.split('.')
            prefix='1' if temp_stockNo[1]=='sz' else '0'
            fullurl=fullurl.replace('##STOCKCODE##', prefix+temp_stockNo[0])
        else:
            assert 0
        
        #访问该url并保存收到的数据
        try:                
            r = requests.get(fullurl, proxies=myGlobal.proxies)
            
            if not r.ok:
                #删除文件
                print ("Download Fail:")
                print (">>>>>>>>")
                print (r)
                print ("<<<<<<<<")
                return False
                        
            with open(os.path.join(config.csvDir, stockNo+'.csv'), "wb") as pf:
                pf.write(r.content)
            #print 'download OK:'+stockNo
            return True
        except Exception as err:
            print (err)
            #print traceback.format_exc()
            #print 'download Fail:'+stockNo
            return False
        
        pass
    
    def __getSockExtendData__(self, allData):
        allColName=myGlobal.column_Type_BaseData_Title+myGlobal.column_Type_ExtendData_Title
        
        #将数据转换为pandas格式，方便计算，并且根据日期升序排序
        allData=pd.DataFrame(allData, index=allData[:,0].tolist(), columns=allColName).sort_values(by=['Date'])
        
        #涨幅和涨幅率
        #涨跌幅度，D日的涨幅是下一个交易日的收盘价减去D日的收盘价，不要弄错
        l=allData['AdjClose'].shift(-1)-allData['AdjClose']
        l.fillna(0.0,inplace=True)
        lr=l/allData['AdjClose']
        
        allData['PriceIncrease']=l
        allData['PriceIncreaseRate']=lr
        
        
        #计算3,5,10,12,20,30,26,60...日均值和均值率（比价格）
        for mean_len in config.MEAN_LEN_LIST:
            allData['mean_'+str(mean_len)] = allData['AdjClose'].rolling(window=mean_len,center=False).mean()
            allData['mean_'+str(mean_len)+'_RatePrice'] = allData['mean_'+str(mean_len)]/allData['AdjClose']
        
        #---------------------------------------------------------------------------------------
        #DIFF=EMA(12)-EMA(26):两条指数平滑移动平均线的差
        allData['DIFF_12_26'] = allData['AdjClose'].ewm(min_periods=0,span=12,adjust=True,ignore_na=False).mean()-allData['AdjClose'].ewm(min_periods=0,span=26,adjust=True,ignore_na=False).mean()
        allData['DIFF_12_26_Rate'] = allData['DIFF_12_26']/allData['AdjClose']
    
        #---------------------------------------------------------------------------------------
        #DEA:DIFF的M日的平均的指数平滑移动平均线,这里M=9
        M=config.DEA_M
        allData['DEA_'+str(M)] = allData['DIFF_12_26'].rolling(window=M,center=False).mean()
        allData['DEA_'+str(M)+'_Rate'] = allData['DEA_'+str(M)]/allData['AdjClose']
    
        #---------------------------------------------------------------------------------------
        #MACD:DIFF-DEA
        M=config.DEA_M
        allData['MACD'] = allData['DIFF_12_26']-allData['DEA_'+str(M)]
        allData['MACD_Rate'] = allData['MACD']/allData['AdjClose']

        #---------------------------------------------------------------------------------------
        #KDJ，这里取n=9
        N=config.KDJ_N
        M=2
        
        Ln = allData['Low'].rolling(center=False,window=N).min()
        Ln.fillna(value=allData['Low'].expanding(min_periods=1).min(), inplace=True)
        Hn = allData['High'].rolling(center=False,window=N).max()
        Hn.fillna(value=allData['High'].expanding(min_periods=1).max(), inplace=True)
        #RSV=(Cn-Ln)/(Hn-Ln)×100    未成熟随机指标值
        RSV = (allData['AdjClose'] - Ln) / (Hn - Ln) * 100
        
        allData['KDJ_K'] = RSV.ewm(com=M,adjust=True,min_periods=0,ignore_na=False).mean()
        allData['KDJ_D'] = allData['KDJ_K'].ewm(com=M,adjust=True,min_periods=0,ignore_na=False).mean()
        allData['KDJ_J'] = 3 * allData['KDJ_K'] - 2 * allData['KDJ_D']
    
        #---------------------------------------------------------------------------------------
        #RSI相对强弱指标
        #RSI(N)计算方法：当天以前的N天的上涨日的涨幅和作为A，当天以前的N天的下跌日的跌幅幅和作为B（B取绝对值），RSI(N)=A/(A＋B)×100
        for N in config.RSI_DArray:
            PriceIncrease = allData['AdjClose']-allData['AdjClose'].shift(1)
            value1 = PriceIncrease
            value1[value1<0.0]=0.0
            PriceIncrease = allData['AdjClose']-allData['AdjClose'].shift(1)         
            value2 = PriceIncrease
            value2[value2>0.0]=0.0
            plus = value1.rolling(window=N,center=False).sum()
            minus = value2.rolling(window=N,center=False).sum()
            RSI = plus/(plus-minus)*100
            allData['RSI_'+str(N)] = RSI
    
        #---------------------------------------------------------------------------------------
        #BOLL布林线指标
        #中轨线=N日的移动平均线
        #上轨线=中轨线+两倍的标准差
        #下轨线=中轨线－两倍的标准差    
        #MA=N日内的收盘价之和÷N
        N=config.BOLL_N
        
        MA = allData['AdjClose'].rolling(window=N,center=False).mean()  #价格N日均线
        MD = (allData['AdjClose']-MA).pow(2, fill_value=0.0)
        MD = MD.rolling(window=N,center=False).mean()
        MD = MD.pow(0.5, fill_value=0.0)
        MB = MA.shift(-1)-MA
        MB.fillna(0.0,inplace=True)
        
        UP=MB+2*MD
        DN=MB-2*MD
        
        allData['BOLL_MA_'+str(N)] = MA
        allData['BOLL_MA_'+str(N)+'_Rate'] = MA/allData['AdjClose']
        allData['BOLL_UP_'+str(N)] = UP
        allData['BOLL_UP_'+str(N)+'_Rate'] = UP/allData['AdjClose']
        allData['BOLL_DN_'+str(N)] = DN
        allData['BOLL_DN_'+str(N)+'_Rate'] = DN/allData['AdjClose']

        #---------------------------------------------------------------------------------------
        #WR威廉指标--威廉超买超卖指数,主要用于分析市场短期买卖走势
        #计算方法：n日WMS=(Hn－Ct)/(Hn－Ln)×100,Ct为当天的收盘价；Hn和Ln是n日内（包括当天）出现的最高价和最低价
        for N in config.WR_DArray:
            AC = allData['Close']   #收盘价
            Hn = AC.rolling(center=False,window=N).max()    #过去N天的最高价
            Ln = AC.rolling(center=False,window=N).min()    #过去N天的最低价
            WR = 100.0*(Hn-AC)/(Hn-Ln)
            allData['WR_'+str(N)] = WR
        
        #---------------------------------------------------------------------------------------
        #DMI指标--DMI指标又叫动向指标或趋向指标
        #TR:=EXPMEMA(MAX(MAX(HIGH-LOW,ABS(HIGH-ref(CLOSE,1))),ABS(ref(CLOSE,1)-LOW)),N);
        #HD :=HIGH-ref(HIGH,1);
        #LD :=ref(LOW,1)-LOW;
        #DMP:=EXPMEMA(IF(HD>0&&HD>LD,HD,0),N);
        #DMM:=EXPMEMA(IF(LD>0&&LD>HD,LD,0),N);
        #PDI:= DMP*100/TR,COLORFFFFFF;
        #MDI:= DMM*100/TR,COLOR00FFFF;
        #ADX:= EXPMEMA(ABS(MDI-PDI)/(MDI+PDI)*100,M),COLOR0000FF,LINETHICK2;
        #ADXR:=EXPMEMA(ADX,M),COLOR00FF00,LINETHICK2;{本文来源: www.cxh99.com }
        #DYNAINFO(9)>0 AND CROSS(ADX,MDI) AND CROSS(ADXR,MDI) AND PDI>MDI;
        for N in config.DMI_DArray:
            #上升动向（+DM） 
            P_DM = allData['High']-allData['High'].shift(1)
            P_DM[P_DM<0.0]=0.0
            #下降动向（-DM）
            N_DM = allData['Low'].shift(1)-allData['Low']
            N_DM[N_DM<0.0]=0.0
            
            #调整上升动向（+DM）和下降动向（-DM）
            comp1=P_DM<=N_DM
            comp2=P_DM>=N_DM
            P_DM[comp1]=0.0
            N_DM[comp2]=0.0
            P_DM = P_DM.rolling(window=N,center=False).mean()
            N_DM = N_DM.rolling(window=N,center=False).mean()
            
            #计算真实波幅（TR）
            TR1 = allData['High']-allData['Low']
            TR2 = allData['High']-allData['Close'].shift(1)
            TR3 = allData['Low']-allData['Close'].shift(1)
            TR1 = pd.Series(np.where(TR1>TR2, TR1, TR2), index=allData.index.tolist())
            TR = pd.Series(np.where(TR1>TR3, TR1, TR3), index=allData.index.tolist())
            TR = TR.rolling(window=N,center=False).mean()
            
            #计算方向线DI-上升指标
            P_DI = (P_DM / TR)*100.0
            #计算方向线DI-上升指标
            N_DI = (N_DM / TR)*100.0
            
            #计算动向平均数ADX
            DX = P_DI+N_DI
            DX = np.where(DX>0.0, DX, 1.0)
            DX = pd.Series(np.fabs(100.0*(P_DI-N_DI)/DX))
            ADX = DX.rolling(window=N,center=False).mean()
            
            #计算评估数值ADXR
            ADX_NDay = ADX.shift(N)
            ADXR = (ADX+ADX_NDay)*0.5
            
            allData['DMI_PDI_'+str(N)] = P_DI
            allData['DMI_NDI_'+str(N)] = N_DI
            allData['DMI_ADX_'+str(N)] = ADX
            allData['DMI_ADXR_'+str(N)] = ADXR
        #---------------------------------------------------------------------------------------
        #主力买卖
        #EXPMA:指数平均数
        #大盘指数
        #横盘突破
        #振幅
        #委比
        
        allData.fillna(0.0,inplace=True)
        
        return allData.as_matrix()
    
    #从我们主动整理的股票文件列表中获取股票编号列表，600006.ss
    def getSockNoList_File(self, sockListFile):
        df=pd.read_csv(sockListFile, encoding='gbk', header=None)
        lol=df.values.tolist()
        sub_sock_list = ['0'*(6-len(str(item[0])))+str(item[0])+'.'+item[5] for item in lol]
        
        return sub_sock_list
    
    def getSockNoList_Db(self):
        res=self.DbEx_GetDataByTitle('summary_tb', ['itemName', 'itemValue'], needSort=0)
        res_itemName=[item[0] for item in res]
        res_itemValue=[item[1] for item in res]
        res=res_itemValue[res_itemName.index('stockList')]
        return res.split(',')
        
    #获取交易信息
    def Download_StockData(self):
        DownloadFailNum=0
        proc_ok_flag=False
        
        stockNo=self.stockNo

        csvFile=os.path.join(config.csvDir, stockNo+'.csv')
        try:
            os.remove(csvFile)#删除以前下载的csv文件
        except:
            pass
        
        while True:
            #全新下载这个股票的数据
            res=self.__downloadSockBaseData__()
                
            if res:#downoad ok
                myGlobal.logger.info(stockNo+' download OK')
                proc_ok_flag=True
                break
            else:
                myGlobal.logger.info(stockNo+' download data fail')
                DownloadFailNum+=1
                if DownloadFailNum>=3:
                    break
                else:
                    continue
        #返回
        return proc_ok_flag
    
    ####对数据库中的数据计算得到扩展数据###########################################
    #基本处理方式:本函数每次取一次历史数据，然后计算一天的数据，然后插入数据库
    def Process_StockData(self):
        preDays_N=80
        
        sockNo = self.stockNo
        
        time.sleep(random.uniform(1, 3))
        calcEngine = cpu_algorithms_engine()

        allColName=myGlobal.column_Type_BaseData_Title+myGlobal.column_Type_ExtendData_Title
        
        #打开文件，读取所有的数据
        fTitle, fData=self.__readDataFromCSV__()#fData是列表形式
        if len(fData) == 0:
            return True
        
        #fData转换为array，并转换为2维数据
        fData=np.array(fData)
        if fData.ndim==1:
            fData.shape=(1, fData.shape[0])
        
        #对文件中读取的数据，依据日期进行降序排序
        x=fData.T.argsort()
        fData=np.array([fData[x[0].tolist()[::-1][index],:].tolist() for index in range(x.shape[1])])
        
        #将fData补齐到与数据库的列数一样
        fData=self.npColMerge((fData, np.zeros((fData.shape[0],len(allColName)-fData.shape[1]))))
        
        #用fData进行批量的扩展数据计算
        fData=self.__getSockExtendData__(fData)
        
        #由于计算的结果可能出现nan值，这种值后继是不能插入数据库的，所以要对是否存在nan值做检查
        assert not np.isnan(fData).any()
        
        #取出日期信息
        nowDateList=fData[:,0].tolist()
        
        #由于数据库中最后一条记录的涨幅和涨幅率是0.0，所以先更新数据库中最后一条记录的涨幅和涨幅率
        dbRecord = self.DbEx_GetDataByTitle(sockNo, allColName, outDataFormat=np.float32)
        if dbRecord.shape[0]:
            #dbRecord[0][0]这天的数据的涨幅和涨幅率需要更新
            lastDate = dbRecord[0][0]
            lastPriceRaise = fData[nowDateList.index(lastDate),:][allColName.index('PriceIncrease')]
            lastPriceRaiseRate = fData[nowDateList.index(lastDate),:][allColName.index('PriceIncreaseRate')]
            self.DbEx_UpdateItem(sockNo, ['Date', 'PriceIncrease', 'PriceIncrease'], [lastDate, lastPriceRaise, lastPriceRaiseRate], needConnect=True, needCommit=True)
        #取出数据库中已经存在的数据，找出本次计算与数据库中数据相比，多出的那些数据，这些数据需要放入数据库
        if dbRecord.shape[0]:
            nowDateList = [nowDateList.index(item) for item in nowDateList if item>dbRecord[0][0]]        
            fData=fData[nowDateList,:]
        
        if fData.shape[0]:
            self.DbEx_Connect()
            for i in range(fData.shape[0]):
                self.DbEx_InsertItem(sockNo, allColName, fData[i].tolist(), needConnect=False, needCommit=False)
            self.DbEx_Commit()
            self.DbEx_Close()
        
        return True
    


    def buy(self, price, amount):
        pass

    def sell(self, price, amount):
        pass
