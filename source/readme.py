# -*- coding: utf-8 -*-

#Python 3.5.x

#V0.01

import os

'''
A0:如何切换Python版本
Python提供了一个py.exe的启动器，想运行python2可以执行
py -2 hello.py
想以python3执行可以使用
py -3 hello.py
如果不想用-2/-3参数，可以在python脚本内容最开始位置增加
#! python2
或
#! python3

而对于pip
需要用
py -2 -m pip install XXXX
或
py -3 -m pip install XXXX


A1:about pip tools
当python2和python3同时安装在PC上时，pip命令可能会受到干扰，这时可以使用指定的pip2或pip3来执行pip

当网络有代理时，pip的命令为：
pip2 install --proxy=http://<user>:<password>@<host/ip>:<port> --trusted-host <pypi.python.org/other> <the packet to install>
如：
pip2 install --proxy=http://xxxxxxxx:<password>@xxxx.xxxx.com:8080 --trusted-host pypi.python.org numpy

A2:install pythoncl
pythoncl二进制安装方式，可以从这里下载安装包：
http://www.lfd.uci.edu/~gohlke/pythonlibs/
不过注意既然是二进制包，难免有各种问题，我历史上用过的好用的两个包，目前已经在网站上没有了。
可以到我的百度网盘的opencl目录找
pyopencl-2016.1-cp27-cp27m-win_amd64.whl
和
pyopencl-2016.1-cp27-cp27m-win32.whl
使用

查看pyopencl的各种帮助
>>> import pyopencl as cl
>>> help(cl)
>>> dir(cl)

A3:OpenCl and Remote Desktop conflict
远程桌面（mstsc）通常会关闭硬件加速，所以远程桌面中运行opencl程序会找不到GPU提供的加速设备
这时可以考虑用VNC方式远程访问

A4:OpenCL中什么时候需要使用工作组的概念？
当处理的数据需要多次的访问统一个区域，这时就需要考虑将数据从刚传入时存放在全局区域先转移到局部存储区域。这样后继的
数据在局部存储区操作。
比如长向量的元素加和，算法是第i个元素与第i+N/2个元素相加，然后不断的重复。这是预先将全局数据转移到局部变量就很有意义，可以大大降低访问延时。
由于一个处理单元的局部存储空间有限，所以有时不能将全部的数据转移到一个处理单元的局部空间，这时需要适当的将全局数据分为多个部分，每个部分可以被复制到一个处理单元的局部空间。
每个处理单元同时处理的工作项的集合就是一个工作组。在工作组内部，索引从0开始计算，就是local_id

而如果待处理的数据在整个kernel计算期间只访问一次，就没有必要转移到局部变量中了。
比如两个矩阵相加，A矩阵的某个元素读取一次，B矩阵对应位置的元素读取一次，相加以后，放入S矩阵的对应位置。所有的数据只访问一次


A5:numpy的二维数组映射到kernel中是怎样的？
import numpy as np
[In]    x=np.array([[1,2,3],[4,5,6]])
[In]    x
[Out]   array([[1, 2, 3],
               [4, 5, 6]])
[In]    x.shape
[Out]   (2, 3)
[In]    x.reshape(6)
[Out]   array([1, 2, 3, 4, 5, 6])

numpy的二维数组在视作一维数组时，是逐行重排的，这与C语言的二维数组是一样的。
在OpenCL中，
gid0=get_global_id(0)
gid1=get_global_id(1)
在gid1==0时，gid0=0,1,2,...对应的是数组的第一行，也就是reshape后一维数组的前N个数据
在gid1==1时，gid0=0,1,2,...对应的是数组的第二行，也就是reshape后一维数组的第二个N个数据


A6:OpenCL的各种维度信息获取
假设下面的二维数据
+--+--+--+--+--+--+--+--+--+--+
| 1| 2| 3| 4| 5| 6| 7| 8| 9|10|
+--+--+--+--+--+--+--+--+--+--+
|11|12|13|14|15|16|17|18|19|20|
+--+--+--+--+--+--+--+--+--+--+
|21|22|23|24|25|26|27|28|29|30|
+--+--+--+--+--+--+--+--+--+--+
|31|32|33|34|35|36|37|38|39|40|
+--+--+--+--+--+--+--+--+--+--+
|41|42|43|44|45|46|47|48|49|50|
+--+--+--+--+--+--+--+--+--+--+
|51|52|53|54|55|56|57|58|59|60|
+--+--+--+--+--+--+--+--+--+--+
|61|62|63|64|65|66|67|68|69|70|
+--+--+--+--+--+--+--+--+--+--+
|71|72|73|74|75|76|77|78|79|80|
+--+--+--+--+--+--+--+--+--+--+
|81|82|83|84|85|86|87|88|89|90|
+--+--+--+--+--+--+--+--+--+--+
|91|92|93|94|95|96|97|98|99|1h|
+--+--+--+--+--+--+--+--+--+--+
如果入参为：
size_t global_offset[]={3,5};
size_t global_size[]={6,4};
size_t local_size[]={3,2};
则36是第一个数据，最后一个数据是89

则在kernel中：
get_work_dim() == 2
get_global_id(0) == 相对于36的纵向偏移值
get_global_id(1) == 相对于36的横向偏移值
get_global_size(0) == 6
get_global_size(1) == 4
get_global_offset(0) == 3
get_global_offset(1) == 5

get_num_groups(0) == 2 (=6/3)
get_num_groups(1) == 2 (=4/2)
get_group_id(0) == 所属group的id（维度0），36-39,46-49,56-59为0, 66-69,76-79,86-89为1
get_group_id(1) == 所属group的id（维度1），x6-x7(x=3-8)为0, x8-x9(x=3-8)为1

get_local_id(0) == 在所属组里的id，如36，38，66，68的id(0)都是0，46，48，46，48都是1
get_local_id(1) == 在所属组里的id，如36，38，66，68的id(0)都是0，37，39，67，69都是1
get_local_size(0) == 组的维度0上的大小
get_local_size(1) == 组的维度1上的大小


假设下面的一维数据
raw dataSet: [7 1 3 2 4 1 8 1 9 3 3 6]
数据划分是
global_size: (12,)
local_size: (4,)
那么
get_global_id(0) == 数据在全部数据中的id，如最后一个数字6的id是11
get_global_size(0) == 12 == dataSet.shape
get_global_offset(0) == 0,由于我们使用了全部的数据，所以偏移值一般是0
get_num_groups(0) == 3 == 12/4
get_group_id(0) == 元素所在组的组id，[7 1 3 2]的gid是0，[4 1 8 1]的gid是1，[9 3 3 6]的gid是2
get_local_id(0) == 元素在所属组之内的id，如[7 4 9]的lid是0, 如[1 1 3]的lid是1, 如[3 8 3]的lid是2, 如[2 1 6]的lid是3
get_local_size(0) == 4， 所属组的组大小


A7:Matplotlib模块在Windows下安装

由于最新的python2.7已经集成了pip，所以只要用pip去安装大部分的包就可以了
1.在安全之前先更新一下pip：python -m pip install --upgrade pip      (如果需要代理，请参考上面的问题)
2.到官网下载Matplotlib的windows安装包（.exe）直接安装
3.安装numpy
4.pip2安装dateutil, pyparsing, scipy, six，有些包不能用pip安装，需要下载whl再安装，而scipy更是需要在"http://www.lfd.uci.edu/~gohlke/pythonlibs/"下载预编译好的whl包安装
5.over and test it:
Code:
--------
# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt

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
--------


A8:Raspberry Pi树莓派上支持GPGPU编程
https://toutiao.io/posts/ekssmd/preview


A9:树莓派安装以后，更新源

源信息在/etc/apt/sources.list，修改之前先备份
sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak
然后编辑
sudo nano /etc/apt/sources.list
将原有的源用#注释掉

然后加入新的源（有效的源可以在这里找到：http://www.raspbian.org/RaspbianMirrors，请选择国内的源）
如
deb http://mirrors.zju.edu.cn/raspbian/raspbian/ jessie main contrib non-free rpi
deb-src http://mirrors.zju.edu.cn/raspbian/raspbian/ jessie main contrib non-free rpi
保存文件以后，就可以更新数据了。
不过最好先确定这些源是网络可达的：
ping 源的ip或域名
ping mirrors.zju.edu.cn

最后更新数据：
sudo apt-get update
sudo apt-get upgrade -y

A10:树莓派开启SSH和RDP
SSH开启需要在sudo raspi-config中开启
RDP需要sudo apt-get install xrdp，sudo apt-get install vnc4server tightvncserver


A11:在树莓派中安装python-opencv



A12:利用pandas和sqlite3快速将excel数据导入sqlite数据库
import sqlite3
import pandas
x=pandas.read_excel('test.xlsx')
conn=sqlite3.connect('dbname.sqlite')
x.to_sql('tablename', conn)
...data proc...
conn.close()







'''