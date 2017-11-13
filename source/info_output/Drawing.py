# -*- coding: utf-8 -*-

#Python 3.5.x

import numpy as np
import matplotlib.pyplot as plt

__metaclass__ = type

class MyDrawing():
    def __init__(self):
        return
    
    def example(self):
        x = np.linspace(0, 10, 1000)
        y = np.sin(x)
        z = np.cos(x**2)
        
        plt.figure(figsize=(8,4))
        plt.plot(x,y,label="$sin(x)$",color="red",linewidth=2)
        plt.plot(x,z,"b--",label="$cos(x^2)$")
        plt.xlabel("Time(s)")
        plt.ylabel("Volt")
        plt.title("PyPlot First Example")
        plt.ylim(-1.2,1.2)
        plt.legend()
        plt.show()        
        return









