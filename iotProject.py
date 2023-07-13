#EEES 406-Data Analytics for IoT Project

import cv2
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
in1 = 16
in2 = 18
en = 22
led1=11
led2=13
led3=15

GPIO.setup(in1,GPIO.OUT)
GPIO.setup(in2,GPIO.OUT)
GPIO.setup(en,GPIO.OUT)
GPIO.setup(led1,GPIO.OUT)
GPIO.setup(led2,GPIO.OUT)
GPIO.setup(led3,GPIO.OUT)

GPIO.output(in1,GPIO.HIGH)
GPIO.output(in2,GPIO.LOW)
GPIO.output(led1,GPIO.LOW)
GPIO.output(led2,GPIO.LOW)
GPIO.output(led3,GPIO.LOW)

p=GPIO.PWM(en,100)
p.start(25)

count_in,count_out=0,0
condition_in,condition_out=False,False
W = 500
H = 500
total=[]

capture = cv2.VideoCapture("example6.mp4")

if not capture.isOpened():
    print("Connection failed!")
    exit()

while(1):
    try:
        ret, frame1 = capture.read()
        frame = cv2.resize(frame1,(W, H))
    except:
        print("The end of the Video")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.blur(gray, (3, 3))
    ret, thresh = cv2.threshold(blur, 70, 255, cv2.THRESH_BINARY_INV)
    erosion=cv2.erode(thresh,None,iterations=3)  
    _,contours,_ = cv2.findContours(erosion, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    cv2.putText(frame, "Counter IN: " + str(count_in), (10, 20), cv2.FONT_ITALIC, 1, (0, 0, 255), 1)
    cv2.putText(frame, "Counter OUT: " + str(count_out), (10, 50), cv2.FONT_ITALIC, 1, (255, 0, 0), 1)
  
    cv2.line(frame, (0,50), (500, 50), (0, 0, 255), 2)
    cv2.line(frame, (0, 450), (500, 450), (0, 0, 255), 2)
    cv2.line(frame, (0, 100), (500, 100), (255, 0, 0), 2)
    cv2.line(frame, (0, 400), (500, 400), (255, 0, 0), 2)    
        
    for contour in contours:
        (x,y,w,h) = cv2.boundingRect(contour)
        area=cv2.contourArea(contour)

        if area>1100:
            mts = cv2.moments(contour)
            cX,cY = int(mts['m10']/mts['m00']),int(mts['m01']/mts['m00'])
                       
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.circle(frame,center=(cX,cY),radius=5,color=(0,0,255),thickness=-1)

            if cY>50 and cY<100:
                condition_out=True

            if cY>400 and cY<450:
                condition_in=True

            if condition_out==1 and cY>100 and cY<120 :
                count_out=count_out+1
                condition_out=False
                total.append(count_in-count_out)
            if cY>450:
               condition_in=False

            if condition_in==1 and cY<400 and cY>380:
                count_in=count_in+1
                condition_in=False
                total.append(count_in-count_out)
            if cY<50:
               condition_out=False


            if (count_in-count_out)>=0 and (count_in-count_out)<=1:
                GPIO.output(led1,GPIO.HIGH)
                GPIO.output(led2,GPIO.LOW)
                GPIO.output(led3,GPIO.LOW)
                p.ChangeDutyCycle(50)

            elif (count_in-count_out)>1 and (count_in-count_out)<=3:
                GPIO.output(led1,GPIO.HIGH)
                GPIO.output(led2,GPIO.HIGH)
                GPIO.output(led3,GPIO.LOW)
                p.ChangeDutyCycle(75)

            elif (count_in-count_out)>3:
                GPIO.output(led1,GPIO.HIGH)
                GPIO.output(led2,GPIO.HIGH)
                GPIO.output(led3,GPIO.HIGH)
                p.ChangeDutyCycle(100)
        
    cv2.imshow('frame',frame)

    k = cv2.waitKey(1) & 0xff
    if k == 27:
        break

GPIO.output(led1,GPIO.LOW)
GPIO.output(led2,GPIO.LOW)
GPIO.output(led3,GPIO.LOW)
p.stop()
GPIO.cleanup()

#This is the part to find contours ​​via the camera module
##from picamera.array import PiRGBArray
##from picamera import PiCamera
##import time
##import cv2
##camera = PiCamera()
##camera.resolution = (500, 500)
##camera.framerate = 32
##capture = PiRGBArray(camera, size=(500, 500))
##time.sleep(0.1)
##
##for f in camera.capture_continuous(capture, format="bgr", use_video_port=True):
##    frame = f.array
##    capture.truncate(0)
##    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
##    blur = cv2.blur(gray, (3, 3)) 
##    ret, thresh = cv2.threshold(blur, 70, 255, cv2.THRESH_BINARY_INV)
##    erosion=cv2.erode(thresh,None,iterations=3)  
##    _,contours,_ = cv2.findContours(erosion, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    



#Cloud Part
import urllib.request
from time import sleep
import re
import json
import csv
import pandas as pd

h=0
result=[]
baseURL='https://api.thingspeak.com/update?api_key=KE6HWBL7O0SDWG91&field1='
for i in total:
        print ("Element of Total: ",i)
        f = urllib.request.urlopen(baseURL +str(i))
        sleep(20)

        data_from_website=urllib.request.urlopen('https://api.thingspeak.com/channels/1045763/feeds.json?api_key=16JO0QY4LI34OLY0&results=1')
        response = data_from_website.read()   
        data=json.loads(response)
        b = data['feeds'][0]['field1']
        try:
                result.append(b)
        except:
                print("None")

with open("people.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(['Total Person', 'Hour'])
    for i in result:
        w.writerow([i,8+h])
        h=h+1

data_from_website.close()



#Model Training Part
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score

data = pd.read_csv('people.csv')
person=data.iloc[:,0:1].values
hour=data.iloc[:, -1:].values

lr = LinearRegression()
poly = PolynomialFeatures(degree=4)
hour_poly = poly.fit_transform(hour)
lr.fit(hour_poly, person)
predict = lr.predict(hour_poly)

print("Polynomial Regression r2 result : " , r2_score(person,predict) )

plt.scatter(hour, person, color='red')
plt.plot(hour, predict, color='blue')
plt.show()


#Linear Regression
lr2 = LinearRegression()
lr2.fit(hour, person)
predict2= lr2.predict(hour)

print("Linear Regression r2 result : " , r2_score(person,predict2) )

plt.scatter(hour, person, color='red')
plt.plot(hour, predict2, color='blue')
plt.show()






