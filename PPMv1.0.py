#Title: PPMv1.0 (beta) 
#Author: Francisco Gonzalez-Martinez
#Date: 5/23/2019

#This is a program for the PPM with a basic GUI
#This program place the image captured by the camera Thorlabs DCC1545M
#Part of this program was made taking code from https://stackoverflow.com/questions/44404349/pyqt-showing-video-stream-from-opencv
#Part of this program was made taking code from https://github.com/pyqt/examples/blob/master/widgets/sliders.py
#The GUI is located in the library ppmgui.py
#The controls for the camera are located in the library camdcx



class nativeCamera():
    def __init__(self,name,index):
        self.name=name
        self.index=index
        self.cam=cv2.VideoCapture(self.index)
    
#Function for detect the cameras conected----
def detectCameras(camera):
    valid_cameras=[]
    
    if camera.open(8, (1280, 1024), (0,0), "Thorlabs", 30,1) is True:
        valid_cameras.append(camera)

    for i in range (2):
        cap=nativeCamera("nativeCam{}".format(i),i)
        if cap is None or not cap.cam.isOpened():
            None
        else:
            valid_cameras.append(cap)
       
        cap.cam.release()            
    cv2.destroyAllWindows()
    return valid_cameras 
    

    
def main(args):
    try:         
        version="1.0"        
        
        camThLabs=camdcx.Camera()   
        Ndef=10       
        mem=[]
        
        cameras=detectCameras(camThLabs) 
        app = ppmgui.QApplication(sys.argv)
        ex = ppmgui.App(cameras,Ndef)
        ex.show()       
        welcome=ppmgui.dialog()
        welcome.createWelcomeDialog("ppm","Welcome to PPM v%s"%version)
        
        #check if there is a camera Thorlabs connected
        c=0
        for x in cameras:
            if str(type(x))=="<class 'camdcx.Camera'>":
                c+=1
        #if there is a camera Thorlabs connected initialize it and make it the default camera        
        if c==1:
            camThLabs.set_external_trigger()    
            n=1
            while True:
                mem.append(camThLabs.initialize_memory())
                camThLabs.add_to_sequence(mem[n-1][0],mem[n-1][1])
                n+=1
                if n>Ndef:
                    #print(mem)
                    break
                    
            live=ppmgui.live(camThLabs,mem)
            live.livestream.connect(ex.setImage)
            live.liveproces.connect(ex.setImage2)
            ex.colMap.connect(live.changeColorMap)
            live.start()
                
        sys.exit(app.exec_())
    finally:
        camThLabs.close()
  

if __name__ == '__main__':
    ###-------Importing usefull libraries
    
    import sys
    import cv2
    import numpy as np
    import os.path
    import time
    import collections as coll
    from ctypes import *
    import camdcx
    import threading
    import logging
    import ppmgui
    import queue
    
    main(sys.argv[1:])
    
    
    