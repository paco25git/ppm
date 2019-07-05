#Title: ppmgui.py 
#Author: Francisco Gonzalez-Martinez
#Date: 7/1/2019

#This is a library for making the GUI to the PPM device

#---------importing libraries
import sys
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import (QMainWindow, QApplication, QAction, QLabel, 
 QGridLayout, QGroupBox, QSpinBox,QDoubleSpinBox,QStyle,QStackedWidget,
 QWidget, QVBoxLayout,QHBoxLayout, QSlider, QDialog, QPushButton, QMdiSubWindow, QTextEdit,QMdiArea,QBoxLayout,QComboBox)
from PyQt5.QtGui import QImage, QPixmap, QFont, QPainter, QPen
from PyQt5.QtCore import QSize, QThread, pyqtSignal, pyqtSlot, Qt, QPoint
import time
import cv2
import numpy as np
from ctypes import *
#import threading
import win32event


#a class for making a thread that handles the camera capture
class live(QThread):
    livestream = pyqtSignal(QImage)
    liveproces = pyqtSignal(QImage)
    
    def __init__(self,camera, mem, ppImg, hEvent):
        super(live,self).__init__(parent=None)
        self.camera=camera
        self.mem=mem        
        self.colormap="jet"
        self.ppImg2=ppImg
        self.handleEvent=hEvent
    def run(self):    
        self.camera.start_continuous_capture()
        while True:		
            self.n=1
            while True:
                #self.camera.freeze_video()
                #time.sleep(.1)
                self.waitEvent=win32event.WaitForSingleObject(self.handleEvent,1000)
                self.ID=self.camera.get_active_image_mem()-1
                if self.ID==0:
                    self.ID=self.camera.NBuff                
                if self.waitEvent==win32event.WAIT_TIMEOUT:
                    print("Timed out")
                elif self.waitEvent==win32event.WAIT_OBJECT_0:
                    arr=self.camera.get_image_v2(self.camera.memID.get(self.ID))
                    print(self.ID)
                    self.n+=1
                rgbImage = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
                h, w,ch= rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QtGui.QImage(rgbImage.data, w, h,bytesPerLine, QtGui.QImage.Format_RGB888)
                p = convertToQtFormat.scaled(1353, 1233,QtCore.Qt.KeepAspectRatio)
                self.livestream.emit(p)
                if self.n>len(self.mem):
                    break
                    
            self.ppImg=do_processing(self.mem)
            self.maxI=max(self.ppImg)
            self.ppImg=self.ppImg.reshape(1024,1280)
            self.ppImg/=self.maxI
            self.ppImg*=255
            
            self.ppImg2.value=self.ppImg.astype(np.uint8)
            self.ppImg=self.ppImg.astype(np.uint8)
            
            if self.colormap=="jet":
                self.ppImg=cv2.applyColorMap(self.ppImg, cv2.COLORMAP_JET)
                
            if self.colormap=="hot":
                self.ppImg=cv2.applyColorMap(self.ppImg, cv2.COLORMAP_HOT)
                
            if self.colormap=="aut":
                self.ppImg=cv2.applyColorMap(self.ppImg, cv2.COLORMAP_AUTUMN)
                
            if self.colormap=="bone":
                self.ppImg=cv2.applyColorMap(self.ppImg, cv2.COLORMAP_BONE)
                
            rgbImage2 = cv2.cvtColor(self.ppImg, cv2.COLOR_BGR2RGB)
            h2, w2, ch2 = rgbImage2.shape
            bytesPerLine2 = ch2 * w2
            convertToQtFormat = QtGui.QImage(rgbImage2.data, w2, h2, bytesPerLine2, QtGui.QImage.Format_RGB888)
            p2 = convertToQtFormat.scaled(1353, 1233,QtCore.Qt.KeepAspectRatio)
            self.liveproces.emit(p2)
            
    @pyqtSlot(str)
    def changeColorMap(self,cm):
        self.colormap=cm
        

#a class for making subWindows outside from the main window
class subwindow(QWidget):
    valueChanged = pyqtSignal(int)
    def __init__(self):
        super(subwindow,self).__init__(parent=None)
          
    def keyPressEvent(self, e):  
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
            
    def createWindowManageCamera(self, current,confData):
        self.current=current
        self.confData=confData
        self.setWindowTitle("Manage Camera")      
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.resize(700,400)
        
        self.genLayout=QVBoxLayout()
        
        self.capBox=QGroupBox("Capture",self)
        self.capBoxLayout=QHBoxLayout()
        
        self.expBox=QGroupBox("Exposure",self)        
        self.expV=QVBoxLayout()
        self.expH=QHBoxLayout()
        
        self.camSel=QLabel("Camera selected = "+str(self.current.name))
        self.expL=QLabel("Current value: ")
        self.expU=QLabel(" [ms]")
        self.expVal=QSpinBox()
        self.expVal.setRange(1,100)
        self.expVal.setSingleStep(1) 
        
        self.expVal.setMaximumWidth(80)
        self.expSlider=QSlider(Qt.Horizontal)
        self.expSlider.setFocusPolicy(Qt.StrongFocus)
        self.expSlider.setTickPosition(QSlider.TicksBothSides)
        self.expSlider.setTickInterval(10)
        self.expSlider.setSingleStep(1)
        self.playButton=QPushButton()
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.setMaximumWidth(50)
        self.pauseButton=QPushButton()
        self.pauseButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.pauseButton.setMaximumWidth(50)
        self.stopButton=QPushButton()
        self.stopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stopButton.setMaximumWidth(50)
        self.initButton=QPushButton("Init Cam",self)
        self.initButton.setMaximumWidth(150)
        self.exitButton=QPushButton("Exit Cam",self)
        self.exitButton.setMaximumWidth(150)        
        
        self.expSlider.valueChanged.connect(self.expVal.setValue)
        self.expVal.valueChanged.connect(self.expSlider.setValue)
        self.expVal.valueChanged.connect(self.changeExp)
        self.expVal.setValue(self.current.get_exposure())
        
        self.capBoxLayout.addWidget(self.initButton) 
        self.capBoxLayout.addWidget(self.playButton)
        self.capBoxLayout.addWidget(self.pauseButton)           
        self.capBoxLayout.addWidget(self.stopButton)           
        self.capBoxLayout.addWidget(self.exitButton)
        
        #self.expH.addStretch(1)
        self.expH.addWidget(self.expL)
        self.expH.addWidget(self.expVal)
        self.expH.addWidget(self.expU)
        
        self.expV.addLayout(self.expH)
        self.expV.addWidget(self.expSlider)
                     
        
        self.expBox.setLayout(self.expV)
        self.capBox.setLayout(self.capBoxLayout)
        
        #self.genLayout.addStretch(1)
        self.genLayout.addWidget(self.camSel,0,Qt.AlignCenter)
        self.genLayout.addWidget(self.capBox)
        self.genLayout.addWidget(self.expBox)
        self.setLayout(self.genLayout)
        
    def changeExp(self):
        self.exp=self.expVal.value()
        if str(type(self.current))=="<class 'camdcx.Camera'>":
            self.current.set_exposure(self.exp)
        return self.exp
        
    def changeWSize(self):
        self.confData.set('processing','lsin',str(self.wsVal.value()))
        self.lsiThr.change_window(self.wsVal.value())

    def createLSIProcessingOptions(self,winN,current,lsiThr,confData):
        self.current=current
        self.confData=confData
        self.setWindowTitle("LSI Processing options")      
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.resize(700,400)
        self.lsiThr=lsiThr
        self.genLay=QVBoxLayout()
        
        ##Selection of sort LSI-----
        self.sLSI=QComboBox()
        self.sLSI.addItem("Time contrast LSI")
        self.sLSI.addItem("Space contrast LSI")
        
        ##Time box creation---------
        self.timeBox=QGroupBox("Time contrast parameters",self)
        self.timeBoxL=QHBoxLayout()
        self.tBL=QLabel("Window size: ")
        self.wsVal=QSpinBox()
        self.wsVal.setRange(1,60)
        self.wsVal.setSingleStep(1)
        self.wsVal.setValue(winN)
        self.wsVal.setMaximumWidth(80)
        self.wsUL=QLabel("[frames]")
        self.timeBoxL.addWidget(self.tBL)
        self.timeBoxL.addWidget(self.wsVal)
        self.timeBoxL.addWidget(self.wsUL)
        self.timeBox.setLayout(self.timeBoxL)

        self.wsVal.valueChanged.connect(self.changeWSize)
        self.wsVal.setValue(self.lsiThr.window)
        
        ##Space box creation--------
        self.spaceBox=QGroupBox("Space contrast parameters",self)
        self.spaceBoxL=QHBoxLayout()
        self.spaceBL=QLabel("Window size: ...")
        #self.wsVal=QSpinBox()
        #self.wsVal.setMaximumWidth(80)
        #self.wsUL=QLabel("[frames]")
        self.spaceBoxL.addWidget(self.spaceBL)
        #self.timeBoxL.addWidget(self.wsVal)
        #self.timeBoxL.addWidget(self.wsUL)
        self.spaceBox.setLayout(self.spaceBoxL)
        
        self.stackedWidget = QStackedWidget()
        self.stackedWidget.addWidget(self.timeBox)
        self.stackedWidget.addWidget(self.spaceBox)
        
        self.expBox=QGroupBox("Exposure",self)        
        self.expV=QVBoxLayout()
        self.expH=QHBoxLayout()
        self.expL=QLabel("Current value: ")
        self.expU=QLabel(" [ms]")
        self.expVal=QSpinBox()
        self.expVal.setRange(1,100)
        self.expVal.setSingleStep(1) 
        self.expVal.setMaximumWidth(80)
        self.expSlider=QSlider(Qt.Horizontal)
        self.expSlider.setFocusPolicy(Qt.StrongFocus)
        self.expSlider.setTickPosition(QSlider.TicksBothSides)
        self.expSlider.setTickInterval(10)
        self.expSlider.setSingleStep(1)
        
        self.sLSI.activated.connect(self.stackedWidget.setCurrentIndex)
        self.expSlider.valueChanged.connect(self.expVal.setValue)
        self.expVal.valueChanged.connect(self.expSlider.setValue)
        self.expVal.valueChanged.connect(self.changeExp)
        self.expVal.setValue(self.current.get_exposure())
        
        self.expH.addWidget(self.expL)
        self.expH.addWidget(self.expVal)
        self.expH.addWidget(self.expU)
        
        self.expV.addLayout(self.expH)
        self.expV.addWidget(self.expSlider)
                     
        
        self.expBox.setLayout(self.expV)
        
        self.genLay.addWidget(self.sLSI)
        self.genLay.addWidget(self.stackedWidget)
        self.genLay.addWidget(self.expBox)
        self.setLayout(self.genLay)
               
    def createContrastOptions(self, lsiThr):
        self.setWindowTitle("Contrast options")      
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.resize(700,400)
        self.lsiThr=lsiThr

        self.contLayout=QVBoxLayout()

        self.kVal=QSpinBox()
        self.kVal.setRange(1,10000)
        self.kVal.setSingleStep(1)         
        self.kVal.setMaximumWidth(80)

        self.maxSDVal=QDoubleSpinBox()
        self.maxSDVal.setRange(0,1)
        self.maxSDVal.setSingleStep(0.0001)         
        self.maxSDVal.setMaximumWidth(80)

        self.maxSDSlider=QSlider(Qt.Horizontal)
        self.maxSDSlider.setMinimum(0)
        self.maxSDSlider.setMaximum(10000)
        self.maxSDSlider.setFocusPolicy(Qt.StrongFocus)
        self.maxSDSlider.setTickPosition(QSlider.TicksBothSides)
        self.maxSDSlider.setTickInterval(50)
        self.maxSDSlider.setSingleStep(1)
        
        self.kSlider=QSlider(Qt.Horizontal)
        self.kSlider.setMaximum(10000)
        self.kSlider.setFocusPolicy(Qt.StrongFocus)
        self.kSlider.setTickPosition(QSlider.TicksBothSides)
        self.kSlider.setTickInterval(1000)
        self.kSlider.setSingleStep(1)

        self.kSlider.valueChanged.connect(self.kVal.setValue)
        self.kVal.valueChanged.connect(self.kSlider.setValue)
        self.kVal.valueChanged.connect(self.changeK)
        self.kVal.setValue(self.lsiThr.k)

        self.maxSDSlider.valueChanged.connect(self.handlemaxSDSlider)
        self.maxSDVal.valueChanged.connect(self.handlemaxSDVal)
        self.maxSDVal.setValue(self.lsiThr.maxSD)
        self.maxSDVal.valueChanged.connect(self.change_maxSD)

        self.contLayout.addWidget(self.kVal)
        self.contLayout.addWidget(self.kSlider)
        self.contLayout.addWidget(self.maxSDVal)
        self.contLayout.addWidget(self.maxSDSlider)
        self.setLayout(self.contLayout)

    def handlemaxSDSlider(self):
        self.maxSDVal.setValue(self.maxSDSlider.value()/10000)

    def handlemaxSDVal(self):
        self.maxSDSlider.setValue(self.maxSDVal.value()*10000)

    def changeK(self):
        self.lsiThr.change_k(self.kSlider.value())

    def change_maxSD(self):
        self.lsiThr.changeMaxSD(self.maxSDVal.value())

           
class dialog(QDialog):
    
    def __init__(self):
        super(dialog,self).__init__(parent=None)        
        self.setWindowModality(Qt.ApplicationModal)
        
    def keyPressEvent(self, e):  
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
        
    def createAboutDialog(self,title):
        self.setWindowTitle(title)
        self.resize(700,400)
        self.AL=QVBoxLayout()
        self.ALmes=QVBoxLayout()
        
        self.Amss=QLabel("Version: 1.0")
        self.Amss1=QLabel("Author: Francisco Gonzalez-Martinez")
        self.Amss2=QLabel("Date: May-27-2019")
        self.Amss3=QLabel("University of California, Riverside")
        self.Amss.setAlignment(Qt.AlignCenter)
        self.Amss1.setAlignment(Qt.AlignCenter)
        self.Amss2.setAlignment(Qt.AlignCenter)
        self.Amss3.setAlignment(Qt.AlignCenter)
        self.AdB=QPushButton("Ok",self)
        self.AdB.setMaximumWidth(200)
        self.AdB.clicked.connect(self.close)

        self.ALmes.addWidget(self.Amss)
        self.ALmes.addWidget(self.Amss1)
        self.ALmes.addWidget(self.Amss2)
        self.ALmes.addWidget(self.Amss3)
        self.AL.addLayout(self.ALmes)
        self.AL.addWidget(self.AdB,0,Qt.AlignCenter)
        self.setLayout(self.AL)
        self.exec_()
        
    def createWelcomeDialog(self,title,message):
        self.setWindowTitle(title)
        self.resize(700,400)
        self.sdL=QVBoxLayout()
        
        self.mss=QLabel(message)
        self.mss.setAlignment(Qt.AlignCenter)
        self.sdB=QPushButton("Start",self)
        self.sdB.setMaximumWidth(200)
        self.sdB.clicked.connect(self.close)

        self.sdL.addWidget(self.mss)
        self.sdL.addWidget(self.sdB,0,Qt.AlignCenter)
        self.setLayout(self.sdL)
        self.exec_()
        
                
class App(QMainWindow):
    count=0
    colMap = pyqtSignal(str)
    def __init__(self,screen,cameras,lsiThr,confData,thLThread=None,jaiThread=None):
        super(App,self).__init__()
        #screen size
        self.screen=screen
        print('Screen: %s' % self.screen.name())
        self.scrSize = self.screen.size()
        print('Size: %d x %d' % (self.scrSize.width(), self.scrSize.height()))
        self.scrAva = self.screen.availableGeometry()
        print('Available: %d x %d' % (self.scrAva.width(), self.scrAva.height()))
        self.camAspR=5/4
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)
        self.title="Portable perfusion monitor"
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
        self.cameras=cameras
        self.currentCam=self.cameras[0]
        self.winN=confData.getint('processing','lsin')
        self.colorMaps=["jet","hot","aut","bone"]
        self.colorMap=self.colorMaps[0]
        self.lsiThr=lsiThr
        self.confData=confData
        self.thLThread=thLThread
        self.jaiThread=jaiThread

        #Painting red line section
        self.drawing = False
        self.firstPoint = QPoint()
        self.lastPoint = QPoint()
        #self.image = QPixmap("myimg.jpg")
        self.setGeometry(100, 100, 500, 300)
        #self.label = QLabel(self)
        #self.label.resize(500, 40)
        #self.resize(self.image.width(), self.image.height())
        self.setMouseTracking(True)

        self.initUI()

    def setThread(self, threadName: str, thread):
        if threadName=='Thorlabs':
            self.thLThread=thread
            return True
        elif threadName=='Jai':
            self.jaiThread=thread
            return True
        else:
            return False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            print(event.pos())
            self.drawing = True
            self.firstPoint = event.pos()

    def keyPressEvent(self, e):  
        if e.key() == QtCore.Qt.Key_Escape:
            print("escape")
        if e.key() == QtCore.Qt.Key_F11:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
                
    def newWindowMDI(self):
        App.count = App.count+1
        sub = QMdiSubWindow()
        sub.setWidget(QTextEdit())
        sub.setWindowTitle("subwindow "+str(App.count))
        self.mdi.addSubWindow(sub)
        sub.show()
        
    def simpleDialog(self):
        self.myDialog=dialog()
        self.myDialog.createAboutDialog("About this program")
           
    def createASubwindow(self):        
        self.mySubwindow=subwindow()
        self.mySubwindow.createWindowManageCamera(self.currentCam,self.confData)
        self.mySubwindow.show()
        
    def createASubwindow2(self):
        self.procOpt=subwindow()
        self.procOpt.createLSIProcessingOptions(self.winN,self.currentCam,self.lsiThr,self.confData)
        self.procOpt.show()
        
    def selectedCameraThorlabs(self): 
        self.currentCam=self.cameras[0]
        self.camThorlabsAct.setFont(self.fBond)
        
        for i in self.cameras:
            if i.name=="Thorlabs":
                exec('self.cam{}Act.setFont(self.fBond)'.format(i.name))
            else:
                exec('self.cam{}Act.setFont(self.fNBond)'.format(i.name))

    def selectedCameraAD080GE_0(self): 
        self.currentCam=self.cameras[0]
        self.camThorlabsAct.setFont(self.fBond)
        
        for i in self.cameras:
            if i.name=="AD080GE_0":
                exec('self.cam{}Act.setFont(self.fBond)'.format(i.name))
            else:
                exec('self.cam{}Act.setFont(self.fNBond)'.format(i.name))

    def selectedCameraAD080GE_1(self): 
        self.currentCam=self.cameras[0]
        self.camThorlabsAct.setFont(self.fBond)
        
        for i in self.cameras:
            if i.name=="AD080GE_1":
                exec('self.cam{}Act.setFont(self.fBond)'.format(i.name))
            else:
                exec('self.cam{}Act.setFont(self.fNBond)'.format(i.name))

                
    def selectedCameranativeCam0(self):  
        self.currentCam=self.cameras[1]
        for i in self.cameras:
            if i.name=="nativeCam0":
                exec('self.cam{}Act.setFont(self.fBond)'.format(i.name))
            else:
                exec('self.cam{}Act.setFont(self.fNBond)'.format(i.name))
        
    def selectedCameranativeCam1(self): 
        self.currentCam=self.cameras[2]
        for i in self.cameras:
            if i.name=="nativeCam1":
                exec('self.cam{}Act.setFont(self.fBond)'.format(i.name))
            else:
                exec('self.cam{}Act.setFont(self.fNBond)'.format(i.name))
        
    def selectedCameranativeCam2(self):
        self.currentCam=self.cameras[3]
        for i in self.cameras:
            if i.name=="nativeCam2":
                exec('self.cam{}Act.setFont(self.fBond)'.format(i.name))
            else:
                exec('self.cam{}Act.setFont(self.fNBond)'.format(i.name))
    
    def selectedJet(self):
        self.colorMap=self.colorMaps[0] 
        self.colMap.emit(self.colorMap)
        for i in self.colorMaps:
            if i=="jet":
                exec('self.{}Act.setFont(self.fBond)'.format(i))
            else:
                exec('self.{}Act.setFont(self.fNBond)'.format(i))
        
    def selectedHot(self):
        self.colorMap=self.colorMaps[1]
        self.colMap.emit(self.colorMap)
        for i in self.colorMaps:
            if i=="hot":
                exec('self.{}Act.setFont(self.fBond)'.format(i))
            else:
                exec('self.{}Act.setFont(self.fNBond)'.format(i))
        
    def selectedAutumn(self):
        self.colorMap=self.colorMaps[2]
        self.colMap.emit(self.colorMap)
        for i in self.colorMaps:
            if i=="aut":
                exec('self.{}Act.setFont(self.fBond)'.format(i))
            else:
                exec('self.{}Act.setFont(self.fNBond)'.format(i))
        
    def selectedBone(self):
        self.colorMap=self.colorMaps[3]
        self.colMap.emit(self.colorMap)
        for i in self.colorMaps:
            if i=="bone":
                exec('self.{}Act.setFont(self.fBond)'.format(i))
            else:
                exec('self.{}Act.setFont(self.fNBond)'.format(i))
        
    def setImage(self, arr):
        rgbImage = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
        h, w,ch= rgbImage.shape
        bytesPerLine = ch * w
        convertToQtFormat = QtGui.QImage(rgbImage.data, w, h,bytesPerLine, QtGui.QImage.Format_RGB888)
        p = convertToQtFormat.scaled(1353, 1233,QtCore.Qt.KeepAspectRatio)
        self.label.setPixmap(QPixmap.fromImage(p))
        
    def setImage2(self, image):
        #print(image)
        
        rgbImage=cv2.cvtColor(cv2.applyColorMap(image, cv2.COLORMAP_JET), cv2.COLOR_BGR2RGB)
        h, w, ch= rgbImage.shape
        bytesPerLine = ch * w
        convertToQtFormat = QtGui.QImage(rgbImage.data, w, h,bytesPerLine, QtGui.QImage.Format_RGB888)
        p = convertToQtFormat.scaled(1353, 1233,QtCore.Qt.KeepAspectRatio)
        self.label2.setPixmap(QPixmap.fromImage(p))
        
    def createContOpt(self):
        self.ContOpt=subwindow()
        self.ContOpt.createContrastOptions(self.lsiThr)
        self.ContOpt.show()

    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height) 
        self.histFlag=False
        
        self.label = QLabel(self)
        self.label.move(0, 120)
        #self.label.resize(1353, 1233)
        self.label.resize(self.scrAva.width()/2, (self.scrAva.width()/2)*(1/self.camAspR))
        
        self.label2 = QLabel(self)
        #self.label2.move(1363,120)
        self.label2.move(self.scrAva.width()/2+10,120)
        #self.label2.resize(1353,1233) 
        self.label2.resize(self.scrAva.width()/2, (self.scrAva.width()/2)*(1/self.camAspR)) 
               
        
        #----setting the menubar
        mainMenu=self.menuBar()
        #FILE-----
        fileMenu = mainMenu.addMenu('File')
        newAct=QAction("New",self)
        fileMenu.addAction(newAct)
        exitAct=QAction("Exit",self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip("Exit application")
        exitAct.triggered.connect(self.close)
        fileMenu.addAction(exitAct)
        
        #EDIT-----
        self.editMenu = mainMenu.addMenu('Edit')
        self.selCam=self.editMenu.addMenu("Select camera")
        
        self.fBond=QtGui.QFont()
        self.fBond.setBold(True)
        
        self.fNBond=QtGui.QFont()
        self.fNBond.setBold(False)
        
        for i in self.cameras:
            exec('self.cam{}Act=QAction("Camera {}",self)'.format(i.name,i.name))
            exec('self.cam{}Act.triggered.connect(self.selectedCamera{})'.format(i.name,i.name))
            exec('self.selCam.addAction(self.cam{}Act)'.format(i.name))
        exec('self.cam{}Act.setFont(self.fBond)'.format(self.cameras[0].name))
                
        mcAct=QAction("Manage Camera",self)
        mcAct.triggered.connect(self.createASubwindow)
        mcAct.setShortcut("Ctrl+M")             
        self.editMenu.addAction(mcAct)        
        
        #VIEW-----
        viewMenu = mainMenu.addMenu('View')
        newWAct=QAction("New Window",self)
        newWAct.triggered.connect(self.newWindowMDI)
        viewMenu.addAction(newWAct)
        chcmct=viewMenu.addMenu("Change Color Map")
        self.jetAct=QAction("Jet",self)
        self.jetAct.setFont(self.fBond)
        self.jetAct.triggered.connect(self.selectedJet)
        chcmct.addAction(self.jetAct)
        self.hotAct=QAction("Hot",self)
        self.hotAct.triggered.connect(self.selectedHot)
        chcmct.addAction(self.hotAct)
        self.autAct=QAction("Autumn",self)
        self.autAct.triggered.connect(self.selectedAutumn)
        chcmct.addAction(self.autAct)
        self.boneAct=QAction("Bone",self)
        self.boneAct.triggered.connect(self.selectedBone)
        chcmct.addAction(self.boneAct)
        self.contAct=QAction("Contrast Options",self)
        viewMenu.addAction(self.contAct)
        self.contAct.triggered.connect(self.createContOpt)
        
        #SEARCH---
        searchMenu = mainMenu.addMenu('Search')
        
        #TOOLS----
        toolsMenu = mainMenu.addMenu('Tools')
        poAct=toolsMenu.addMenu("Processing options")
        lsiM=QAction("LSI options",self)
        lsiM.triggered.connect(self.createASubwindow2)
        poAct.addAction(lsiM)
        histAct=QAction("Show histogram",self)
        #histAct.triggered.connect(self.createHistogram)
        toolsMenu.addAction(histAct)
        
        #HELP-----
        helpMenu = mainMenu.addMenu('Help')
        manualAct=QAction("Open PDF Manual",self)
        helpMenu.addAction(manualAct)
        aboutAct=QAction("About",self)
        aboutAct.triggered.connect(self.simpleDialog)
        helpMenu.addAction(aboutAct)
        
        
        self.showMaximized()   
