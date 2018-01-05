# -*- coding: utf-8 -*-

#Python 3.5.x

import numpy as np
import matplotlib.pyplot as plt

__metaclass__ = type

class MyDrawing():
    def __init__(self):
        return
    
    def drawCurve(self, x, yList, outfile='', title='title', xlabel='x', ylabel='y'):
        colorList=['red', 'green', 'blue']
        z = np.zeros(x.shape[0])
        plt.figure(figsize=(8,4))       #设置画布大小
        ymax=ymin=0.0
        try:
            for i in range(len(colorList)):
                plt.plot(x,yList[i],color=colorList[i],label='Line %d' % i, linewidth=2)
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
