# -*- coding: utf-8 -*-

#Python 3.5.x

#V0.01

import numpy as np
import datetime
import traceback
import myGlobal

__metaclass__ = type


class BaseFunc():
    
    def datestr2num(self, datestr):
        l1=datestr.split('-')
        l2=datestr.split('/')
        assert len(l1)==3 or len(l2)==3, datestr
    
        l=l1 if len(l1)==3 else l2
        assert len(l)==3,"Error Date Format"
        
        d1 = datetime.datetime(int(l[0]), int(l[1]), int(l[2]))
        d2 = datetime.datetime(1900, 1, 1)
        
        return (d1-d2).days
    
    def getTodayAsNum(self):
        return (datetime.datetime.today()-datetime.datetime(1900, 1, 1)).days-1
    
    def num2ymd(self, num):
        d1=datetime.datetime(1900, 1, 1)
        d2=d1+datetime.timedelta(days=int(num))
        return d2.year,d2.month,d2.day
    
    def num2datestr(self, num):
        y,m,d=self.num2ymd(num)
        return '%04d-%02d-%02d' % (y,m,d)
    
    def num2weekday(self, num):
        y,m,d=self.num2ymd(num)
        x=datetime.datetime(y,m,d)
        
        return x.weekday()  #0---monday, 6-sunday

    
    #将多个np array数据进行列合并，注意入参可能不是一维数据
    def npColMerge(self, arrayList):
        #允许arrayList中传入空值，这里要将空值去除
        arrayList=list(arrayList)
        arrayList=[item for item in arrayList if hasattr(item, 'tolist')]
        if not arrayList:
            return None
        if len(arrayList)==1:
            return arrayList[0]
        
        arrayList=tuple(arrayList)
        l=0
        rowNum=0
        for index,item in enumerate(arrayList):
            if index==0:
                l=item
                if l.ndim==1:
                    l=l[:,None]#转为列
                elif l.ndim==2:
                    pass
                else:
                    assert 0
                rowNum=l.shape[0]
            else:
                assert rowNum==item.shape[0]
                if item.ndim==1:
                    l=np.hstack((l,item[:,None]))
                elif item.ndim==2:
                    l=np.hstack((l,item))
                else:
                    assert 0
        return l
    
    def npRowMerge(self, arrayList):
        temp_list=list(arrayList)
        temp_list=[item for item in temp_list if not (item.ndim==1 and item.shape[0]==0)]   #去掉空的项
        
        #将数据统一转换为二维
        for index,item in enumerate(temp_list):
            if item.ndim==1:
                temp_list[index].shape=(1, item.shape[0])
        
        #所有的数据做T变换
        temp_list=[item.T for item in temp_list]
        
        #做列合并
        l=self.npColMerge(temp_list)
        
        return l.T
    
    #从列表元素中选择任意selnum个
    def selectElementFromList(self, inList, selnum):
        assert selnum>=1
        
        allRst=[]

        if 1==selnum:
            allRst = [[item] for item in inList]
        else:
            #任意选择多个
            for i in range(len(inList)):
                #先取出第i项，以及后面的项
                cur=inList[i]
                other=inList[i+1:]
                #现在在other中任选（selnum-1）个元素
                if len(other)<(selnum-1):
                    break
                else:
                    resList=self.selectElementFromList(other, selnum-1)
                    allRst += [[cur]+item for item in resList]
        return allRst




