from yolo_test import gender
#import esp32
from paho.mqtt import client as mqtt_client
import submqtt as sens 
import random
import requests
import cv2,json
from PIL import Image
from datetime import datetime
import shutil,os,glob,time

# import pyqt5
import sys 
from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QColor, QPalette,QPixmap,QTransform
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtWidgets import* 
from PyQt5.uic import loadUi
import pymongo,cv2
import numpy as np
from pymongo import MongoClient,InsertOne
from sklearn.cluster import dbscan
# connecct to a Atlas cluster
client = MongoClient("mongodb+srv:// [your url]")
db = client.espcam.cam         
sensorHUMID=''
sensorTEMP=''

class YOLOThread(QThread):
    predict =   pyqtSignal(str) 

    def __init__(self,ip):
        self.ip = ip
        super().__init__()

    def run(self):
        cap = cv2.VideoCapture('http://%s:81/stream' % (self.ip))
        while True:
            # check if not null and read as cv_img
            ret, cv_img = cap.read()
            if ret:
                predict_gender= gender(cv_img)
                # print(predict_gender)
                self.predict.emit(predict_gender)  # 傳送pyqt變數資訊

                time.sleep(3)     




class VideoThread(QThread):

    # init qt video  
    change_pixmap_signal=pyqtSignal(np.ndarray)
    print("video init")
        
    def __init__(self,ip,person):
        # # read from qt
        self.ip=ip
        self.person=person
        self.url_cam = 'http://%s/capture?_cb'  % (self.ip)
        super().__init__()       


          
    def takephoto(self):
        
        photo = requests.get(self.url_cam)
        if photo.status_code!=200:
            print('esp get url probelm.')
        rawData=photo.content           
        #show photo in QT and 調整QT視窗大小
        file = open("tmp.jpg", 'wb')
        file.write(rawData)
        file.close()
        self.photoshow()
        time.sleep(2)

    def photoshow(self):
        # initialize the plot
        self.mypixmap = QPixmap()        
        self.mypixmap.load('tmp.jpg')
        if self.mypixmap.isNull():
            print('load image failed')
            return
        self.trans = QTransform() 
        self.trans.rotate(90)

        self.getstill_view.setPixmap(self.mypixmap.transformed(self.trans))        
        self.getstill_view.show()
        
    def savetodb(self):

        if self.person not in [name.name for name in self.namelist]:
            # 創新的person 
            name_obj = database(self.person,1,'home',True)
            # 將name存入list
            self.namelist.append(name_obj)
        else:
        # 用舊的name object
            for per_obj in self.namelist:
                if self.person == per_obj.name:
                    name_obj = per_obj
        
        if self.person!=None:
            # 存jpg   
            name_obj.number +=1
            filename = name_obj.name + "_" + str(name_obj.number)
            filename = filename + ".jpg"
            # save as tmp 
            os.rename('tmp.jpg', filename)
            
            # save to DB
            add=name_obj.__dict__
            db.insert_one(add)
        
        return(self.namelist)

    def convert_cv_qt(cv_img):
        # streaming 
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        return QPixmap.fromImage(convert_to_Qt_format)

    def onDisplayVideoID(self, cv_img):
        """Updates the getstill_view with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)   
        # show on label 
        self.getstill_view.setPixmap(qt_img)


    def run(self):
        
        # capture from web cam
        cap = cv2.VideoCapture('http://%s:81/stream' % (self.ip))
        while True:
            ret, cv_img = cap.read()
            if ret:
                cv_img = cv2.rotate(cv_img, cv2.cv2.ROTATE_90_CLOCKWISE)
                # 設pixmap的變數值
                # self.change_pixmap_signal.emit(cv_img)
                # print("get stream")





    

class MqttThread(QThread):
    thread_name = 'unknown'
    sleep_seconds = 1
    # 設一個pyqt signal變數
    humid = pyqtSignal(str) #放這邊會變成self attribute嗎?
    temp = pyqtSignal(str)
    time = pyqtSignal(str)


    def __init__(self,thread_name,sleep_seconds):
        # mqtt server
        self.broker = 'mqtt.eclipseprojects.io'

        # generate client ID with pub prefix randomly
        super().__init__()
        self.thread_name = thread_name
        self.sleep_seconds = sleep_seconds  
        self.client =mqtt_client.Client()
        # self.client.username_pw_set(self.id, self.pasw)

    def on_message(self, client, userdata, msg):    
        topic_humid = "sensorHUMID"
        topic_tmp="sensorTEMP"
        if msg.topic==topic_humid:
            # print(msg.topic+" "+ msg.payload.decode('utf-8'))
            global sensorHUMID
            sensorHUMID=msg.payload.decode('utf-8')
            self.humid.emit(sensorHUMID)  # 傳送pyqt變數資訊
            self.time.emit(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))

        elif msg.topic==topic_tmp:
            global sensorTEMP
            sensorTEMP=msg.payload.decode('utf-8')
            self.temp.emit(sensorTEMP)

    def on_connect(self, client, userdata, flags, rc):
        # print('trying to bind on-connect...')
        if rc == 0:
            # print("Connected to MQTT Broker!")
            client.subscribe("sensorHUMID")
            client.subscribe("sensorTEMP")
            # print('subscribe topic')

        else:
            print("Failed to connect, return code %d\n", rc)

    def connect_mqtt(self):               
        #bind call back
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker, 1883)
        print('connected to mqtt')
        
        
        self.client.loop_start()
        
    def run(self):
        self.connect_mqtt()
        while(True):

            time.sleep(5)     


class database():
    # add to db
    name = db.name
    number = db.number
    category = db.category
    status = db.status
    # add to db from python class
    def __init__(self,name,number,category,status):
        self.name = name
        self.number = number
        self.category = category
        self.status = status

# 使用QTCreator畫一個application
class MyForm(QMainWindow):

    def __init__(self):
        
        QMainWindow.__init__(self)

        # 將UI 返回self
        loadUi("ui.ui",self)

        # connect esp32 cam url
        self.mqttthread = MqttThread('work 1', 2)


        self.mqtt_launch()
        self.mqttthread.humid.connect(self.onDisplayHumID) 
        self.mqttthread.temp.connect(self.onDisplayTempID) 
        self.mqttthread.time.connect(self.onDisplayTimeID) #把發送的消息接上onDisplayhumid

        # 如果push button,則執行video_lauch function
        self.startButton.clicked.connect(self.video_launch)   

        self.DBInit()

    def DBInit(self):
        # initialize from DB.
        name_ls = db.distinct('name') 
        self.namelist=[]   
        for name_i in name_ls:
            # get the newest one            
            for data in db.find({"name":name_i}).sort("number",pymongo.DESCENDING).limit(1):
                x=database(data['name'],data['number'],data['category'],data['status'])
                self.namelist.append(x)
        print('init app,db.')          
    def onDisplayHumID(self, str):
        self.humidlabel.setText(str+'%')
    def onDisplayTempID(self, str):
        self.tmplabel.setText(str+'*C')
    def onDisplayTimeID(self, str):
        self.timelabel.setText(str)
    def onDisplayDetectID(self, str):
        # self.predictlabel.move(100, 100)
        self.predictlabel.setText(str)

    

    def mqtt_launch(self):
        self.mqttthread.start()

    # create image according things when start button is pushed
    def video_launch(self):
        # read text from user input
        ip=self.ipCamURL_LineEdit.text()
        ip = '192.168.1.106'
        person=self.Person_LineEdit.text()   
        # start AI thread   
        self.yolothread =YOLOThread(ip)
        self.yolothread.start()
        self.yolothread.predict.connect(self.onDisplayDetectID) 

        # start streaming and taking photo
        self.videothread = VideoThread(ip,person)
        # self.videothread.start() #run asych 

        # connect qt signal to video steam
        # self.videothread.change_pixmap_signal.connect(self.videothread.onDisplayVideoID)
        # #takephoto button --->沒辦法在thread裡更動QT.SETPIXMAP
        # self.photoButton.clicked.connect(self.videothread.takephoto)   
        # self.getStillButton.clicked.connect(self.videothread.savetodb)
       

if __name__=="__main__":

    app = QApplication(sys.argv)
    qt=MyForm()
    qt.show()
    sys.exit(app.exec_())





