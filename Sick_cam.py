import sys
import os
import PyQt5.QtGui
# import some PyQt5 modules
from PyQt5.QtWidgets import QApplication,QAction
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
# import Opencv module
import cv2
from pyzbar import pyzbar
from ui import *
import numpy as np
import threading
import time
import clr
import ctypes
clr.FindAssembly("sick_vision_api_dotnet.dll")
clr.AddReference('sick_vision_api_dotnet')
import vision_api 
clr.FindAssembly('AXMVS100_dotNet.dll')
clr.AddReference('AXMVS100_dotNet')
import AXMVS100_dotNet
from System import IntPtr
import multiprocessing as mp

bRuning,bGet,frame,iRuning= True ,False ,None,True

dataStream,deviceCount,count,image_s=0,0,0,0

os.chdir('C:/Users/AX/Desktop/build/save_img')

class MainWindow(QWidget):
    # class constructor
    def __init__(self):
        # call QWidget constructor
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # let label automatic size
        self.ui.image_label.setScaledContents(True)
        self.ui.image_label1.setScaledContents(True)
       
        # make a black view
        self.img = np.zeros([640,480,3],dtype=np.uint8)
        self.img.fill(0)

        self.qImg = QImage(self.img.data, 640,480,1920 , QImage.Format_RGB888) 
        
        self.ui.image_label.setPixmap(QPixmap.fromImage(self.qImg))

       
        self.ui.control_bt.clicked.connect(self.thread_sick_cam)
        
        
    #close window to call this funtion  
    def closeEvent(self, event):
        global bRuning,iRuning
        bRuning=False
        iRuning=False
        sys.exit()
    def bt_saveimage(self):
        global bRuning,image_s,iRuning

        device_ = AXMVS100_dotNet.AXMVS100();
        result = device_.AXMVS100_LightingCtrl_SetConfig(1,0,0,0,0,0,0,1)
        result = device_.AXMVS100_LightingCtrl_SetSignal(1,0,0,1)
        while iRuning:
            result1,status=device_.AXMVS100_DI_ReadLine(0,0,0)
            number=1
            while status==1:
                while os.path.exists(f'{number}.jpg'):number+=1
                image_s=image_s[...,::-1] #BGR to RGB
                cv2.imwrite(f'{number}.jpg',image_s)
                result = device_.AXMVS100_LightingCtrl_Enable(1)
                #print(f'Enable True:{result}')
                time.sleep(0.15)
                result = device_.AXMVS100_LightingCtrl_SetConfig(1,0,0,0,0,0,0,1)
                #print(f'Enable False:{result}')
                time.sleep(1)
                status=0

    def thread_sick_cam(self):
        global frame,bGet,bRuning,deviceCount,deviceManager,t1,image_s,iRuning
        
        if self.ui.control_bt.text()=='Start':

            self.ui.image_label1.setText('Wait for connecting to camera')
            self.ui.image_label1.resize(640,480)
            self.ui.image_label1.setAlignment(PyQt5.QtCore.Qt.AlignCenter)   
            self.ui.image_label1.setFont(QFont('Times', 30,QFont.Bold))
            self.ui.image_label1.setStyleSheet('color: white')
            self.ui.control_bt.setText("Stop")
            QApplication.processEvents()
            self.ui.image_label1.setText('')

            #update ui 
                
            bRuning=True
            iRuning=True
            threading.Thread(target=self.sick_cam).start()     
            threading.Thread(target=self.bt_saveimage).start()
         
            time.sleep(3)

            while self.ui.control_bt.text()=='Stop':
                while bGet==False:time.sleep(0.001)
                bGet = False
                image = cv2.resize(frame,(640,480)).reshape((480,640,1))
                image=np.concatenate((image,image,image),axis=2)
                image_s=self.read_barcodes(image)
                #image=np.concatenate((image,image,image),axis=0)
                #image=image.reshape(640,480,3)
                qImg = QImage(image_s.data, 640, 480, 1920, QImage.Format_RGB888)
                self.ui.image_label.setPixmap(QPixmap.fromImage(qImg))
                QApplication.processEvents()
        else:

            bRuning=False
            iRuning=False
            self.ui.control_bt.setText("Start")
            QApplication.processEvents()
    def sick_cam(self):
        global bRuning,bGet,frame,dataStream,count,deviceCount
        
        frameCounter = 0
        vision_api.Library.Initialize()
        deviceManager = vision_api.DeviceManager.Instance()
        deviceManager.Update()
        deviceCount = deviceManager.Devices().Count

        if count==0:
            device = deviceManager.Devices()[0].OpenDevice(vision_api.core.DeviceAccessType.Control)
            dataStreams = device.DataStreams()
            dataStream = dataStreams[0].OpenDataStream()
            nodeMapRemoteDevice = device.RemoteDevice().NodeMaps()[0]
            nodeMapRemoteDevice.FindNode[vision_api.core.nodes.EnumerationNode]("UserSetSelector").SetCurrentEntry("Default")
            nodeMapRemoteDevice.FindNode[vision_api.core.nodes.CommandNode]("UserSetLoad").Execute()
            nodeMapRemoteDevice.FindNode[vision_api.core.nodes.CommandNode]("UserSetLoad").WaitUntilDone()
            nodeFrameRate = nodeMapRemoteDevice.FindNode[vision_api.core.nodes.FloatNode]("AcquisitionFrameRate")
            #print(f'FrameRate:{nodeFrameRate.Value()}\nMax:{nodeFrameRate.Maximum()}\nMin:{nodeFrameRate.Minimum()}')
            nodeFrameRate.SetValue(30)
            #print(nodeFrameRate.Value())
            #print(f'Model Name: {nodeMapRemoteDevice.FindNode[vision_api.core.nodes.StringNode]("DeviceModelName").Value()}')
            #print(f'User ID: {nodeMapRemoteDevice.FindNode[vision_api.core.nodes.StringNode]("DeviceUserID").Value()}')
            payloadSize = nodeMapRemoteDevice.FindNode[vision_api.core.nodes.IntegerNode]("PayloadSize").Value()
            bufferCountMax = dataStream.NumBuffersAnnouncedMinRequired()
            #bRuning=Trueprint(payloadSize,bufferCountMax)
            for bufferCount in range(bufferCountMax):
                buffer = dataStream.AllocAndAnnounceBuffer(payloadSize, IntPtr.Zero)
                dataStream.QueueBuffer(buffer)
            dataStream.StartAcquisition();
            nodeMapRemoteDevice.FindNode[vision_api.core.nodes.CommandNode]("AcquisitionStart").Execute();
            nodeMapRemoteDevice.FindNode[vision_api.core.nodes.CommandNode]("AcquisitionStart").WaitUntilDone();
            count+=1
            npArray = None
            destPtr = None
            while bRuning:
                while dataStream.NumBuffersAwaitDelivery()<1:time.sleep(0.1)
                buffer = dataStream.WaitForFinishedBuffer(vision_api.core.Timeout(0))
                if npArray is None:
                    npArray = np.empty(buffer.Size(), order='C', dtype=np.dtype('uint8'))
                    destPtr = npArray.__array_interface__['data'][0]
                ctypes.memmove(destPtr, buffer.BasePtr().ToInt64(), npArray.nbytes)
                frame = npArray.reshape((buffer.Height(),buffer.Width(),1))
                dataStream.QueueBuffer(buffer);
                bGet = True

        else:
            npArray = None
            destPtr = None
            while bRuning:
                while dataStream.NumBuffersAwaitDelivery()<1:time.sleep(0.1)
                buffer = dataStream.WaitForFinishedBuffer(vision_api.core.Timeout(0))
                if npArray is None:
                    npArray = np.empty(buffer.Size(), order='C', dtype=np.dtype('uint8'))
                    destPtr = npArray.__array_interface__['data'][0]
                ctypes.memmove(destPtr, buffer.BasePtr().ToInt64(), npArray.nbytes)
                frame = npArray.reshape((buffer.Height(),buffer.Width(),1))
                dataStream.QueueBuffer(buffer);
                bGet = True
                #frameCounter += 1
                    #print(frameCounter)

    # decode barcodes  
    def read_barcodes(self,frame_1):
        barcodes = pyzbar.decode(frame_1)
        #print(barcodes)

        for barcode in barcodes:
            
            x, y , w, h = barcode.rect
            #print((x+w)/(y+h))
            #1

            #if (x+w)/(y+h)<3 and (x+w)/(y+h)>=1:
            if  w>h and (x+w)/(y+h)>0 :
            
            #data.append((x+w)/(y+h))
                barcode_info = barcode.data.decode('utf-8')

                cv2.rectangle(frame_1, (x, y),(x+w, y+h), (0, 255, 0), 2) #cv2.rectangle(影像, 頂點座標, 對向頂點座標, 顏色, 線條寬度) 
                    
                    #2
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame_1, barcode_info, (x + 6, y - 6), font, 1.2, (255, 0, 0), 1) # cv2.putText(影像, 文字, 座標, 字型, 大小, 顏色, 線條寬度, 線條種類)
                #cv2.putText(frame, str((x+w)/(y+h)), (x + 6, y - 3), font, 1.0, (255, 255, 255), 1)
            #with open("barcode_result.txt", mode ='w') as file:
            #    file.write("Recognized Barcode:" + barcode_info)
        return frame_1
    # get form size
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            #self.rect=self.geometry()
            #print(self.geometry())
            #print(self.rect.width(), self.rect.height())
            print(event.pos().x(),event.pos().y())
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # create and show mainWindow
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())


