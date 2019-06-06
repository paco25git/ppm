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
            self.name=None
            self.Id=None
            self.driver=None
            self.camHandle=None
            self.jaifactory=cdll.LoadLibrary(jai_file)
            self.hFactory=c_int() 
            self.retval=self.jaifactory.J_Factory_Open("",byref(self.hFactory)) #handle self.hFactory obtained with J_Factory_Open function
            if self.retval==0: # 0 value defined as J_ST_SUCCESS in Jai_Error.h (refer this file for more defines)
                print("Jai factory SDK open correct")
            else:
                raise CameraOpenError("Couldn't open JAI sdk functions")                
        else:
            raise CameraOpenError("Jai_Factory.dll file is missing")
            
    def update_camera_list(self,driver):
        self.driver="INT=>"+driver  #Use "INT=>SD" or "INT=>FD"
        self.bhasChanged=c_bool(True)   
        self.nCameras=c_int()
        self.retval=self.jaifactory.J_Factory_UpdateCameraList(self.hFactory,byref(self.bhasChanged))
        self.sCameradId=(c_char*512)(0)
        self.sizeId=c_int(len(self.sCameradId))
        
        if self.retval==0 and self.bhasChanged.value==True:
            print("Camera conected")
            """
            Get the number of cameras. This number can be larger than the actual camera count 
            because the cameras can be detected through different driver types! 
            This mean that we might need to filter the cameras in order to avoid dublicate 
            references.
            """
            self.retval=self.jaifactory.J_Factory_GetNumOfCameras(self.hFactory, byref(self.nCameras))
           
            if self.retval==0 and self.nCameras.value>0:
                print("%d cameras have been found \nCameras List: \n"%self.nCameras.value)
                self.listCameras={}
                #Run through the list of found cameras
                for i in range(self.nCameras.value):
                    #Get camera ID
                    self.sizeId=c_int(len(self.sCameradId))
                    self.retval=self.jaifactory.J_Factory_GetCameraIDByIndex(self.hFactory,i,self.sCameradId,byref(self.sizeId))
                    if self.retval==0:
                        print("Camera %d =%s"%(i,self.sCameradId.value))
                        if str(self.sCameradId.value).find(self.driver)!=-1:                            
                            self.camHTemp=c_void_p(i)
                            self.listCameras[self.sCameradId.value]=self.camHTemp                        
                    else:
                        print(self.retval)
                return self.listCameras
        else:
            print("No camera conected")
    
    def open(self,Id,camHand):
        self.camHandle=camHand
        self.Id=Id
        self.name=str(self.Id)[-12:]
myCam=Camera()
cameras=myCam.update_camera_list("SD")

print(list(cameras.keys())[1])


