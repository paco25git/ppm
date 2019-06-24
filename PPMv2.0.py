#Title: PPMv2.0 (beta) 
#Author: Francisco Gonzalez-Martinez
#Date: 6/8/2019

#This is a program for the PPM with a basic GUI
#This program place the image captured by the camera Thorlabs DCC1545M
#Part of this program was made taking code from https://stackoverflow.com/questions/44404349/pyqt-showing-video-stream-from-opencv
#Part of this program was made taking code from https://github.com/pyqt/examples/blob/master/widgets/sliders.py
#The GUI is located in the library ppmgui.py
#The controls for the camera are located in the library camdcx

###-------Importing usefull libraries    
import sys
import cv2
from matplotlib import pyplot as plt
import numpy as np
import os.path
import time
#import collections as coll
#from ctypes import *
import camdcx
import camjai
import threading 
import logging
import ppmgui
import queue
from events import Events
from PIL import Image

class nativeCamera():
    def __init__(self,name,index):
        self.name=name
        self.index=index
        self.cam=cv2.VideoCapture(self.index)
        self.camType="native"

    def close(self):
        self.cam.release()

#Function for detect the cameras conected----
#Include native cameras, Thorlabs camera and JAI camera
def detectCameras():
    valid_cameras=[]
    #Looking for Thorlabs cameras
    if thDLL==True:
        lTh=camdcx.list_cameras_connected()
        if not lTh:
            pass
        else:
            for i in lTh:
                cap=camdcx.Camera(i)
                valid_cameras.append(cap)

    #Looking for JAI cameras
    if jaiDLL==True:
        ljai=camjai.update_camera_list("FD")
        if not ljai:
            pass
        else:
            for i in ljai:
                cap=camjai.Camera(i)
                valid_cameras.append(cap)

    #Looking for native cameras
    for i in range (2):
        cap=nativeCamera("nativeCam{}".format(i),i)
        if cap is None or not cap.cam.isOpened():
            None
        else:
            valid_cameras.append(cap)
        cap.cam.release()   

    cv2.destroyAllWindows()
    
    return valid_cameras

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
                    res2=sd/mn
                    #res2 = map(lambda x: x * self.k, res2)
                    res2*=self.k
                    #self.maxI=np.amax(res2)
                    #res2=np.uint8(self.maxI*255)

                    #res2/=self.maxSD
                    #res2/=self.maxI
                    #res2*=255
                    np.clip(res2,0,255,out=res2)
                    if self.app:
                        #imagen=Image.fromarray(res2,'L')
                        #print(res2)
                        self.app.setImage2(res2.astype(np.uint8))
                    #res3=cv2.applyColorMap(res2.astype(np.uint8), cv2.COLORMAP_JET)
                    #cv2.imshow('image',res3)
                    #cv2.waitKey(1)
                #print(self.imqueue.qsize())
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

class dataLSI(object):
    def __init__(self,start=np.zeros((1024,1280)).astype(np.uint8)):
        self.lock=threading.Lock()
        self.value=start       

    def calc_hist(self,eve):
        self.eve=eve
        self.hist=cv2.calcHist([self.value],[0],None,[256],[0,256])
        plt.plot(self.hist,color='b')
        plt.xlim([0,256])
        plt.draw()
        plt.pause(0.0001)
        plt.clf()
        #if not plt.fignum_exists("Figure 1"):
         #   self.eve.clear()
        #plt.show()


def histogram_calc(img,threadname='Histo'):
    logging.info("Thread %s: starting", threadname)
    while True:
        logging.info("Thread %s: waiting", threadname)
        eve.wait()
        while eve.isSet():
            #logging.info("Thread %s: working", threadname)
            img.calc_hist(eve)
            
    logging.info("Thread %s: finishing", threadname)

def main(args): 
    try:
        imQueue=queue.Queue()
        global eve
        eve = threading.Event()
        format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=format, level=logging.INFO,datefmt="%H:%M:%S")

        version="2.0"
        #open the Thorlabs camera dll file
        global thDLL
        thDLL=camdcx.load_library()
        global jaiDLL
        jaiDLL=camjai.load_library()
        Ndef=5        
        cameras=detectCameras()
        #Open the first camera in the list (if Thorlabs connected will be the first one)
        if len(cameras)>=1:
            if cameras[0].camType=='ThorlabsCam':
                cameras[0].open()
                mem=cameras[0].create_sequence(Ndef)
                handleEvent=cameras[0].init_event()
                cameras[0].enable_event()
                cameras[0].start_continuous_capture()
            elif cameras[0].camType=='JaiCam':
                pass
        #Create histogram thread
        img=dataLSI()
        hisThread = threading.Thread(target=histogram_calc, args=(img,), daemon=True)
        hisThread.start()
        
        #Create LSI thread
        lsiThread=LSI(imQueue)
        #Create GUI
        app = ppmgui.QApplication(sys.argv)
        screen = app.primaryScreen()       
        ex = ppmgui.App(screen,cameras,Ndef,eve,lsiThread)
        ex.show()       
        welcome=ppmgui.dialog()
        welcome.createWelcomeDialog("ppm","Welcome to PPM v%s"%version)
        """
        #Place captured image
        live=ppmgui.live(cameras[0],mem,img,handleEvent)
        live.livestream.connect(ex.setImage)
        live.liveproces.connect(ex.setImage2)
        ex.colMap.connect(live.changeColorMap)
        live.start()
        """
        lsiThread.set_gui(ex)
        #Create stream thread
        streamTh=threading.Thread(target=cameras[0].stream_thread,args=(imQueue,ex,),daemon=True)
        streamTh.start()
        lsiThread.start()
        sys.exit(app.exec_())

    finally:
        
        for i in cameras:
            i.close()
        lsiThread.stopThread()
        print("END")

if __name__ == '__main__':
    main(sys.argv[1:])
