#Title: camjai.py
#Author:Francisco Gonzalez-Martinez
#Date:06/04/2019

#This is a library for handle the JAI camera: model AD-080GE

import os.path
from ctypes import *
#import numpy as np

class CameraOpenError(Exception):
    def __init__(self,mesg):
        self.mesg=mesg
    def __str__(self):
        return self.mesg

class Camera(object):
    def __init__(self):
        jai_file=os.path.dirname(os.path.realpath(__file__))+'\includesJAI\Jai_Factory.dll'
        if os.path.isfile(jai_file):
            self.handle=None
            self.jaifactory=cdll.LoadLibrary(jai_file)
        else:
            raise CameraOpenError("Jai_Factory.dll file is missing")
            
    def open(self,name):
        self.name=name
        self.handle=c_int(0)
        self.jaifactory.J_Factory_UpdateCameraList(self.handle)
        


