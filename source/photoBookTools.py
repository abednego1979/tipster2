# -*- coding: utf-8 -*-
#Python 2.7.x
#V0.01


#photo book tools

from math import *
import numpy as np
import cv2

def readImage(picName):
    img = cv2.imread(picName,cv2.IMREAD_UNCHANGED)
    return img

def showImage(img, showTime=0):
    cv2.namedWindow("img", cv2.WINDOW_NORMAL)
    cv2.imshow('img',img)
    cv2.waitKey(showTime)
    cv2.destroyAllWindows()
    
def writeImage(picName, img):
    if picName.lower().endswith(".jpg"):
        cv2.imwrite(picName, img, [int( cv2.IMWRITE_JPEG_QUALITY), 95])
    elif picName.lower().endswith(".png"):
        cv2.imwrite(picName, img, [int( cv2.IMWRITE_PNG_COMPRESSION), 9])
    else:
        assert 0,"Output picture name postfix error!"
    return


def revolveImage(img, angle):
    if not angle:
        return img
    else:
        height,width=img.shape[:2]
        #旋转后的尺寸
        heightNew=int(width*fabs(sin(radians(angle)))+height*fabs(cos(radians(angle))))
        widthNew=int(height*fabs(sin(radians(angle)))+width*fabs(cos(radians(angle))))        

        matRotation=cv2.getRotationMatrix2D((width/2,height/2),angle,1)
        
        matRotation[0,2] +=(widthNew-width)/2  #重点在这步，目前不懂为什么加这步
        matRotation[1,2] +=(heightNew-height)/2  #重点在这步
        
        imgRotation=cv2.warpAffine(img,matRotation,(widthNew,heightNew),borderValue=(255,255,255))
        
        return imgRotation

#图像缩放
def zoomImage(img, scale=1.0):
    return cv2.resize(img, (int(img.shape[1]*scale), int(img.shape[0]*scale)), interpolation=cv2.INTER_CUBIC)

#图像锐化
def sharpImage(img, kernel=np.array([[0, -1, 0],[-1, 5, -1],[0, -1, 0]])):
    return cv2.filter2D(img, -1, kernel)

    
def preprocess(gray):  
    # 1. Sobel算子，x方向求梯度  
    sobel = cv2.Sobel(gray, cv2.CV_8U, 1, 0, ksize = 3)  
    # 2. 二值化  
    ret, binary = cv2.threshold(sobel, 0, 255, cv2.THRESH_OTSU+cv2.THRESH_BINARY)  
  
    # 3. 膨胀和腐蚀操作的核函数  
    element1 = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 9))  
    element2 = cv2.getStructuringElement(cv2.MORPH_RECT, (24, 6))  
  
    # 4. 膨胀一次，让轮廓突出  
    dilation = cv2.dilate(binary, element2, iterations = 1)  
  
    # 5. 腐蚀一次，去掉细节，如表格线等。注意这里去掉的是竖直的线  
    erosion = cv2.erode(dilation, element1, iterations = 1)  
  
    # 6. 再次膨胀，让轮廓明显一些  
    dilation2 = cv2.dilate(erosion, element2, iterations = 3)  
  
    # 7. 存储中间图片   
    #cv2.imwrite("binary.png", binary)  
    #cv2.imwrite("dilation.png", dilation)  
    #cv2.imwrite("erosion.png", erosion)  
    #cv2.imwrite("dilation2.png", dilation2)  
  
    return dilation2  


def findTextRegion(img):  
    region = []  
  
    # 1. 查找轮廓  
    binary, contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)  
  
    # 2. 筛选那些面积小的  
    for i in range(len(contours)):  
        cnt = contours[i]  
        # 计算该轮廓的面积  
        area = cv2.contourArea(cnt)   
  
        # 面积小的都筛选掉  
        if(area < 1000):  
            continue  
  
        # 轮廓近似，作用很小  
        epsilon = 0.001 * cv2.arcLength(cnt, True)  
        approx = cv2.approxPolyDP(cnt, epsilon, True)  
  
        # 找到最小的矩形，该矩形可能有方向  
        rect = cv2.minAreaRect(cnt)  
        #print ("rect is: ",rect)  
          
  
        # box是四个点的坐标  
        box = cv2.boxPoints(rect)  
        box = np.int0(box)  
  
        # 计算高和宽  
        height = abs(box[0][1] - box[2][1])  
        width = abs(box[0][0] - box[2][0])  
  
        # 筛选那些太细的矩形，留下扁的  
        if(height > width * 1.2):  
            continue  
  
        region.append(box)  
  
    return region


#识别文本区域
def detect(img):  
    # 1.  转化成灰度图  
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  
  
    # 2. 形态学变换的预处理，得到可以查找矩形的图片  
    dilation = preprocess(gray)  
  
    # 3. 查找和筛选文字区域  
    region = findTextRegion(dilation)  
    
    #找出文字部分的最大范围
    try:
        #x是横向，y是纵向
        min_x=min(region[0][:,0])
        max_x=max(region[0][:,0])
        min_y=min(region[0][:,1])
        max_y=max(region[0][:,1])
        for box in region:
            min_x=min(min(box[:,0]), min_x)
            max_x=max(max(box[:,0]), max_x)
            min_y=min(min(box[:,1]), min_y)
            max_y=max(max(box[:,1]), max_y)
            
        #调正x-y比例为3：4
        max_y = int((max_x-min_x)/3.0)*4+min_y
        
        max_box=np.array([[min_x, max_y], [min_x, min_y], [max_x, min_y], [max_x, max_y]])
        #print ("Max Box:")
        #print (max_box)
        region.append(max_box)
        
        #cv2.drawContours(img, [max_box], 0, (0, 255, 0), 2)
    except:
        pass
    
    # 4. 用绿线画出这些找到的轮廓  
    #for box in region:  
        #cv2.drawContours(img, [box], 0, (0, 255, 0), 2)

    return img, max_box


#blankScale:有字区域向外扩展的白边量的比例
def foo(fileList, blankScale=0.03, outFileProfix="proc_"):    
    for pic in fileList:
        print ("Proc:"+pic)
        img = cv2.imread(pic)  

        res=[]
        for index in range(-5, 6):
            angle=index*0.1
            #print ("angle:"+str(angle))
            rImg=revolveImage(img, angle)
            img_det,max_box = detect(rImg)
            width=max(max_box[:,0])-min(max_box[:,0])
            res.append((width, angle, max_box))
            #showImage(img_det)
            
        
        res = sorted(res, key=lambda x: x[0])
        #print (res)
    
        #print ("Right Angle:"+str(res[0][1]))
        
        #旋转到最佳位置
        rImg=revolveImage(img, res[0][1])
        
        #writeImage('proc_003_temp01.jpg', rImg)
        
        #将max_box扩大一些白边
        max_box=res[0][2]
        width=max(max_box[:,0])-min(max_box[:,0])
        height=max(max_box[:,1])-min(max_box[:,1])
        min_x=min(max_box[:,0])-int(blankScale*width)
        max_x=max(max_box[:,0])+int(blankScale*width)
        min_y=min(max_box[:,1])-int(blankScale*height)
        max_y = int((max_x-min_x)/3.0)*4+min_y
        max_box=np.array([[min_x, max_y], [min_x, min_y], [max_x, min_y], [max_x, max_y]])
        
        cv2.drawContours(rImg, [max_box], 0, (0, 255, 0), 2)
        #writeImage('proc_003_temp02.jpg', rImg)
        
        #取出选好的内容
        new_img = rImg[min_y:max_y, min_x:max_x, :]
        
        #缩放到标准大小
        new_img = zoomImage(new_img, scale=1.0*2048/new_img.shape[0])
        
        #锐化
        new_img = sharpImage(new_img)
        
        #保存
        new_fileName=outFileProfix+pic
        writeImage(new_fileName, new_img)
        
    print ("Proc Over")
    

if __name__ == '__main__':
    fileList=['003.jpg', '004.jpg', '005.jpg']
    foo(fileList)

