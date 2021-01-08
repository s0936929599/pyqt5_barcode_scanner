import sys
import PyQt5.QtGui
# import some PyQt5 modules
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt
# import Opencv module
import cv2
from pyzbar import pyzbar
from cam_ui import *

class MainWindow(QWidget):
    # class constructor
    def __init__(self):
        # call QWidget constructor
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        # create a timer
        self.timer = QTimer()
        # set timer timeout callback function
        self.timer.timeout.connect(self.viewCam)
        # set control_bt callback clicked  function
        self.ui.control_bt.clicked.connect(self.controlTimer)
    
   
    # view camera
    def viewCam(self):
        # read image in BGR format
        ret, image = self.cap.read()
        #  image  barcode 
        image = self.read_barcodes(image)
        # convert image to RGB format
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # get image infos
        height, width, channel = image.shape

       

        step = channel * width
        # create QImage from image
        qImg = QImage(image.data, width, height, step, QImage.Format_RGB888)
        # show image in img_label
        self.ui.image_label.setPixmap(QPixmap.fromImage(qImg))

   
    # start/stop timer
    def controlTimer(self):
        # if timer is stopped
        if not self.timer.isActive():
            # create video capture
            self.cap = cv2.VideoCapture(0)
            
            # start timer
            self.timer.start(20)
            # update control_bt text
            self.ui.control_bt.setText("Stop")
        # if timer is started
        else:
            # stop timer
            self.timer.stop()
            # release video capture
            self.cap.release()
            # update control_bt text
            self.ui.control_bt.setText("Start")

    # decode barcodes  
    def read_barcodes(self,frame):
        barcodes = pyzbar.decode(frame)
        for barcode in barcodes:
            x, y , w, h = barcode.rect
            #1
            barcode_info = barcode.data.decode('utf-8')
            cv2.rectangle(frame, (x, y),(x+w, y+h), (0, 255, 0), 2)
            
            #2
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, barcode_info, (x + 6, y - 6), font, 2.0, (255, 255, 255), 1)
            #3
            with open("barcode_result.txt", mode ='w') as file:
                file.write("Recognized Barcode:" + barcode_info)
        return frame
    # get form size
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.rect=self.geometry()
            print(self.geometry())
            print(self.rect.width(), self.rect.height())
            #print(event.pos().x(),event.pos().y())
        

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # create and show mainWindow
    mainWindow = MainWindow()
    mainWindow.show()

    sys.exit(app.exec_())
