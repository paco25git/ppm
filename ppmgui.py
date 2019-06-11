#Title: ppmgui.py 
#Author: Francisco Gonzalez-Martinez
#Date: 5/23/2019

#This is a library for making the GUI to the PPM device

#---------importing libraries
import sys
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import (QMainWindow, QApplication, QAction, QLabel, QGridLayout, QGroupBox, QSpinBox,QStyle,QStackedWidget,
 QWidget, QVBoxLayout,QHBoxLayout, QSlider, QDialog, QPushButton, QMdiSubWindow, QTextEdit,QMdiArea,QBoxLayout,QComboBox)
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import QSize, QThread, pyqtSignal, pyqtSlot, Qt
import time
import cv2
import numpy as np
from ctypes import *
#import threading

def do_processing(memory):
    imgs=[]
    for i in range(len(memory)):
        imgs.append(np.frombuffer(memory[i][0], c_ubyte))
    sd=np.std(imgs,axis=0)
    mn=np.mean(imgs,axis=0)
    res2=sd/mn
    return res2

#a class for making a thread that handles the camera capture
class live(QThread):
    livestream = pyqtSignal(QImage)
    liveproces = pyqtSignal(QImage)
    
    def __init__(self,camera, mem, ppImg):
        super(live,self).__init__(parent=None)
        self.camera=camera
        self.mem=mem        
        self.colormap="jet"
        self.ppImg2=ppImg
               
    def run(self):    
        while True:		
            self.n=1
            while True:
                self.camera.freeze_video()
                time.sleep(.1)
                arr=self.camera.get_image_v2(self.mem[self.n-1][0])
                self.n+=1
                rgbImage = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
                h, w,ch= rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QtGui.QImage(rgbImage.data, w, h,bytesPerLine, QtGui.QImage.Format_RGB888)
                p = convertToQtFormat.scaled(1353, 1233,QtCore.Qt.KeepAspectRatio)
                self.livestream.emit(p)
                if self.n>len(self.mem):
                    break
                    
            self.ppImg=do_processing(self.mem).reshape(1024,1280)
            self.ppImg*=3000 
            #self.ppImg+=60
            
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
            
    def createWindowManageCamera(self, current):
        self.current=current
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
        
    def createLSIProcessingOptions(self,Ndef,current):
        self.current=current
        self.setWindowTitle("LSI Processing options")      
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.resize(700,400)
        
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
        self.wsVal.setRange(1,30)
        self.wsVal.setSingleStep(1)
        self.wsVal.setValue(Ndef)
        self.wsVal.setMaximumWidth(80)
        self.wsUL=QLabel("[frames]")
        self.timeBoxL.addWidget(self.tBL)
        self.timeBoxL.addWidget(self.wsVal)
        self.timeBoxL.addWidget(self.wsUL)
        self.timeBox.setLayout(self.timeBoxL)
        
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
               
class histo(QWidget):
    def __init__(self):
        super(histo,self).__init__(parent=None)
        
    def keyPressEvent(self, e):  
        if e.key() == QtCore.Qt.Key_Escape:
            
            self.close()
            
    def closeEvent(self, event):
        print ("User has clicked the red x on the main window")
        event.accept()
        
    def createHistSubW(self):
        self.setWindowTitle("Histogram tool")      
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.resize(1200,400)
           
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
    def __init__(self,cameras,Ndef,eve):
        super(App,self).__init__()
        self.eve=eve
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)
        self.title="Portable perfusion monitor"
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
        self.cameras=cameras
        self.currentCam=self.cameras[0]
        self.Ndef=Ndef
        self.colorMaps=["jet","hot","aut","bone"]
        self.colorMap=self.colorMaps[0]
        self.initUI()
        
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
        self.mySubwindow.createWindowManageCamera(self.currentCam)
        self.mySubwindow.show()
        
    def createASubwindow2(self):
        self.procOpt=subwindow()
        self.procOpt.createLSIProcessingOptions(self.Ndef,self.currentCam)
        self.procOpt.show()
        
    def selectedCameraThorlabs(self): 
        self.currentCam=self.cameras[0]
        self.camThorlabsAct.setFont(self.fBond)
        
        for i in self.cameras:
            if i.name=="Thorlabs":
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
        
    @pyqtSlot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))
        
    @pyqtSlot(QImage)
    def setImage2(self, image):
        self.label2.setPixmap(QPixmap.fromImage(image))
        
        
    def createHistogram(self):
        self.histFlag=True
        self.eve.set()
        """
        self.histSubW=histo()
        self.histSubW.createHistSubW()
        self.histSubW.show()
        """
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height) 
        self.histFlag=False
        
        self.label = QLabel(self)
        self.label.move(10, 120)
        self.label.resize(1353, 1233)
        
        self.label2 = QLabel(self)
        self.label2.move(1363,120)
        self.label2.resize(1353,1233) 
               
        
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
        editMenu = mainMenu.addMenu('Edit')
        selCam=editMenu.addMenu("Select camera")
        
        self.fBond=QtGui.QFont()
        self.fBond.setBold(True)
        
        self.fNBond=QtGui.QFont()
        self.fNBond.setBold(False)
        
        for i in self.cameras:
            exec('self.cam{}Act=QAction("Camera {}",self)'.format(i.name,i.name))
            exec('self.cam{}Act.triggered.connect(self.selectedCamera{})'.format(i.name,i.name))
            exec('selCam.addAction(self.cam{}Act)'.format(i.name))
        exec('self.cam{}Act.setFont(self.fBond)'.format(self.cameras[0].name))
                
        mcAct=QAction("Manage Camera",self)
        mcAct.triggered.connect(self.createASubwindow)
        mcAct.setShortcut("Ctrl+M")             
        editMenu.addAction(mcAct)        
        
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
        
        #SEARCH---
        searchMenu = mainMenu.addMenu('Search')
        
        #TOOLS----
        toolsMenu = mainMenu.addMenu('Tools')
        poAct=toolsMenu.addMenu("Processing options")
        lsiM=QAction("LSI options",self)
        lsiM.triggered.connect(self.createASubwindow2)
        poAct.addAction(lsiM)
        histAct=QAction("Show histogram",self)
        histAct.triggered.connect(self.createHistogram)
        toolsMenu.addAction(histAct)
        
        #HELP-----
        helpMenu = mainMenu.addMenu('Help')
        manualAct=QAction("Open PDF Manual",self)
        helpMenu.addAction(manualAct)
        aboutAct=QAction("About",self)
        aboutAct.triggered.connect(self.simpleDialog)
        helpMenu.addAction(aboutAct)
        
        
        self.showMaximized()   
