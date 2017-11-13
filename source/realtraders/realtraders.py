#*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

import abc


class Realtrader(object, metaclass=abc.ABCMeta):    
    #某些准备工作
    def begin(self):
        pass

    #收尾工作
    def end(self):
        pass

    ## abstract
    @abc.abstractmethod
    def Exchanger(self):
        pass
