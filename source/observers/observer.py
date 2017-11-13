#*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

import abc


class Observer(object, metaclass=abc.ABCMeta):    
    #某些准备工作
    def begin_opportunity_finder(self):
        pass

    #opportunity_finder的收尾工作
    def end_opportunity_finder(self):
        pass

    ## abstract
    @abc.abstractmethod
    def opportunity(self):
        pass
