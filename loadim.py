import sys,time
import requests
from paho.mqtt import client as mqtt_client

from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QLabel, QPushButton)
from PyQt5.QtGui import QPixmap
ip = '192.168.1.104'
url_cam = 'http://%s/capture?_cb'  % (ip)
sensorHUMID=''
def on_connect(client, userdata, flags, rc):
    print('trying to bind on-connect...')
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe("sensorHUMID")
        client.subscribe("sensorTEMP")
        print('subscribe topic')

    else:
        print("Failed to connect, return code %d\n", rc)

def on_message(client, userdata, msg):
    # 轉換編碼utf-8才看得懂中文
    if msg.topic=='sensorHUMID':
        # print(msg.topic+" "+ msg.payload.decode('utf-8'))
        global sensorHUMID
        sensorHUMID=msg.payload.decode('utf-8')
        # return(str(sensorHUMID))

    # elif msg.topic=='sensorTEMP':
    #     # print(msg.topic+" "+ msg.payload.decode('utf-8'))
    #     global sensorTEMP
    #     sensorTEMP=msg.payload.decode('utf-8')


class esp32():
    def __init__(self):
        # mqtt server
        # self.broker = 'c65d1111-internet-facing-2e5e454121de7c2e.elb.us-east-1.amazonaws.com'
        self.broker = 'mqtt.eclipseprojects.io'
        self.topic_humid = "sensorHUMID"
        self.topic_tmp="sensorTEMP"

        # generate client ID with pub prefix randomly
        self.client_id = 'ESP32Client-eqkk36'
       
    
    def connect_mqtt(self):       
        # Set Connecting Client ID
        # client = mqtt_client.Client(self.client_id)
        # client.username_pw_set(self.id, self.pasw)
        client =mqtt_client.Client()
        #bind call back
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(self.broker, 1883)
        print('connected to mqtt')
        
        
        client.loop_start()
        time.sleep(1)
        client.loop_stop()

        # client.loop_forever()

        return(client)


class MyWidget(QWidget):
    def __init__(self):
        # create the esp32 object [this can work]
        esp_sub=esp32()
        # call the mqtt subscription[ok]
        esp_client = esp_sub.connect_mqtt()
        super().__init__()
        # sensorTEMP=0
        self.initUI()



    def initUI(self):
        self.setWindowTitle('my window')
        self.setGeometry(50, 50, 200, 150)

        layout = QGridLayout()
        self.setLayout(layout)

        self.mylabel = QLabel('click button to load image', self)
        layout.addWidget(self.mylabel, 0, 0, 1, 2)


        self.MQTTlabel = QLabel('mqtt', self)
        layout.addWidget(self.MQTTlabel, 0, 0, 2, 2)
        self.MQTTlabel.setText(sensorHUMID)
        print('mqttgot=',sensorHUMID)


        self.mybutton1 = QPushButton('load image', self)
        self.mybutton1.clicked.connect(self.loadImageAndShow)
        layout.addWidget(self.mybutton1, 1, 0)

    def loadImageAndShow(self):
        print('load image...')
        # self.mypixmap = QPixmap('lena.jpg')
        # or
        photo = requests.get(url_cam)
        # 200 正常~
        if photo.status_code!=200:
            print('espcam server not connect.')
        rawData=photo.content    

    
        #show photo in QT and 調整QT視窗大小
        file = open("tmp.jpg", 'wb')
        file.write(rawData)
        time.sleep(5)

        self.mypixmap = QPixmap()
        self.mypixmap.load('C:\\Users\\an\\esp\\espcam\\tmp.jpg')
        if self.mypixmap.isNull():
            print('load image failed')
            return
        self.mylabel.setPixmap(self.mypixmap)


if __name__ == '__main__':
    # sensorTEMP=0
    # sensorHUMID=0


    app = QApplication(sys.argv)
    # esp_sub.subscribe(client)
    # client.loop_forever() //會造成python app not show.
    
    w = MyWidget()
    w.show()
    sys.exit(app.exec_())

    
