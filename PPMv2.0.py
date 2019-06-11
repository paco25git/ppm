#Title: PPMv2.0 (beta) 
#Author: Francisco Gonzalez-Martinez
#Date: 6/8/2019

#This is a program for the PPM with a basic GUI
#This program place the image captured by the camera Thorlabs DCC1545M
#Part of this program was made taking code from https://stackoverflow.com/questions/44404349/pyqt-showing-video-stream-from-opencv
#Part of this program was made taking code from https://github.com/pyqt/examples/blob/master/widgets/sliders.py
#The GUI is located in the library ppmgui.py
#The controls for the camera are located in the library camdcx
import numpy as np
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
        #
        #'''
        #

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

class dataLSI(object):
    def __init__(self,start=np.zeros((1024,1280)).astype(np.uint8)):
        self.lock=threading.Lock()
        self.value=start
        

    def calc_hist(self,e):
        self.hist=cv2.calcHist([self.value],[0],None,[256],[0,256])
        plt.plot(self.hist,color='b')
        plt.xlim([0,256])
        
        if plt.fignum_exists("Figure 1"):
            plt.draw()
            plt.pause(0.0001)
            plt.clf()
        else:
            e.clear()
        #plt.show()


def histogram_calc(img,threadname='Histo'):
    logging.info("Thread %s: starting", threadname)
    while True:
        logging.info("Thread %s: waiting", threadname)
        e.wait()
        while e.isSet():
            logging.info("Thread %s: working", threadname)
            img.calc_hist(e)
            
    logging.info("Thread %s: finishing", threadname)

def main(args): 
    try:
        global e
        e = threading.Event()
        format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=format, level=logging.INFO,datefmt="%H:%M:%S")

        version="2.0"
        #open the Thorlabs camera dll file
        global thDLL
        thDLL=camdcx.load_library()
        Ndef=5        
        cameras=detectCameras()
        #Open the first camera in the list (if Thorlabs connected will be the first one)
        if len(cameras)>=1:
            if cameras[0].camType=='ThorlabsCam':
                cameras[0].open()
                mem=camdcx.create_sequence(cameras[0],Ndef)
        #Create histogram thread
        img=dataLSI()
        hisThread = threading.Thread(target=histogram_calc, args=(img,), daemon=True)
        hisThread.start()
        #Create GUI
        app = ppmgui.QApplication(sys.argv)
        ex = ppmgui.App(cameras,Ndef,e)
        ex.show()       
        welcome=ppmgui.dialog()
        welcome.createWelcomeDialog("ppm","Welcome to PPM v%s"%version)
        #Place captured image
        live=ppmgui.live(cameras[0],mem,img)
        live.livestream.connect(ex.setImage)
        live.liveproces.connect(ex.setImage2)
        ex.colMap.connect(live.changeColorMap)
        live.start()

        sys.exit(app.exec_())

    finally:
        for i in cameras:
            i.close()
        print("END")

if __name__ == '__main__':
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
    import threading 
    import logging
    import ppmgui
    #import queue
    from events import Events
    main(sys.argv[1:])

