#Title: ppmgui.py 
#Author: Francisco Gonzalez-Martinez
#Date: 5/23/2019

#This is a library for making the GUI to the PPM device

#---------importing libraries
import sys
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import (QMainWindow, QApplication, QAction, QLabel, QGridLayout, QGroupBox, QSpinBox,
 QWidget, QVBoxLayout,QHBoxLayout, QSlider, QDialog, QPushButton, QMdiSubWindow, QTextEdit,QMdiArea,QBoxLayout)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QSize, QThread, pyqtSignal, pyqtSlot, Qt

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

        self.expBox=QGroupBox("Exposure",self)
        self.expV=QVBoxLayout()
        self.expH=QHBoxLayout()

        self.expL=QLabel("Current value: ")
        self.expU=QLabel(" [ms]")
        self.expVal=QSpinBox()
        self.expVal.setRange(1,100)
        self.expVal.setSingleStep(1)
        self.expSlider=QSlider(Qt.Horizontal)
        self.expSlider.setFocusPolicy(Qt.StrongFocus)
        self.expSlider.setTickPosition(QSlider.TicksBothSides)
        self.expSlider.setTickInterval(10)
        self.expSlider.setSingleStep(1)

        self.expH.addStretch(1)
        self.expH.addWidget(self.expL)
        self.expH.addWidget(self.expVal)
        self.expH.addWidget(self.expU)
        #self.setLayout(self.expH)
        self.expV.addLayout(self.expH)
        self.expV.addWidget(self.expSlider)
             
        
        self.expBox.setLayout(self.expV)
       
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
        self.box=QGroupBox("",self)
        self.box.resize(600,300)
        mess=QLabel("This is a message")
        okB=QPushButton("ok")
        #okB.move(290,300)
        self.dialogLayout=QGridLayout()
        self.dialogLayout.addWidget(mess,0,0)
        self.dialogLayout.addWidget(okB,3,1,1,3)
        self.box.setLayout(self.dialogLayout)
        self.exec_()

class App(QMainWindow):
    count=0
    def __init__(self):
        super().__init__()
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)
        self.title="Portable perfusion monitor"
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
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
        sub.setWindowTitle("subwindow"+str(App.count))
        self.mdi.addSubWindow(sub)
        

    def simpleDialog(self):
        self.myDialog=dialog()
        self.myDialog.createAboutDialog("About this program")
           
    def createASubwindow(self):
        
        self.mySubwindow=subwindow()
        self.mySubwindow.createWindowManageCamera()
        
        
        self.mySubwindow.show()
        
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
        #HELP----
        helpMenu = mainMenu.addMenu('Help')
        aboutAct=QAction("About",self)
        aboutAct.triggered.connect(self.simpleDialog)
        helpMenu.addAction(aboutAct)
        
        self.showMaximized()   
