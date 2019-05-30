#Title: PPMv1.0 (beta) 
#Author: Francisco Gonzalez-Martinez
#Date: 5/23/2019

#This is a program for the PPM with a basic GUI
#This program place the image captured by the camera Thorlabs DCC1545M
#Part of this program was made taking code from https://stackoverflow.com/questions/44404349/pyqt-showing-video-stream-from-opencv
#Part of this program was made taking code from https://github.com/pyqt/examples/blob/master/widgets/sliders.py
#The GUI is located in the library ppmgui.py
#The controls for the camera are located in the library camdcx

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

def detectCameras(camera):
    valid_cameras=[]
    
    if camera.open(8, (1280, 1024), (0,0), "ThorCam FS", 30,1) is True:
        valid_cameras.append("Thorlabs")
        #camera.close()
    else:
        None

    for i in range (2):
        cap=cv2.VideoCapture(i)
        if cap is None or not cap.isOpened():
            None
        else:
            valid_cameras.append(i)
    cap.release()            
    cv2.destroyAllWindows()
    return valid_cameras 
    
def main(args):
    try: 
        camThLabs=camdcx.Camera()
        Ndef=5
        n=1
        mem=[]
        cameras=detectCameras(camThLabs)
        
        while True:
            mem.append(camThLabs.initialize_memory())
            camThLabs.add_to_sequence(mem[n-1][0],mem[n-1][1])
            n+=1
            if n>Ndef:
                #print(mem)
                break
            
        version="1.0"
        app = ppmgui.QApplication(sys.argv)
        ex = ppmgui.App(cameras,Ndef)
        live=ppmgui.live(camThLabs,mem)
        live.livestream.connect(ex.setImage)
        live.start()
        ex.show()
        
        welcome=ppmgui.dialog()
        welcome.createWelcomeDialog("ppm","Welcome to PPM v%s"%version)
        
        
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
    
    
    