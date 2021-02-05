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
import TriggerOut 
import AXMVS100_dotNet
from System import IntPtr
import multiprocessing as mp
from multiprocessing import Process, Queue
TriggerOut.main()
bRuning,bGet,frame,iRuning,sRunning,get_image= True ,False ,None,True,False,True

dataStream,deviceCount,count,image_s,status=0,0,0,0,0

os.chdir('C:/Users/AX/Desktop/save_img')

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

        #self.timer = QTimer()
        #self.timer.timeout.connect(self.image_update)
        self.ui.control_bt.clicked.connect(self.thread_sick_cam)
        #self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        #self.setWindowFlags( QtCore.Qt.CustomizeWindowHint )
        
    #close window to call this funtion  
    def closeEvent(self, event):
        global bRuning,iRuning,sRunning
        bRuning=False
        iRuning=False
        sRunning=False
        sys.exit()
    def bt_saveimage(self): # button trigger light and pyzbar
        global bRuning,image_s,iRuning,sRunning,frame,bGet
        while bRuning:
            while bGet==False and bRuning:time.sleep(0.001)
            bGet = False
            #print(threading.active_count())
            try:
                image = cv2.resize(frame,(640,480)).reshape((480,640,1))
                image_s=np.concatenate((image,image,image),axis=2)
                image_s=self.read_barcodes(image_s)
                qImg = QImage(image_s.data, 640, 480, 1920, QImage.Format_RGB888)
                self.ui.image_label.setPixmap(QPixmap.fromImage(qImg))
                QApplication.processEvents()
            except:
                pass

        

    def image_update(self): #image update every second
        global frame,bGet,bRuning,deviceCount,deviceManager,t1,image_s,iRuning,status,sRunning
        while sRunning:
            while bGet==False:time.sleep(0.001)
            bGet = False
            image = cv2.resize(frame,(640,480)).reshape((480,640,1))
            image_s=np.concatenate((image,image,image),axis=2)
            qImg = QImage(image_s.data, 640, 480, 1920, QImage.Format_RGB888)
            self.ui.image_label.setPixmap(QPixmap.fromImage(qImg))
            QApplication.processEvents()

    def thread_sick_cam(self):
        global frame,bGet,bRuning,deviceCount,deviceManager,t1,image_s,iRuning,status,sRunning,get_image
        
        if self.ui.control_bt.text()=='Start':

            self.ui.image_label1.setText('Wait for connecting to camera')
            self.ui.image_label1.resize(640,480)
            self.ui.image_label1.setAlignment(PyQt5.QtCore.Qt.AlignCenter)   
            self.ui.image_label1.setFont(QFont('Times', 30,QFont.Bold))
            self.ui.image_label1.setStyleSheet('color: white')
            self.ui.control_bt.setText("Connecting")
            QApplication.processEvents()
            self.ui.image_label1.setText('')
               
            bRuning=True 
            iRuning=True
            sRunning=True
            threading.Thread(target=self.harware_trigger_camera).start()     
            threading.Thread(target=self.bt_saveimage).start()
            
            #self.timer.start(1)
            time.sleep(3)
            self.ui.control_bt.setText("Stop")
            
        else:

            bRuning=False #stop image thread
            get_image=False
            iRuning=False #stop save thread
            sRunning=False
            self.ui.control_bt.setText("Start")

            #sys.exit()
 
    def harware_trigger_camera(self):
        global bRuning,bGet,frame,get_image,iRuning,sRunning

        frameCounter = 0
        vision_api.Library.Initialize()
        deviceManager = vision_api.DeviceManager.Instance()
        deviceManager.Update()
        deviceCount = deviceManager.Devices().Count
        #d = deviceManager.Devices()[i]
        #print(f'{d.ModelName()}')
        #print(f'{d.ParentInterface().DisplayName()}')
        #print(f'{d.ParentInterface().ParentSystem().DisplayName()}')
        #print(f'{d.ParentInterface().ParentSystem().Version()}')
        device = deviceManager.Devices()[0].OpenDevice(vision_api.core.DeviceAccessType.Control)
        dataStreams = device.DataStreams()
        dataStream = dataStreams[0].OpenDataStream()
        nodeMapRemoteDevice = device.RemoteDevice().NodeMaps()[0]
        nodeMapRemoteDevice.FindNode[vision_api.core.nodes.EnumerationNode]("UserSetSelector").SetCurrentEntry("Default")
        nodeMapRemoteDevice.FindNode[vision_api.core.nodes.CommandNode]("UserSetLoad").Execute()
        nodeMapRemoteDevice.FindNode[vision_api.core.nodes.CommandNode]("UserSetLoad").WaitUntilDone()
        #print(f'Model Name: {nodeMapRemoteDevice.FindNode[vision_api.core.nodes.StringNode]("DeviceModelName").Value()}')
        #print(f'User ID: {nodeMapRemoteDevice.FindNode[vision_api.core.nodes.StringNode]("DeviceUserID").Value()}')
        payloadSize = nodeMapRemoteDevice.FindNode[vision_api.core.nodes.IntegerNode]("PayloadSize").Value()
        bufferCountMax = dataStream.NumBuffersAnnouncedMinRequired()
        #print(payloadSize,bufferCountMax)
        for bufferCount in range(bufferCountMax):
            buffer = dataStream.AllocAndAnnounceBuffer(payloadSize, IntPtr.Zero)
            dataStream.QueueBuffer(buffer)
        
        nodeMapRemoteDevice.FindNode[vision_api.core.nodes.EnumerationNode]("TriggerSelector").SetCurrentEntry("ExposureStart")
        nodeMapRemoteDevice.FindNode[vision_api.core.nodes.EnumerationNode]("TriggerMode").SetCurrentEntry("On")
        nodeMapRemoteDevice.FindNode[vision_api.core.nodes.EnumerationNode]("TriggerSource").SetCurrentEntry("Line0")
        nodeMapRemoteDevice.FindNode[vision_api.core.nodes.EnumerationNode]("TriggerActivation").SetCurrentEntry("RisingEdge")
        dataStream.StartAcquisition()
        nodeMapRemoteDevice.FindNode[vision_api.core.nodes.CommandNode]("AcquisitionStart").Execute()
        #nodeMapRemoteDevice.FindNode[vision_api.core.nodes.CommandNode]("AcquisitionStart").WaitUntilDone()

        time.sleep(1)

        while bRuning:
            
            for t0 in range(1000): 
                if dataStream.NumBuffersAwaitDelivery()>0 or bRuning==False :break
                else:time.sleep(0.001)
            #while dataStream.NumBuffersAwaitDelivery()<1 and get_image :time.sleep(0.01)
            if bRuning==False:
                remoteNodeMap = device.RemoteDevice().NodeMaps()[0];
                remoteNodeMap.FindNode[vision_api.core.nodes.CommandNode]("AcquisitionStop").Execute();
                remoteNodeMap.FindNode[vision_api.core.nodes.CommandNode]("AcquisitionStop").WaitUntilDone();
                dataStream.KillWait();
                dataStream.StopAcquisition(vision_api.core.AcquisitionStopMode.Default);
                dataStream.Flush(vision_api.core.DataStreamFlushMode.DiscardAll);
                for buffer in dataStream.AnnouncedBuffers():
                         
                    dataStream.RevokeBuffer(buffer);
                vision_api.Library.Close();
                break
            try:
                
                buffer = dataStream.WaitForFinishedBuffer(vision_api.core.Timeout(1000))
                npArray = np.empty(buffer.Size(), order='C', dtype=np.dtype('uint8'))
                destPtr = npArray.__array_interface__['data'][0]
                ctypes.memmove(destPtr, buffer.BasePtr().ToInt64(), npArray.nbytes)
                frame = npArray.reshape((buffer.Height(),buffer.Width(),1))
                dataStream.QueueBuffer(buffer);
                bGet = True
                frameCounter += 1
                #print(frameCounter)
            except:
                pass
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
