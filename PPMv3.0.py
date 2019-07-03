#Title: PPMv3.0 (beta) 
#Author: Francisco Gonzalez-Martinez
#Date: 6/28/2019

#This is a program for the PPM with a basic GUI
#This program place the image captured by the camera Thorlabs DCC1545M
#Part of this program was made taking code from https://stackoverflow.com/questions/44404349/pyqt-showing-video-stream-from-opencv
#Part of this program was made taking code from https://github.com/pyqt/examples/blob/master/widgets/sliders.py
#The GUI is located in the library ppmgui.py
#The controls for the camera are located in the library camdcx

###-------Importing usefull libraries-----#    
import sys
import os.path
import time
import numpy as np
import cv2 
from matplotlib import pyplot as plt
import camdcx    #Library for thorlabs camera functions
import camjai    #Library for jai camera functions
import ppmgui    #graphical user interface defined in this file
import threading 
from events import Events
import logging
import queue
from PIL import Image
from configparser import RawConfigParser

#---------------------------------------#
#    Error handler                      #
#---------------------------------------#
class Error(Exception):
	def __init__(self, mesg):
		self.mesg=mesg
	def __str__(self):
		return self.mesg
#---------------------------------------#
#     A class for the native cameras    #
#---------------------------------------#
class nativeCamera():
    def __init__(self,name,index):
        self.name=name
        self.index=index
        self.cam=cv2.VideoCapture(self.index)
        self.camType="native"
        self.isOpen=False

    def close(self):
        self.cam.release()
#-----------------------------------------------------#
#  Defining a class for the list of connected cameras #
#-----------------------------------------------------#
class camerasConnected(list):
    def __init__(self):
        self.active=None
        self.length=None
        
    #---------------------------------------#
    # Function for detect cameras connected #
    #---------------------------------------#
    #Camera detection function works for native cameras, thorlabs and JAI cameras
    def detectCameras(self):
        #Looking for Thorlabs cameras
        listTh=camdcx.list_cameras_connected()
        if listTh:
            for i in listTh:
                cap=camdcx.Camera(i)
                self.append(cap)
        
        #Looking for JAI cameras
        listjai=camjai.update_camera_list("FD")
        if listjai:
            for i in listjai:
                cap=camjai.Camera(i)
                self.append(cap)

        #Looking for native cameras
        for i in range (2):
            cap=nativeCamera("nativeCam{}".format(i),i)
            if cap is None or not cap.cam.isOpened():
                None
            else:
                self.append(cap)
            cap.cam.release()
        cv2.destroyAllWindows()
        
        self.length=len(self)
        return self
    #-------------------------------------------#
    # Function for set the active camera        #
    #-------------------------------------------#
    def set_active(self,index):
        if self>0:
            if index in range(0,len(self)):
                self.active=index
                return True
            else:
                print("set_active() Error: index out of limits of valid cameras")
                return False
        else: 
            print("set_active() Error: valid cameras list empty")
            return False

#-------------------------------------------#
# LSI processing thread                     #
#-------------------------------------------#
class LSI(threading.Thread):
    def __init__(self,imqueue,window=5,app=None):
        threading.Thread.__init__(self)
        self.threadname='LSI processing'
        self.imqueue=imqueue
        self.window=window
        self.can_run=threading.Event()
        self.thing_done=threading.Event()
        self.end_thread=threading.Event()
        self.thing_done.set()
        self.can_run.set()
        self.end_thread.clear()
        self.daemon=True
        self.app=app
        self.k=1
        self.maxSD=0.1
        
    def run(self):
        print("LSI processing thread started")
        while True:
            self.can_run.wait()
            try:
                self.thing_done.clear()
                if self.imqueue.qsize()>self.window:
                    imgs=[]
                    for i in range(self.window):
                        imgs.append(self.imqueue.get())
                    sd=np.std(imgs,axis=0,dtype=np.float64, ddof=1)
                    mn=np.mean(imgs,axis=0,dtype=np.float64)
                    res2=np.divide(sd,mn,dtype=np.float64)
                    res2*=self.k
                    self.maxI=np.amax(res2)
                    #res2=np.uint8(self.maxI*255)

                    #res2/=self.maxSD
                    #res2/=self.maxI
                    #res2*=255
                    res2=np.floor(res2)
                    np.clip(res2,0,255,out=res2)
                    if self.app:
                        self.app.setImage2(res2.astype(np.uint8))
                        
            finally:
                self.thing_done.set()
                if self.end_thread.is_set():
                    break
        print("Thread : %s stoped"%self.threadname)

    def set_gui(self,app):
        self.app=app

    def change_window(self,winVal):
        self.window=winVal

    def change_k(self,gan):
        self.k=gan

    def changeMaxSD(self,maxsd):
        self.maxSD=maxsd

    def pause(self):
        self.can_run.clear()
        self.thing_done.wait()

    def resume(self):
        self.can_run.set()

    def stopThread(self):
        self.end_thread.set()

#-------------------------------------------#
#               Main Function               #
#-------------------------------------------#
def main(args):
    try:
        #________loading initial configurations____________#
                
        config_file="config.cfg" #Initial default config settings located in config.cfg
        last_config="lastConfig.cfg" #Saved values in the last running
        temp=RawConfigParser()   #Creating the data structure for locate the config data
        if not os.path.isfile(last_config):
            if not os.path.isfile(config_file):  #Check if config file is on folder
                raise Error("Error: missing config.cfg file in folder")
            else:
                with open(config_file, 'r') as f: #Read the config.cfg file
                    temp.read_file(f)
        else:
            with open(last_config, 'r') as f: #Read the last values cfg file
                temp.read_file(f)

        #________defining some variables___________________#
        
        imQueue=queue.Queue()  #Queue for locate images from camera
        version="3.0"          #Version of this file

        #________find connected cameras____________________#

        camdcx.load_library() #Before use the camdcx functions must load DLL library
        camjai.load_library() #Before use the camjai functions must load DLL library
        cameras=camerasConnected() #Creating an object for save the cameras conected
        cameras.detectCameras() #Update the list cameras connected
        if cameras.length==0:
            empty=True   #just a flag for check if there is cameras connected

        #________find if the prefered camera is connected and get the index____#

        finx=None #variable for save the index in the cameras list
        for i in range(cameras.length):
            if cameras[i].camType==temp.get('main','preferedCamera'):
                finx=i  #save the index of the first camera founded
                break
        if finx!=None:
            print("%s camera found in cameras index %d"%(temp.get('main','preferedCamera'),finx))
            cameras.set_active(finx)!=True #setting the camera founded as the active
        else:
            cameras.set_active(0) #setting the first camera 

        lsiThread=LSI(imQueue)  #thread for lsi processing
        #_________create the GUI_____________#

        app = ppmgui.QApplication(sys.argv)
        screen = app.primaryScreen()       
        ex = ppmgui.App(screen,cameras,lsiThread,temp)
        ex.show()       
        welcome=ppmgui.dialog()
        welcome.createWelcomeDialog("ppm","Welcome to PPM v%s"%version)
        lsiThread.set_gui(ex)

        #_________create camera streams threads_____________#

        for i in cameras:  #find cameras types and create threads for that connected 
            if i.camType=='ThorlabsCam':
                streamTh=threading.Thread(target=i.stream_thread,args=(imQueue,ex),daemon=True)  #create thread for tholabs camera
                break

        for i in cameras:  #find cameras types and create threads for that connected 
            if i.camType=='JaiCam':
                streamJai=threading.Thread(target=i.stream_thread,args=(imQueue,ex),daemon=True)   #create thread for tholabs camera
                break

    finally:
        print(cameras)
        for i in cameras:
            if i.isOpen==True:
                i.close()

if __name__ == '__main__':
    main(sys.argv[1:])

        

