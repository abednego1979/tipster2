# -*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

import platform
import base64

cryptoKey=b''

# observers if any
observers = ["observer_Tipster", \
             "observer_PriceFluctuation_TwoStock_DailyClose", \
             "observer_PriceFluctuation_MultiStock_DailyClose",\
             "observer_Tipster_Knn",\
             "observer_Tipster_DecisionTrees",\
             "observer_Tipster_Logistic",\
             ]

realtraders = ['realtrade_Template']

# information source
stock_data_source = 'netease'
yahoo_stock_url = "http://table.finance.yahoo.com/table.csv"
netease_stock_url = "http://quotes.money.163.com/service/chddata.html?code=##STOCKCODE##&fields=TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER;TCAP;MCAP"

#扩展数据的
#均值序列长度
MEAN_LEN_LIST=[3,5,10,12,20,30,26,60]
#DEA_M
DEA_M=9
#KDJ_N
KDJ_N=9
#RSI_DArray
RSI_DArray=[5,10,14,6,12,24]
#BOLL_N
BOLL_N=20
#WR_DArray
WR_DArray = [13,34,89]
#DMI_DArray
DMI_DArray = [7,14]


g_opencl_accelerate=0


# [db_info]
db_type = 'mysql'
# [db_entry_mysql]
db_entry = {'server_ip': 'localhost', \
            'port': 3306, \
            'user': 'zhy', \
            'password': '123456', \
            'db_name': 'tipster_db',}


def encryptInfo(clearText, key=b''):
    assert isinstance(clearText, str)
    from aes import AESCrypto

    if not key:
        passKey=input('input the decrypt key:')
        assert len(passKey)==16 or len(passKey)==24 or len(passKey)==32
        
        if not isinstance(passKey, bytes):
            passKey = passKey.encode()
    else:
        assert isinstance(key, bytes)
        passKey=key
    
    crypto = AESCrypto(passKey, b'0000000000000000')
    ciphertext = crypto.encrypt(clearText)
    return str(base64.b64encode(ciphertext), encoding = "utf-8")


def decryptInfo(cipherText, key=b''):
    assert isinstance(cipherText, str)
    from aes import AESCrypto

    if not key:
        passKey=input('input the decrypt key:')
        assert len(passKey)==16 or len(passKey)==24 or len(passKey)==32
    
        if not isinstance(passKey, bytes):
            passKey = passKey.encode()
    else:
        assert isinstance(key, bytes)
        passKey=key
        
    ciphertext = base64.b64decode(cipherText)
    return AESCrypto(passKey, b'0000000000000000').decrypt(ciphertext)


#proxy相关
config_proxy_en='on'
#How to create enctrypt message:
#config.encryptInfo/config.decryptInfo
#{'user': 'xxxxxxxx', 'password': 'xxxxxxxx', 'ip_http': 'xxxxxxxx', 'ip_https': 'xxxxxxxx'}
config_proxy_info = '+xIGTSdXLxw2mdsilaRypGf6hutl2ucuBdiIYKTedm9cDOSWyDsIP+gZKNDeGPliEwf9R6MQb4eAlXgum4AluNx+fLiGj6mZ6wY5inlOPxS2drnzsEniEAuSn96HgvBDCtRYXpI0opchEapilPNkWZdcGVQjHRL94MavmrmGS2U='
#{'mail_host': 'smtp.qq.com', 'mail_port': 465, 'mail_user': 'xxxxxxxx', 'mail_pass': '授权码,不是密码', 'sender': 'xxxxxxxx@qq.com', 'receivers': 'xxxxxxxx@163.com'}
email_info='TE9fi1aWPoyB4hCjbl/ZfMgeMTv8zV/Hhsdr6+gn200nF+DFkSYIHybZi8vdAqIDO4KmlGXIndCVl9cGc+LCgrW/K+y98JKqlFxV+C9FPKpdRcuUU9/qs8/9vFha1Ok01vNBvhqFPy4Xel2CENEOoqMEDDnf57s+xqxIDW4OgxDePl9sDhwtB5LryO2vySLH1udoCZ1nASM6QyyU/MY/grN4sy+kwkIALdsIOWGBDi0='

#logger日志相关
logger_console='on'
logger_console_level='INFO'
logger_file='on'
logger_file_level='DEBUG'



#下载的数据的各个列的title
downloadItemTitle = ["Date", "Open", "High", "Low", "Close", "Volume", "AdjClose"]

csvDir='dir_download'
tempOutDataDir='dir_temp_data'


g_data_daylen_of_predict = 20



g_threadnum_download=1
g_threadnum_dataproc=1
g_threadnum_predict=1

sysEnterChar=''
if platform.system() == "Windows":
    sysEnterChar='\r\n'
elif platform.system() == "Linux":
    sysEnterChar='\n'
else:#for mac os
    sysEnterChar='\r'
    


stockList={'Bank':[["601398.ss", "工商银行"],["601939.ss", "建设银行"],["601288.ss", "农业银行"],["601988.ss", "中国银行"],["600036.ss", "招商银行"],["600016.ss", "民生银行"],["600000.ss", "浦发银行"],["601328.ss", "交通银行"],["601818.ss", "光大银行"],["601169.ss", "北京银行"],["601998.ss", "中信银行"],["601166.ss", "兴业银行"],["600015.ss", "华夏银行"],["601229.ss", "上海银行"]],\
           'petroleum':[[],[]]\
           }
           
#stockList={'Bank':[["601398.ss", "工商银行"],["600036.ss", "招商银行"]],\
    #'petroleum':[[],[]]\
    #}           

def getNamebyStock(No):
    pass





