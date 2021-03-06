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
config_proxy_en=''
#How to create enctrypt message:
#config.encryptInfo/config.decryptInfo
#the encryption information is in conf file

#{'user': 'xxxxxxxx', 'password': 'xxxxxxxx', 'ip_http': 'xxxxxxxx', 'ip_https': 'xxxxxxxx'}
config_proxy_info=''
#{'mail_host': 'smtp.qq.com', 'mail_port': 465, 'mail_user': 'xxxxxxxx', 'mail_pass': '授权码,不是密码', 'sender': 'xxxxxxxx@qq.com', 'receivers': 'xxxxxxxx@163.com'}
#{}['receivers']用,分割
email_info=''


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
    


stockList={\
    'Bank':[["601398.ss", "工商银行"],["601939.ss", "建设银行"],["601288.ss", "农业银行"],["601988.ss", "中国银行"],["600036.ss", "招商银行"],["600016.ss", "民生银行"],["600000.ss", "浦发银行"],["601328.ss", "交通银行"],["601818.ss", "光大银行"],["601169.ss", "北京银行"],["601998.ss", "中信银行"],["601166.ss", "兴业银行"],["600015.ss", "华夏银行"],["601229.ss", "上海银行"]],\
    'Petroleum':[["601857.ss", "中国石油"],["600028.ss", "中国石化"],["601808.ss", "中海油服"]]\
           }

#各种预测方法说参考的指标
refStockTargetItem=[\
    'Volume', \
    'mean_3_RatePrice', \
    'mean_5_RatePrice', \
    'mean_10_RatePrice', \
    'mean_20_RatePrice', \
    'mean_30_RatePrice', \
    'DIFF_12_26_Rate', \
    'DEA_9_Rate', \
    'MACD_Rate', \
    'RSI_5', \
    'RSI_14', \
    'WR_13', \
    'WR_34', \
]
#KDJ_K,KDJ_D和KDJ_J指标之间比较才有意义，所以还要在衍生一些指标后才纳入计算参考
#BOLL_MA,BOLL_UP和BOLL_DN指标之间比较才有意义，所以还要在衍生一些指标后才纳入计算参考
#DMI-xxx指标之间比较才有意义，所以还要在衍生一些指标后才纳入计算参考

def getNamebyStock_configfile(No):
    temp_stockList=[]
    temp_stockName=[]
    for kType in stockList.keys():
        temp_stockList+=[item[0] for item in stockList[kType]]
        temp_stockName+=[item[1] for item in stockList[kType]]

    try:
        return temp_stockName[temp_stockList.index(No)]
    except:
        return "Unknow_Stock_Name.ss"

def getStockNoList_configfile():
    res=[]
    for kType in stockList.keys():
        res+=[item[0] for item in stockList[kType]]
        
    return res





