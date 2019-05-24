#Title: PPMv1.0 (beta) 
#Author: Francisco Gonzalez-Martinez
#Date: 5/23/2019

#This is a program for the PPM with a basic GUI
#This program place the image captured by the camera Thorlabs DCC1545M
#Part of this program was made taking code from https://stackoverflow.com/questions/44404349/pyqt-showing-video-stream-from-opencv
#Part of this program was made taking code from https://github.com/pyqt/examples/blob/master/widgets/sliders.py
#The GUI is located in the library ppmgui.py

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

if __name__ == '__main__':
    app = ppmgui.QApplication(sys.argv)
    ex = ppmgui.App()
    ex.show()
    sys.exit(app.exec_())
