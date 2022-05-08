import requests
import cv2,json
from PIL import Image
from datetime import datetime
import shutil,os,glob

# import pyqt5
import sys 
from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QColor, QPalette,QPixmap
from PyQt5.QtCore import QDate, QTime, QDateTime, Qt,QFile,QThread
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtWidgets import* 
from PyQt5.uic import loadUi
import pymongo
from pymongo import MongoClient,InsertOne
import pprint
from sklearn.cluster import dbscan
# private_key='fe68cb06-9e6e-424f-afd1-61f2b67f8e11'
# public_key ='vpvagifi'

client = MongoClient(url)
db = client.espcam.cam         # connecct to a Atlas cluster


class database():
    # add to db
    name = db.name
    number = db.number
    category = db.category
    status = db.status

    # add from python class
    def __init__(self,name,number,category,status):
        self.name = name
        self.number = number
        self.category = category
        self.status = status

    def add_photo(self,num):
        self.number+=num
    

class name():
    def __init__(self,name):
        self.name = str(name)
        self.number=0
        self.category = 'home'
        self.status = True
        

# 使用QTCreator畫一個application
class MyForm(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("ui.ui",self)
        self.photoButton.clicked.connect(self.takephoto)   
        self.getStillButton.clicked.connect(self.savetodb)
        self.getstill_view;   


        # initialize from DB.
        name_ls = db.distinct('name') 
        self.namelist=[]   
        for name_i in name_ls:
            #get the newest one            
            for data in db.find({"name":name_i}).sort("number",pymongo.DESCENDING).limit(1):
                x=database(data['name'],data['number'],data['category'],data['status'])
                self.namelist.append(x)

    def takephoto(self):
        # "ESPCAM SERVER" IP
        # ip = self.ipCamURL_LineEdit.text()
        ip = '192.168.1.106'

        # 如果有ip 跟 person 情況做存照
        if ip!= None :
            # connect esp32 cam url
            url = 'http://%s/capture?_cb' % (ip)
            photo = requests.get(url)
            # 200 正常~
            if photo.status_code!=200:
                print('espcam server not connect.')
            rawData=photo.content           
        
            #show photo in QT and 調整QT視窗大小
            file = open("tmp.jpg", 'wb')
            file.write(rawData)
            pixmap= QPixmap("tmp.jpg")
            self.getstill_view.setPixmap(pixmap)
            # self.resize(pixmap.width(),pixmap.height())
            self.getstill_view.resize(pixmap.width(),pixmap.height())
            self.getstill_view.setMask(pixmap.mask())
            self.getstill_view.show()
        return (rawData)

    def savetodb(self):
        # 從textbox得到目前照片標記
        person=self.Person_LineEdit.text()      

        if person not in [name.name for name in self.namelist]:
            # 創新的person 
            name_obj = name(person)
            # 將name存入list
            self.namelist.append(name_obj)
        else:
        # 用舊的name object
            for per_obj in self.namelist:
                if person == per_obj.name:
                    name_obj = per_obj
        
        if person!=None:
            # 存jpg   
            name_obj.number +=1
            filename = name_obj.name + "_" + str(name_obj.number)
            filename = filename + ".jpg"
            os.rename('tmp.jpg', 'test.jpg')
            # shutil.copy("tmp.jpg")

            
            # 存DB
            new_posts = database(name_obj.name,name_obj.number,'home',True)
            add=new_posts.__dict__
            db.insert_one(add)
        
            #調整QT視窗大小
            pixmap= QPixmap(filename)
            # self.getstill_view.setPixmap(pixmap)
            self.getstill_view.setText("test")

            print(filename)
            self.getstill_view.setMask(pixmap.mask())
            self.getstill_view.show()


        return(self.namelist)
        

if __name__=="__main__":

    app = QApplication(sys.argv)
    #app.setWindowIcon(QtGui.QIcon("/icon/logo.png")
    # 建立 QT Form物件
    qt=MyForm()
    qt.show()
    sys.exit(app.exec_())





