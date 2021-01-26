import sys
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
import numpy as np
import clr
import ctypes
clr.FindAssembly("sick_vision_api_dotnet.dll")
clr.AddReference('sick_vision_api_dotnet')
import vision_api 
from System import IntPtr
import multiprocessing as mp

bRuning,bGet,frame = True ,False ,None

dataStream,deviceCount,count=0,0,0



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

        # create a timer
        self.timer = QTimer()
        # set timer timeout callback function
        #self.timer.timeout.connect(self.viewCam)
        #self.timer.timeout.connect(self.viewCam_sick)
        # set control_bt callback clicked  function

        #self.ui.control_bt.clicked.connect(self.controlTimer)
        self.ui.control_bt.clicked.connect(self.thread_sick_cam)
        
        
    #close window to call this funtion  
    def closeEvent(self, event):
        global bRuning
        bRuning=False
        sys.exit()

    def thread_sick_cam(self):
        global frame,bGet,bRuning,deviceCount,deviceManager,t1
        
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
            threading.Thread(target=self.sick_cam).start()
            #close thread when main thread closing
            #self.t1=threading.Thread(target=self.sick_cam)
            #t1.setDaemon(True)
            #self.t1.start()
            #mp.Process(target=self.sick_cam).start()
            time.sleep(3)
            #print(self.ui.control_bt.text())
            while self.ui.control_bt.text()=='Stop':
                #print(bGet)
                while bGet==False:time.sleep(0.01)

                image = cv2.resize(frame,(640,480))
                image=self.read_barcodes(image)
                #image=np.concatenate((image,image,image),axis=0)
                #image=image.reshape(640,480,3)
                #print(image.shape)
                qImg = QImage(image.data, 640, 480, 1920, QImage.Format_RGB888)
                self.ui.image_label.setPixmap(QPixmap.fromImage(qImg))
                QApplication.processEvents()
        else:
    
            bRuning=False
            self.ui.control_bt.setText("Start")
            QApplication.processEvents()
    def sick_cam(self):
        global bRuning,bGet,frame,dataStream,count,deviceCount
        
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
        #print(threading.active_count())
        if count==0:
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
            #bRuning=Trueprint(payloadSize,bufferCountMax)
            for bufferCount in range(bufferCountMax):
                buffer = dataStream.AllocAndAnnounceBuffer(payloadSize, IntPtr.Zero)
                dataStream.QueueBuffer(buffer)
            dataStream.StartAcquisition();
            nodeMapRemoteDevice.FindNode[vision_api.core.nodes.CommandNode]("AcquisitionStart").Execute();
            nodeMapRemoteDevice.FindNode[vision_api.core.nodes.CommandNode]("AcquisitionStart").WaitUntilDone();
            count+=1
            while bRuning:
                time.sleep(0.1)
                buffer = dataStream.WaitForFinishedBuffer(vision_api.core.Timeout(1000))
                npArray = np.empty(buffer.Size(), order='C', dtype=np.dtype('uint8'))
                destPtr = npArray.__array_interface__['data'][0]
                ctypes.memmove(destPtr, buffer.BasePtr().ToInt64(), npArray.nbytes)
                #frame = npArray.reshape((buffer.Height(),buffer.Width(),1))
                npArray=npArray.reshape((buffer.Height(),buffer.Width(),1))
                frame=np.concatenate((npArray,npArray,npArray),axis=2)
                dataStream.QueueBuffer(buffer);
                bGet = True
                #frameCounter += 1
                #print(frameCounter)
        else:
            while bRuning:
                time.sleep(0.1)
                buffer = dataStream.WaitForFinishedBuffer(vision_api.core.Timeout(1000))
                npArray = np.empty(buffer.Size(), order='C', dtype=np.dtype('uint8'))
                destPtr = npArray.__array_interface__['data'][0]
                ctypes.memmove(destPtr, buffer.BasePtr().ToInt64(), npArray.nbytes)
                #frame = npArray.reshape((buffer.Height(),buffer.Width(),1))
                npArray=npArray.reshape((buffer.Height(),buffer.Width(),1))
                frame=np.concatenate((npArray,npArray,npArray),axis=2)
                dataStream.QueueBuffer(buffer);
                bGet = True
                #frameCounter += 1
                    #print(frameCounter)

    # decode barcodes  
    def read_barcodes(self,frame):
        barcodes = pyzbar.decode(frame)
        #print(barcodes)

        for barcode in barcodes:
            
            x, y , w, h = barcode.rect
            #print((x+w)/(y+h))
            #1

            #if (x+w)/(y+h)<3 and (x+w)/(y+h)>=1:
            if  w>h and (x+w)/(y+h)>0 :
            
            #data.append((x+w)/(y+h))
                barcode_info = barcode.data.decode('utf-8')

                cv2.rectangle(frame, (x, y),(x+w, y+h), (0, 255, 0), 2) #cv2.rectangle(影像, 頂點座標, 對向頂點座標, 顏色, 線條寬度) 
                    
                    #2
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, barcode_info, (x + 6, y - 6), font, 1.0, (255, 255, 255), 1) # cv2.putText(影像, 文字, 座標, 字型, 大小, 顏色, 線條寬度, 線條種類)
                #cv2.putText(frame, str((x+w)/(y+h)), (x + 6, y - 3), font, 1.0, (255, 255, 255), 1)
            #with open("barcode_result.txt", mode ='w') as file:
            #    file.write("Recognized Barcode:" + barcode_info)
        return frame
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
