# -*- coding: utf-8 -*-

#Python 3.5.x

#V0.01

import numpy as np
import pandas as pd
import os
import config
from database.DB_MySql import MyDB_MySQL

__metaclass__ = type


#这个类将以numpy的array作为对外的数据交换方式
class MyDbEx(MyDB_MySQL):
    db_entry={}

    def __init__(self):
        return
        

    #在设定的目录下创建新的数据库，这个函数用于数据库的首次创建，不应该在程序中多次调用
    def __DbEx_CreateNewDB__(self):
        self.DB_Base_CreateDB(config.db_entry)
        return

    
    def __DbEx_DropDB__(self):
        self.DB_Base_DropDB(config.db_entry)
        return
    
    def __DbEx_CreateTable__(self, tb_name, table_construction, auto_increment=False):
        self.DB_Base_CreateTable(self.__DbEx_TransStockNo2StockName__(tb_name), table_construction, auto_increment)
        return
    
    def __DbEx_GetTable__(self):
        return self.DB_Base_GetTable()
        
        
    def __DbEx_DropTable__(self, tb_name):
        self.DB_Base_DropTable(self.__DbEx_TransStockNo2StockName__(tb_name))
        return
        
        
    def __DbEx_Connect__(self):
        self.DB_Base_Connect(config.db_entry)
        return

    def __DbEx_Commit__(self):
        self.DB_Base_Commit()
        return

    
    def __DbEx_Close__(self):
        self.DB_Base_Close()
        return
    
    def __DbEx_GetTitle__(self):
        all_title=config.db_entry['table_construction']['column']
        return all_title

    
    def __DbEx_TransStockNo2StockName__(self, stockNo):
        temp=stockNo.split('.')
        if len(temp)==2 and (temp[1]=='ss' or temp[1]=='sz'):
            return temp[1]+temp[0]
        else:
            return stockNo
    
    #############################################################
    def DbEx_Connect(self):
        self.__DbEx_Connect__()
        return
    def DbEx_Commit(self):
        self.__DbEx_Commit__()
        return       
    def DbEx_Close(self):
        self.__DbEx_Close__()
        return
    
    def DbEx_GetColumns(self, tb_name):
        #查询所有的列名称

        self.__DbEx_Connect__()
        
        query = self.DB_Base_Create_SqlCmd_SELECT(self.__DbEx_TransStockNo2StockName__(tb_name), '*', '')
        self.db_curs.execute(query)
        names=[f[0] for f in self.db_curs.description]

        self.__DbEx_Close__()
        return names

    #返回的是一个二维array，列数与入参的titleNameList长度一样
    def DbEx_GetDataByTitle(self, tb_name, titleNameList, needSort=1, outDataFormat=None):    #outDataFormat: np.float64 or np.float32
        self.__DbEx_Connect__()
        
        query=self.DB_Base_Create_SqlCmd_SELECT(self.__DbEx_TransStockNo2StockName__(tb_name), ','.join(titleNameList), '')
        res=np.array(self.DB_Base_Query(query), dtype=outDataFormat)
        
        self.__DbEx_Close__()
        
        if needSort:
            if res.ndim==2:
                #需要排序，这里用第一列进行降序排列
                x=res.T.argsort()
                res=np.array([res[x[0].tolist()[::-1][index],:].tolist() for index in range(x.shape[1])], dtype=outDataFormat)
                
        #如果读取回来的数据是空数据，一条数据，则需要对返回的数据进行shape的调整
        if res.ndim==1:
            if res.shape[0]==0:
                #读回的是空数据
                res.shape=(0, len(titleNameList))
            else:
                #读回的只有一条数据
                res.shape=(1, len(titleNameList))
        
        return res
    
    def DbEx_GetRowByTitle_ByDate(self, tb_name, titleNameList, Date, outDataFormat=None):
        self.__DbEx_Connect__()
        
        query=self.DB_Base_Create_SqlCmd_SELECT(self.__DbEx_TransStockNo2StockName__(tb_name), ','.join(titleNameList), 'Date=%s' % str(self.datestr2num(Date)))
        res=np.array(self.DB_Base_Query(query), dtype=outDataFormat)
        
        self.__DbEx_Close__()
        
        return res
    
    def DbEx_InsertItem(self, tb_name, titleNameList, data, needConnect=True, needCommit=True):
        if needConnect:
            self.__DbEx_Connect__()
        
        insert = self.DB_Base_Create_SqlCmd_INSERT(tb_name, titleNameList, data);
        
        self.db_curs.execute(insert)
        
        if needCommit and needConnect:
            self.__DbEx_Commit__()
        if needConnect:
            self.__DbEx_Close__()
        return
    
    def DbEx_UpdateItem(self, tb_name, titleNameList, data, needConnect=True, needCommit=True):
        if needConnect:
            self.__DbEx_Connect__()
        
        for index,item in enumerate(titleNameList):
            if index!=0:
                #以data_array[0]为titleNameList[0]特征，修改titleNameList[index]列为data_array[index]
                para1=data[index]
                if type(para1)==str:
                    para1='"'+para1+'"'                
                para2=data[0]
                if type(para2)==str:
                    para2='"'+para2+'"'
                update=self.DB_Base_Create_SqlCmd_UPDATE(self.__DbEx_TransStockNo2StockName__(tb_name), titleNameList[index]+'=##0', titleNameList[0]+'=##1', para1, para2)
                self.DB_Base_Update(update)
                    
                
        if needCommit:
            self.__DbEx_Commit__()
        if needConnect:
            self.__DbEx_Close__()
        return
    
    def DbEx_GetLastDate(self, stockNo):
        self.__DbEx_Connect__()
        query=self.DB_Base_Create_SqlCmd_SELECT(self.__DbEx_TransStockNo2StockName__(stockNo), 'Date', '')
        res=self.DB_Base_Query(query)              
        self.__DbEx_Close__()
        
        res=[item[0] for item in res]
        
        return max(res)
