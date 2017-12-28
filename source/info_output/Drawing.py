# -*- coding: utf-8 -*-

#Python 3.5.x

import numpy as np
import matplotlib.pyplot as plt

__metaclass__ = type

class MyDrawing():
    def __init__(self):
        return
    
    def drawCurve(self, x, y, outfile='', title='title', xlabel='xlabel', ylabel='ylabel'):
        z = np.zeros(x.shape[0])
        plt.figure(figsize=(8,4))       #设置画布大小
        plt.plot(x,y,color="red",linewidth=2)
        plt.plot(x,z,"b--") #虚线
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        ymax=y.max()
        ymin=y.min()
        temp=(ymax-ymin)*0.2
        plt.ylim(ymin-temp,ymax+temp)
        plt.legend()
        if not outfile:
            plt.show()
        else:
            plt.savefig(outfile)
        return
