#Title: ppmgui.py 
#Author: Francisco Gonzalez-Martinez
#Date: 5/23/2019

#This is a library for making the GUI to the PPM device

#---------importing libraries
import sys
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import (QMainWindow, QApplication, QAction, QLabel, QGridLayout, QGroupBox, QSpinBox,QStyle,
 QWidget, QVBoxLayout,QHBoxLayout, QSlider, QDialog, QPushButton, QMdiSubWindow, QTextEdit,QMdiArea,QBoxLayout)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QSize, QThread, pyqtSignal, pyqtSlot, Qt
import time

#a class for making a thread that handles the camera capture
#class live(QThread, camera):

    

#a class for making subWindows outside from the main window
class subwindow(QWidget):
    valueChanged = pyqtSignal(int)
    def __init__(self):
        super(subwindow,self).__init__(parent=None)
          
    def keyPressEvent(self, e):  
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
                        
    def createWindowManageCamera(self):
        
        self.setWindowTitle("Manage Camera")      
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.resize(700,400)
        
        self.genLayout=QVBoxLayout()
        
        self.capBox=QGroupBox("Capture",self)
        self.capBoxLayout=QHBoxLayout()
        
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
        self.genLayout.addWidget(self.capBox)
        self.genLayout.addWidget(self.expBox)
        self.setLayout(self.genLayout)
        
        
    def changeExp(self):
        print("value changed")
        
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
    def __init__(self,cameras):
        super(App,self).__init__()
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)
        self.title="Portable perfusion monitor"
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
        self.cameras=cameras
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
        self.mySubwindow.createWindowManageCamera()
        
        
        self.mySubwindow.show()
        
    def selectedCamera0(self):        
        print("camera0")
    def selectedCamera1(self):        
        print("camera1")
    def selectedCamera2(self):        
        print("camera2")    
    def selectedCamera3(self):        
        print("camera3")    
        
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height) 
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
        
        for i in self.cameras:
            exec('cam{}Act=QAction("Camera {}",self)'.format(i,i))
            exec('cam{}Act.triggered.connect(self.selectedCamera{})'.format(i,i))
            exec('selCam.addAction(cam{}Act)'.format(i))
            
            
        mcAct=QAction("Manage Camera",self)
        mcAct.triggered.connect(self.createASubwindow)
        mcAct.setShortcut("Ctrl+M")             
        editMenu.addAction(mcAct)        
        
        #VIEW-----
        viewMenu = mainMenu.addMenu('View')
        newWAct=QAction("New Window",self)
        newWAct.triggered.connect(self.newWindowMDI)
        viewMenu.addAction(newWAct)
        
        #SEARCH---
        searchMenu = mainMenu.addMenu('Search')
        toolsMenu = mainMenu.addMenu('Tools')
        
        #HELP-----
        helpMenu = mainMenu.addMenu('Help')
        manualAct=QAction("Open PDF Manual",self)
        helpMenu.addAction(manualAct)
        aboutAct=QAction("About",self)
        aboutAct.triggered.connect(self.simpleDialog)
        helpMenu.addAction(aboutAct)
        
        
        self.showMaximized()   
