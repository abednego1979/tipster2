# -*- coding: utf-8 -*-

#Python 3.5.x

#V0.01

import os
import re
import json
import datetime
import base64
import time
import multiprocessing
import random
import traceback
import numpy as np
import configparser

import myGlobal
from CalcEngine_CPU import *
from version import Version
from info_output.sendMail import MySendMail

import argparse
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, wait

import time
import config
import logging
import logging.handlers
import sys
from utils import log_exception
import myGlobal
from BaseFunc import BaseFunc
from public_stocks.stock import Stock

#初始化全局变量
#这些全局变量统一被定义在一个模块中
#
def initGlobalValue():     
    
    #每个stock会建立一个table,每个table的表项是一样的，如下
    myGlobal.column_Type_BaseData_Title=config.downloadItemTitle
    column_Type_BaseData_DataType=["CHAR(10)"]+["FLOAT"]*(len(myGlobal.column_Type_BaseData_Title)-1)
        
    myGlobal.column_Type_Forecast_Title=["Forecast_Increase", "Forecast_Accuracy"]
    column_Type_Forecast_DataType=["FLOAT"]*len(myGlobal.column_Type_Forecast_Title)
    
    
    myGlobal.column_Type_ExtendData_Title=["PriceIncrease", "PriceIncreaseRate"]
    for meanLen in config.MEAN_LEN_LIST:
        myGlobal.column_Type_ExtendData_Title+=['mean_'+str(meanLen), 'mean_'+str(meanLen)+'_RatePrice']
    myGlobal.column_Type_ExtendData_Title+=["DIFF_12_26", "DIFF_12_26_Rate"]
    myGlobal.column_Type_ExtendData_Title+=["DEA_"+str(config.DEA_M), "DEA_"+str(config.DEA_M)+"_Rate"]
    myGlobal.column_Type_ExtendData_Title+=["MACD", "MACD_Rate"]
    myGlobal.column_Type_ExtendData_Title+=["KDJ_K", "KDJ_D", "KDJ_J"]
    for item in config.RSI_DArray:
        myGlobal.column_Type_ExtendData_Title+=["RSI_"+str(item)]
    myGlobal.column_Type_ExtendData_Title+=["BOLL_MA_20", "BOLL_MA_20_Rate", "BOLL_UP_20", "BOLL_UP_20_Rate", "BOLL_DN_20", "BOLL_DN_20_Rate"]
    for item in config.WR_DArray:
        myGlobal.column_Type_ExtendData_Title+=["WR_"+str(item)]
    for item in config.DMI_DArray:
        myGlobal.column_Type_ExtendData_Title+=["DMI_PDI_"+str(item)]
        myGlobal.column_Type_ExtendData_Title+=["DMI_NDI_"+str(item)]
        myGlobal.column_Type_ExtendData_Title+=["DMI_ADX_"+str(item)]
        myGlobal.column_Type_ExtendData_Title+=["DMI_ADXR_"+str(item)]
        
    column_Type_ExtendData_DataType=["FLOAT"]*len(myGlobal.column_Type_ExtendData_Title)

    config.db_entry['table_construction']={'column': myGlobal.column_Type_BaseData_Title+myGlobal.column_Type_Forecast_Title+myGlobal.column_Type_ExtendData_Title, \
                                         'dataType':column_Type_BaseData_DataType+column_Type_Forecast_DataType+column_Type_ExtendData_DataType}
    config.db_entry['main_key']=myGlobal.column_Type_BaseData_Title[0]



class Arbitrer(object):
    def __init__(self):
        self.stocks = []        #数据收集者
        self.observers = []         #数据观察者
        self.realtraders = []       #真实交易者
        
        db_handle=Stock()
        #初始化数据收集者
        self.init_stocks(db_handle.getStockNoList_Db())
        self.init_observers(config.observers)       
        self.init_realtraders(config.realtraders)
        
        #初始化一个线程池，其他的还都没有做
        self.threadpool = ThreadPoolExecutor(max_workers=10)        

    def init_stocks(self, stocks):
        self.stocks_names = stocks
        exec('import public_stocks.stock')
        for stock_name in stocks:
            try:
                newStock=eval('public_stocks.stock.Stock("%s")' % (stock_name))
                self.stocks.append(newStock)
            except (AttributeError) as e:
                print("%s stck name is invalid: Ignored (you should check your config file)" % (stock_name))
                
    def init_observers(self, _observers):
        self.observer_names = _observers
        for observer_name in _observers:
            try:
                exec('import observers.' + observer_name.lower())
                observer = eval('observers.' + observer_name.lower() + '.' + observer_name + '()')
                self.observers.append(observer)
            except (ImportError, AttributeError) as e:
                print("%s observer name is invalid: Ignored (you should check your config file)" % (observer_name))
                
    def init_realtraders(self, _realtraders):
        self.realtraders_names = _realtraders
        for realtrader_name in _realtraders:
            try:
                exec('import realtraders.' + realtrader_name.lower())
                realtrader = eval('realtraders.' + realtrader_name.lower() + '.' + realtrader_name + '()')
                self.realtraders.append(realtrader)
            except (ImportError, AttributeError) as e:
                print("%s realtrader name is invalid: Ignored (you should check your config file)" % (realtrader_name))    
    
    def __get_stock_tradeinfo(self, paras):
        stock=paras["stock"]
        #获得数据并存入数据库,并计算扩展数据
        print('Download Data(%s)' %(stock.stockNo))
        res=stock.Download_StockData()
        print('Proc :'+('OK' if res else 'Fail'))
        print('Proc Data')
        res=stock.Process_StockData()
        print('Proc :'+('OK' if res else 'Fail'))
        
        pass
    
    def run_stocks(self):
        if False:
            futures = []
            for stock in self.stocks:
                futures.append(self.threadpool.submit(self.__get_stock_tradeinfo, {"stock":stock}))
            wait(futures)
        else:
            for stock in self.stocks:
                time.sleep(3)
                self.__get_stock_tradeinfo({"stock":stock})
        return
            
    def run_observers(self):
        for observer in self.observers:
            observer.begin_opportunity_finder()
            
        #在不同的市场中查找机会
        for observer in self.observers:
            try:
                observer.opportunity()
            except Exception as err:
                print (err)
                print(traceback.format_exc())
                myGlobal.logger.error(err)
            pass

        for observer in self.observers:
            observer.end_opportunity_finder()

    def run_realtraders(self):
        for realtrader in self.realtraders:
            realtrader.begin()
            
        for realtrader in self.realtraders:
            realtrader.Exchanger()
            pass

        for realtrader in self.realtraders:
            realtrader.end()    

    def loop(self):
        lastRunDay=""
        while True:
            curDay=datetime.datetime.today().strftime("%Y-%m-%d")
            if lastRunDay==curDay:
                time.sleep(600)
                continue
            else:
                lastRunDay=curDay
                
            myGlobal.logger.info("tick@%s" % (datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")))

            #初始一个文件,用于临时存放要发送的mail正文
            try:
                with open('MailOutInfo.txt', 'w') as pf:
                    pf.write('Mail:\r\n')
            except:
                pass
            myGlobal.attachMailFileList=[]
            
            #获取时间，如果是某个时刻，就开始运行下面的代码
            try:
                self.run_stocks()
                self.run_observers()    #这里整理信息
                self.run_realtraders()    #这里真实交易
                #time.sleep(config.refresh_rate)
            except:
                pass
            
            #发送邮件
            if myGlobal.userChooseProxySet != 'on':
                try:
                    with open('MailOutInfo.txt', 'r') as pf:
                        lines=pf.read()
                        #print (">>>>>>>>>"+lines)
                        MySendMail().sendRes_ByMail(lines, myGlobal.attachMailFileList)
                except:
                    pass
            
            try:
                #删除MailOutInfo.txt文件
                #os.remove('MailOutInfo.txt')
                pass
            except:
                pass
            
            break


class ArbitrerCLI:
    def __init__(self):
        pass
    def exec_command(self, args):
        initGlobalValue()
        if args.reset:
            #复位系统，重新初始化数据库等
            a=input('####%%%%    Are you want to re-build the DataBase???(Type "yes" to continue)')
            if a.lower() != 'yes':
                exit()
            
            init_handle=Stock('000001.ss')
            
            print('drop database...')
            init_handle.__DbEx_DropDB__()
            
            print('create database...')
            init_handle.__DbEx_CreateNewDB__()
            
            print('get stock no list from CSV file...')
            stock_list = init_handle.getStockNoList_File(os.path.join('dir_baseData', 'stockList.csv'))         
            print('find '+str(len(stock_list))+' stocks.')
            
            print('create table for each stock...')
            init_handle.DbEx_Connect()
            for stockNo in stock_list:
                init_handle.__DbEx_CreateTable__(stockNo, config.db_entry['table_construction'])
            init_handle.DbEx_Commit()
            init_handle.DbEx_Close()
            print('Create Tables OK')
            
            print('create table for weight...')
            init_handle.DbEx_Connect()
            init_handle.__DbEx_CreateTable__('weight_tb', {'column': ['stockNo', 'W_array', 'b_array'], 'dataType': ['CHAR(9)', 'TEXT', 'TEXT']})
            init_handle.DbEx_Commit()
            init_handle.DbEx_Close()
            print('create ok')
            
            print('create table for Summary information, like stock list, tradeDate list...')
            init_handle.DbEx_Connect()
            init_handle.__DbEx_CreateTable__('summary_tb', {'column': ['itemName', 'itemValue'], 'dataType': ['CHAR(32)', 'LONGTEXT']})
            init_handle.DbEx_Commit()
            init_handle.DbEx_Close()
            
            print('import stock list into summary_tb...')
            init_handle.DbEx_InsertItem('summary_tb', ['itemName', 'itemValue'], ['stockList', ','.join(stock_list)])
            init_handle.DbEx_InsertItem('summary_tb', ['itemName', 'itemValue'], ['tradeDates', ''])
            
            
            print('Now the follow tables are create in DB:')
            init_handle.DbEx_Connect()
            db_tables = init_handle.__DbEx_GetTable__()
            init_handle.DbEx_Close()
            db_tables = [str(item[0]) for item in db_tables]
            db_tables_type_ss=[item for item in db_tables if re.match(r'''ss[0-9]{6}''', item)]
            db_tables_type_sz=[item for item in db_tables if re.match(r'''sz[0-9]{6}''', item)]
            db_tables_type_common=[item for item in db_tables if item not in db_tables_type_ss and item not in db_tables_type_sz]
            print('--------')
            print(str(len(db_tables_type_ss))+' ss stocks')
            print(str(len(db_tables_type_sz))+' sz stocks')
            print('Other databse: '+','.join(db_tables_type_common))
            
            for table_name in db_tables_type_common:
                #显示数据库中的所有数据项名称
                names=init_handle.DbEx_GetColumns(table_name)
                print('--------')
                print('Cols of '+table_name+' is:')
                print(','.join(names))
            if (len(db_tables_type_ss)+len(db_tables_type_sz)) >0:
                temp_list=db_tables_type_sz+db_tables_type_ss
                names=init_handle.DbEx_GetColumns(temp_list[0])
                print('--------')
                print('Cols of common stock db is:')
                print(','.join(names))
            
            print('####&&&&to be finished####&&&&')
            
        else:
            db_handle=Stock()
            stock_list_1 = db_handle.getStockNoList_File(os.path.join('dir_baseData', 'stockList.csv'))
            stock_list_2 = db_handle.getStockNoList_Db()
            a=[item for item in stock_list_1 if item not in stock_list_2]
            b=[item for item in stock_list_2 if item not in stock_list_1]
            if a or b:
                print ("The stock list is different between file and database, Please run commond with '--reset'.")
            else:
                #代理设置初始化
                
                
                
                myGlobal.userChooseProxySet=config.config_proxy_en
                if config.config_proxy_en=='on':
                    proxyChoose=input('The PROXY is on, Right?(Y/n)')
                    if proxyChoose=='N' or proxyChoose=='n':
                        myGlobal.userChooseProxySet='off'
                
                if myGlobal.userChooseProxySet=='on':
                    #代理信息加密存储，这里先要解密
                    temp_config_proxy = json.loads(config.decryptInfo(config.config_proxy_info, config.cryptoKey))
                    
                    a=temp_config_proxy['user']
                    b=temp_config_proxy['password']
                    if temp_config_proxy['ip_http']:
                        myGlobal.proxies['http']="http://"+a+":"+b+"@"+temp_config_proxy['ip_http']
                    if temp_config_proxy['ip_https']:
                        myGlobal.proxies['https']="http://"+a+":"+b+"@"+temp_config_proxy['ip_https']               

                self.create_arbitrer()
                self.arbitrer.loop()

    def create_arbitrer(self):
        self.arbitrer = Arbitrer()

    def init_logger(self):        
        # 定义日志输出格式
        formatString='%(asctime)s [%(levelname)s] %(message)s'
        
        # 初始化
        logging.basicConfig()
        
        #创建日志对象并设置级别
        myGlobal.logger = logging.getLogger('baselogger')
        myGlobal.logger.setLevel(logging.DEBUG)
        myGlobal.logger.propagate = False
        
        if config.logger_console=='on':
            #######################################
            #创建一个日志输出处理对象
            hdr = logging.StreamHandler()
            hdr.setLevel(config.logger_console_level)
            hdr.setFormatter(logging.Formatter(formatString))
            #######################################
            myGlobal.logger.addHandler(hdr)
        
        if config.logger_file=='on':
            #######################################
            #创建一个日志文件输出处理对象
            fileshandle = logging.handlers.TimedRotatingFileHandler('procLog_', when='H', interval=2, backupCount=0)
            # 设置日志文件后缀，以当前时间作为日志文件后缀名。
            fileshandle.suffix = "%Y%m%d_%H%M%S.log"
            fileshandle.extMatch = re.compile(r"^\d{4}\d{2}\d{2}_\d{2}\d{2}\d{2}.log$")
            # 设置日志输出级别和格式
            fileshandle.setLevel(config.logger_file_level)
            fileshandle.setFormatter(logging.Formatter(formatString))
            #######################################
            myGlobal.logger.addHandler(fileshandle)

        pass
    

    def main(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-r", "--reset", help="Reset the system, clear all the history data", action="store_true")
        #parser.add_argument("command", nargs='*', default="watch", help='verb: "watch|replay-history|get-balance|list-public-markets"')
        args = parser.parse_args()
        self.init_logger()
        self.exec_command(args)
        

def main():
    
    v=Version()
    print('Tipster(TensorFlow) '+v.getVersionString())
    
    #input('这里写还未实现的功能，以后一一实现')
    
    passKey=input('input the crypt key for config file:')
    assert len(passKey)==16 or len(passKey)==24 or len(passKey)==32
    if not isinstance(passKey, bytes):
        passKey = passKey.encode()
    config.cryptoKey = passKey
    

    #检查是否存在mysql数据库，如果不存在就创建一个
    #数据库的基本数据格式有时间戳（id），marcket（同一个交易所的不同币种认为是不同市场），datatype（深度，交易等），data（json格式）
    #assert 0
    
    cli = ArbitrerCLI()
    cli.main()

if __name__ == "__main__":
    print ("Start ...")
    main()