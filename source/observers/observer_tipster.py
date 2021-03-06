#*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码


#tensorflow工具的人工智能方式预测

import logging
import json
import traceback
from .observer import Observer
import myGlobal
import config

#这个Observer用于预测股票涨跌
class observer_Tipster(Observer):
    def __init__(self):
        #some my code here
        
        
        super(observer_Tipster, self).__init__()
                
                
    def opportunity(self):
        pass
    
    
    
    
    ####对数据库中的数据计算预测###########################################
    def InitTipsterProc_Task_Core(Tid, calcEngine, stockNo, locks):
        proc_ok_flag=False
        
        initObj=StockDataEngine(calcEngine=calcEngine)
    
        #进行预测
        initObj.tipster_DailyProc(stockNo, locks)
        
                
        proc_ok_flag=True
        
        return proc_ok_flag    
    
    #------------------------------------------------------------------

    
    #每天的预测某个具体股票的函数
    def tipster_DailyProc(self, stockNo, locks):
        assert 0
        #要参考的信息项目
        ColTitleUsed=config.refStockTargetItem.copy()
        
        self.tipster_DailyProc_Model_Softmax(stockNo, ColTitleUsed, locks)
    
    #利用已经得到的基本数据和扩展数据，进行softmax训练
    def tipster_DailyProc_Model_Softmax(self, stockNo, ColTitleUsed, locks):
        
        #从系数数据库中取出W和b
        W_Coefficient, b_Coefficient=self.getRecommondCoefficient(stockNo)
        
        #从股票数据库中取出所需的数据
        #多取的两列，Date是为了排序的需要，PriceIncreaseRate是作为kNN的分类标签
        bData=self.DbEx_GetDataByTitle(dbname, ['Date', 'PriceIncreaseRate']+ColTitleUsed, outDataFormat=np.float32)
        bData=bData[1:,:]   #第一条数据是待预测的值，还没有实际的涨跌幅作为label，所以去除
        
        #如果数据量太少就不训练
        if bData.shape[0]<640:
            return None
        
        labels=bData[:,1]
        y_data=[]
        for i in range(bData.shape[0]-100):
            dBlock=bData[:config.g_data_daylen_of_predict,2:]#把每个数据的最近g_data_daylen_of_predict天的数据作为训练数据
            y_data.append(dBlock.T.reshape((dBlock.size)))
        #512个样本
        labels=labels[:len(y_data)]
        y_data = np.array(y_data)
        
        #trans labels to ont-hot encoding
        labels_temp=[]
        for item in labels:
            if item<=-0.07:
                labels_temp.append([1,0,0,0,0,0,0,0,0])
            elif -0.07<item<=-0.05:
                labels_temp.append([0,1,0,0,0,0,0,0,0])
            elif -0.05<item<=-0.03:
                labels_temp.append([0,0,1,0,0,0,0,0,0])
            elif -0.03<item<=-0.01:
                labels_temp.append([0,0,0,1,0,0,0,0,0])
            elif -0.01<item<0.01:
                labels_temp.append([0,0,0,0,1,0,0,0,0])
            elif 0.01<=item<0.03:
                labels_temp.append([0,0,0,0,0,1,0,0,0])
            elif 0.03<=item<0.05:
                labels_temp.append([0,0,0,0,0,0,1,0,0])
            elif 0.05<=item<0.07:
                labels_temp.append([0,0,0,0,0,0,0,1,0])
            else:
                labels_temp.append([0,0,0,0,0,0,0,0,1])
        labels = labels_temp
        
            
        
        #数据训练
        
        #将训练得到的W和b系数写入系数数据库
        self.setRecommondWeight(stockNo, W_Coefficient, b_Coefficient)
        
        return ColTitleUsed
        


        
    def getRecommondCoefficient(self, stockNo):
        #read last weight from db file
        colName_stockNo='stockNo'
        colName_W='W_array'
        colName_b='b_array'  
        
        self.DbEx_Connect()
        query=self.DB_Base_Create_SqlCmd_SELECT('weight_tb', ','.join([colName_W, colName_b]), colName_stockNo+'="##0"', stockNo)
        res=self.DB_Base_Query(query)
        self.DbEx_Close()

        if not res:
            return dict()
        else:
            assert len(res)==1
            assert 0#need to modify
            temp_dict=json.loads(base64.b64decode(res[0][0]))
            res_dict=dict()
            for key in temp_dict.keys():
                res_dict[str(key)]=temp_dict[key]
            
            return res_dict

        
    def setRecommondWeight(self, stockNo, dict_weight):
        
        colName_stockNo='stockNo'
        colName_weight='weight_array'
        
        #将weight_json(字符串)存入文件
        self.DbEx_Connect()
        query=self.DB_Base_Create_SqlCmd_SELECT('weight_tb', colName_weight, colName_stockNo+'="##0"', stockNo)
        res=self.DB_Base_Query(query)
        self.DbEx_Close()
        if not res:
            #insert
            self.DbEx_InsertItem('weight_tb', [colName_stockNo, colName_weight], [stockNo, base64.b64encode(json.dumps(dict_weight))])
        else:
            #update
            self.DbEx_UpdateItem('weight_tb', [colName_stockNo, colName_weight], [stockNo, base64.b64encode(json.dumps(dict_weight))])

    