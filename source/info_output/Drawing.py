# -*- coding: utf-8 -*-

#Python 3.5.x

import numpy as np
import matplotlib.pyplot as plt

__metaclass__ = type

class MyDrawing():
    def __init__(self):
        return
    
    #x:X轴序列
    #yList:Y上的N个序列
    #outfile:非空代表要输出的图片文件名，若为空则代表要显示到屏幕
    #title:整个图的标题
    #xlabel:X轴名称
    #ylabel:Y轴名称
    def drawCurve(self, x, yList, lineName=[], outfile='', title='title', xlabel='x', ylabel='y'):
        assert (len(yList)==len(lineName)) or (len(lineName)==0)
        colorList=['red', 'green', 'blue', 'yellow', 'black', 'cyan', 'magenta']
        assert len(yList)<=len(colorList)   #保证颜色够用
        if len(lineName)==0:
            lineName=["Line %d" % i for i in range(len(yList))]
        z = np.zeros(x.shape[0])
        plt.figure(figsize=(8,4))       #设置画布大小
        ymax=ymin=0.0
        try:
            for i in range(len(yList)):
                plt.plot(x,yList[i],color=colorList[i],label=lineName[i], linewidth=2)
                if i==0:
                    ymax=yList[i].max()
                    ymin=yList[i].min()
                else:
                    ymax=max(ymax, yList[i].max())
                    ymin=min(ymin, yList[i].min())
        except:
            pass
        plt.plot(x,z,"b--") #虚线
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        temp=(ymax-ymin)*0.2
        plt.ylim(ymin-temp,ymax+temp)
        plt.legend(loc=3)
        if not outfile:
            plt.show()
        else:
            plt.savefig(outfile)
        return
