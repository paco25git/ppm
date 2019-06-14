#Title: camjai.py
#Author:Francisco Gonzalez-Martinez
#Date:06/04/2019

#This is a library for handle the JAI camera: model AD-080GE

#AD-080GE_#0 visible
#AD-080GE_#1 infrared

import os.path
from ctypes import *
import time
import threading
import cv2
import numpy as np
from PIL import Image
import io

jaifactory=None

def load_library():
    global jaifactory
    global hFactory
    hFactory=c_int()
    jai_file=os.path.dirname(os.path.realpath(__file__))+'\\includesJAI\\Jai_Factory.dll'
    if os.path.isfile(jai_file):
        jaifactory=cdll.LoadLibrary(jai_file)
        if jaifactory.J_Factory_Open("",byref(hFactory))==0: #handle self.hFactory obtained with J_Factory_Open function 
            # 0 value defined as J_ST_SUCCESS in Jai_Error.h (refer this file for more defines)
            print("JAI factory SDK opened correct")
        else:
            raise CameraOpenError("Couldn't open JAI sdk functions")
        return True
    else:
        raise CameraOpenError("Jai drivers not available.")

def update_camera_list(driver):
        driver="INT=>"+driver  #Use "INT=>SD" or "INT=>FD"
        bhasChanged=c_bool(True)   
        nCameras=c_int()
        retval=jaifactory.J_Factory_UpdateCameraList(hFactory,byref(bhasChanged))
        sCameradId=(c_char*512)(0)
        sizeId=c_int(len(sCameradId))
        
        if retval==0 and bhasChanged.value==True:
            print("Camera conected")
            """
            Get the number of cameras. This number can be larger than the actual camera count 
            because the cameras can be detected through different driver types! 
            This mean that we might need to filter the cameras in order to avoid dublicate 
            references.
            """
            retval=jaifactory.J_Factory_GetNumOfCameras(hFactory, byref(nCameras))
           
            if retval==0 and nCameras.value>0:
                print("%d cameras have been found" %nCameras.value)
                print("Checking for repited cameras with diferent drivers")
                print("Cameras List: \n")
                listCameras=[]
                #Run through the list of found cameras
                for i in range(nCameras.value):
                    #Get camera ID
                    sizeId=c_int(len(sCameradId))
                    retval=jaifactory.J_Factory_GetCameraIDByIndex(hFactory,i,byref(sCameradId),byref(sizeId))
                    if retval==0:
                        #print("Camera %d =%s"%(i,sCameradId.value))
                        if str(sCameradId.value).find(driver)!=-1: 
                            listCameras.append(sCameradId.value)
                    else:
                        print(retval)
                print("%d cameras verified with the driver: %s"%(len(listCameras),driver))
                return listCameras
        else:
            print("No camera conected")

class CameraOpenError(Exception):
    def __init__(self,mesg):
        self.mesg=mesg
    def __str__(self):
        return self.mesg

class Camera(object):
    def __init__(self):
        if jaifactory==None:
            raise CameraOpenError("Jai_Factory.dll file not open, use load_library() method")
        else:
            self.name=None
            self.Id=None
            self.driver=None
            self.camHandle=None
            self.pDS=None
            #thread variables
            self.can_run=threading.Event()
            self.thing_done=threading.Event()
            self.end_thread=threading.Event()
            self.thing_done.set()
            self.can_run.set()
            self.end_thread.clear()
            
            
    def stream_thread(self,threadname='stream'):
        print("Stream Thread initied")
        self.iResult=None
        self.iSize=c_int()
        self.iQueued=c_ulonglong(0)
        self.waitResult=c_uint()
        self.m_hCondition=c_uint()
        self.iNumImages=c_ulonglong(0) #0 or 0xFFFFFFFFFFFFFFFF for continuous capture.
        self.hEvent=c_void_p()
        """
        class EVENT_NEW_BUFFER_DATA(Structure):
            _fields_=[('BufferHandle',c_void_p),('pUserPointer',c_void_p)]
        #self.eventData=EVENT_NEW_BUFFER_DATA 
        """
        self.eventData=c_void_p()
                   
        #Create condition
        if jaifactory.J_Event_CreateCondition(byref(self.m_hCondition))!=0:
            print("Error creating condition")
            
        #Register event
        if jaifactory.J_DataStream_RegisterEvent(self.pDS,c_int(1),self.m_hCondition,byref(self.hEvent))!=0: #EVENT_NEW_BUFFER=1 defined in GenTL.h
            print("Error registering event")
            
        #Start image aquisition
        self.iAcquisitionFlag=c_uint(0x1) #ACQ_START_NEXT_IMAGE  = 0x1 defined in jai_factory.h
        if jaifactory.J_DataStream_StartAcquisition(self.pDS,self.iAcquisitionFlag,self.iNumImages)!=0:
            print("Error starting acquisition")
            #self.m_bStreamStarted = True
        #Loop of stream processing
        self.iTimeout=c_uint(2000)
        while True:
            self.can_run.wait() #Wait 
            try:
                self.thing_done.clear() #Flag for starting task
                stat=jaifactory.J_Event_WaitForCondition(self.m_hCondition,self.iTimeout,byref(self.waitResult))
                if stat==0:
                    #print("wait result = %d"%self.waitResult.value)
                    if self.waitResult.value==1: #(J_COND_WAIT_SIGNAL == WaitResult)  J_COND_WAIT_SIGNAL=1 <-defined on jai_factory.h
                        #get the buffer handle from the event
                        self.iSize=c_uint(sizeof(self.eventData))
                        if jaifactory.J_Event_GetData(self.hEvent,byref(self.eventData),byref(self.iSize))==0:
                            #print(self.eventData.BufferHandle)
                            #print(self.eventData)
                            #Getting the buffer ID
                            self.infoValue=c_ulonglong(0)
                            self.iSize=c_uint(sizeof(self.eventData))
                            if jaifactory.J_DataStream_GetBufferInfo(self.pDS, self.eventData, c_uint(0), byref(self.infoValue), byref(self.iSize))!=0: #BUFFER_INFO_BASE=0 defined in GenTL.h
                                print("Error getting pointer to the frame buffer")
                                break
                            #Get the effective data size.
                            self.infoValue=c_ulonglong(0)
                            self.iSize=c_uint(sizeof(self.eventData))
                            if jaifactory.J_DataStream_GetBufferInfo(self.pDS, self.eventData, c_uint(1), byref(self.infoValue), byref(self.iSize))!=0: #BUFFER_INFO_SIZE=1 defined in GenTL.h
                                print("Error getting effective data size")
                                break
                            print("Effective data size = %d"%self.infoValue.value)
                            ##Get data from the buffer
                            #arr=np.frombuffer(self.m_pAquBuffer[0], c_ubyte).reshape(768, 1024)
                            arr=np.array(Image.open(io.BytesIO(self.m_pAquBuffer[0][0].value)))
                            cv2.imshow('image', cv2.resize(arr,None,fx=1,fy=1))
                            cv2.waitKey(1)

                            if jaifactory.J_DataStream_QueueBuffer(self.pDS, self.eventData)!=0:
                                print("Error queueing buffer")
                                break
                        else:
                            print("Error getting data from the event") 
                            break
                    elif self.waitResult.value==0:
                        print("waitResult: Timeout")
                        break
                    elif self.waitResult.value==2:
                        print("waitResult: Kill event")
                        break
                    elif self.waitResult.value==-1:
                        print("waitResult: error event")
                        break
                    else:
                        print("Unknown error")
                        break
                else:
                    break
                if self.end_thread.is_set():
                    print("Thread stoped")
                    break
            finally:
                self.thing_done.set() #Task done

        #Unregister new buffer event with acquisition engine
        jaifactory.J_DataStream_UnRegisterEvent(self.pDS, c_int(1))
        jaifactory.J_Event_CloseCondition(self.hEvent) 
        jaifactory.J_Event_ExitCondition(self.m_hCondition) 
        jaifactory.J_DataStream_StopAcquisition(self.pDS, c_int(1)) #ACQ_STOP_FLAG_KILL=1 defined in GenTL.h
        jaifactory.J_DataStream_Close(self.pDS)

    def pauseThread(self):
        self.can_run.clear()
        print("Camera stream thread paused")
        self.thing_done.wait()

    def resumeThread(self):
        print("Camera stream thread resumed")
        self.can_run.set()

    def stopThread(self):
        self.end_thread.set()

    def open(self,Id):
        self.Id=c_char_p(Id)
        self.camHandle=c_int()        
        self.name=str(self.Id.value)[-12:-1]
        self.retval=jaifactory.J_Camera_Open(hFactory,self.Id,byref(self.camHandle),0)
        if self.retval==0:
            print("Camera %s open success"%self.name)
        
    def close(self):
        self.retval=jaifactory.J_Camera_Close(self.camHandle)
        if self.retval==0:
            print("Camera %s closed"%self.name)

    def get_size(self):
        self.camWidth=c_longlong()
        self.camHeight=c_longlong()
        #Get width from the camera
        if jaifactory.J_Camera_GetValueInt64(self.camHandle,c_char_p("Width".encode('utf-8')),byref(self.camWidth))!=0:
            print("Error getting width value from the camera %s"%self.name)
        else:
            print("Sensor (%s) Width = %d"%(self.name,self.camWidth.value))
        #Get Height from the camera
        if jaifactory.J_Camera_GetValueInt64(self.camHandle,c_char_p("Height".encode('utf-8')),byref(self.camHeight))!=0:
            print("Error getting height value from the camera %s"%self.name)
        else:
            print("Sensor (%s) Height = %d"%(self.name,self.camHeight.value))
        return self.camWidth,self.camHeight

    def list_nodes(self):
        self.nFeatureNodes=c_longlong()
        self.hNode=c_void_p()
        self.sNodeName=(c_char*256)(0)
        self.sSubNodeName=(c_char*256)(0)
        self.size=c_uint()
        if jaifactory.J_Camera_GetNumOfSubFeatures(self.camHandle,c_char_p("Root".encode('utf-8')),byref(self.nFeatureNodes))!=0:
            print("Error getting nodes from the camera %s"%self.name)
            return False
        else:
            for i in range(self.nFeatureNodes.value):
                if jaifactory.J_Camera_GetSubFeatureByIndex(self.camHandle,c_char_p("Root".encode('utf-8')),c_uint(i),byref(self.hNode))!=0:
                    print("Error getting nodes from the camera %s"%self.name)
                    return False
                else:
                    self.size=c_uint(sizeof(self.sNodeName))
                    if jaifactory.J_Node_GetName(self.hNode,byref(self.sNodeName),byref(self.size),c_uint(0))!=0:
                        print("Error getting node name from the camera %s"%self.name)
                        return False
                    else:
                        print("Node %d name: %s"%(i,str(self.sNodeName.value)))
                        self.nodeType=c_uint()
                        if jaifactory.J_Node_GetType(self.hNode,byref(self.nodeType))!=0:
                            print("Error getting node type from the camera %s"%self.name)
                            return False
                        else:
                            if self.nodeType.value==101: #J_ICategory=101 defined in jai_factory.h
                                self.nSubFeaturesNodes=c_uint()
                                if jaifactory.J_Camera_GetNumOfSubFeatures(self.camHandle,self.sNodeName,byref(self.nSubFeaturesNodes))!=0:
                                    print("Error getting subnode number from the camera %s"%self.name)
                                else:
                                    if self.nSubFeaturesNodes.value>0:
                                        print("%d subFeature node were found"%self.nSubFeaturesNodes.value)
                                        for j in range(self.nSubFeaturesNodes.value):
                                            self.hSubNode=c_void_p()
                                            if jaifactory.J_Camera_GetSubFeatureByIndex(self.camHandle,self.sNodeName,c_uint(j),byref(self.hSubNode))!=0:
                                                print("Error getting subnode name from the camera %s"%self.name)
                                                return False
                                            else:
                                                self.size=c_uint(sizeof(self.sSubNodeName))
                                                if jaifactory.J_Node_GetName(self.hSubNode,self.sSubNodeName,byref(self.size),c_uint(0))!=0:
                                                    print("Error getting node name from the camera %s"%self.name)
                                                    return False
                                                if jaifactory.J_Node_GetType(self.hSubNode,byref(self.nodeType))!=0:
                                                    print("Error getting node type from the camera %s"%self.name)
                                                    return False
                                                else:
                                                    print("    Node %d.%d name: %s, type: %d"%(i,j,str(self.sSubNodeName.value),self.nodeType.value))
        
    def get_pixel_format(self):
        self.pixelFormat=c_longlong()
        if jaifactory.J_Camera_GetValueInt64(self.camHandle,c_char_p("PixelFormat".encode('utf-8')),byref(self.pixelFormat))!=0:
            print("Error getting pixel format value from the camera %s"%self.name)
            return False
        else:
            print("Pixel Format = %d"%self.pixelFormat.value)
            return self.pixelFormat.value
        #35127316=24 Bit RGB Color
        #17301505=8 Bit Monochrome

    def prepare_buffers(self,bufferCount=1, bufferSize=1024*768, pPrivateData=c_void_p()):
        self.pPrivateData=pPrivateData
        self.m_iValidBuffers=0
        self.m_pAquBuffer=[]
        self.m_pAquBufferID=[]
        self.pNum=c_uint()
        self.pDS=c_void_p()
        #Get number of data streams
        if jaifactory.J_Camera_GetNumOfDataStreams(self.camHandle,byref(self.pNum))==0:
            print(self.pNum)
            #Create data stream
            if jaifactory.J_Camera_CreateDataStream(self.camHandle,c_uint(0), byref(self.pDS))==0:
                
                for i in range(bufferCount):
                    self.m_pAquBuffer.append((c_ubyte*bufferSize*3)())
                    self.m_pAquBufferID.append(c_void_p())
                    print("Creating buffer %d = %s"%(i,self.m_pAquBuffer[i]))
                    #Announce the buffer pointer to the Acquisition engine
                    if jaifactory.J_DataStream_AnnounceBuffer(self.pDS,self.m_pAquBuffer[i],bufferSize,self.pPrivateData,byref(self.m_pAquBufferID[i]))!=0:
                        del self.m_pAquBuffer[i]
                        break
                    else:
                        print("Sucessfully announced, buffer ID = %d"%self.m_pAquBufferID[i].value)
                    if jaifactory.J_DataStream_QueueBuffer(self.pDS,self.m_pAquBufferID[i])!=0:
                        del self.m_pAquBuffer[i]
                        break
                    else:
                        print("Sucessfully queued")
                    self.m_iValidBuffers+=1
            else:
                print("Error Creating stream data")        
        return self.m_iValidBuffers

    def start_aquisition(self):
        self.sNodeName=c_char_p("AcquisitionStart".encode('utf-8'))
        #self.sNodeName=create_string_buffer("AcquisitionStart",16)
        if jaifactory.J_Camera_ExecuteCommand(self.camHandle,self.sNodeName)==0:
            print("Acquisition started")
        else:
            print("Error starting aquisition in the camera")

    def stop_aquisition(self):
        self.sNodeName=c_char_p("AcquisitionStop".encode('utf-8'))
        #self.sNodeName=create_string_buffer("AcquisitionStart",16)
        if jaifactory.J_Camera_ExecuteCommand(self.camHandle,self.sNodeName)==0:
            print("Acquisition stoped")
        else:
            print("Error stoping aquisition in the camera")

    def unprepare_buffers(self):
        pPrivate=c_void_p()
        pBuffer=c_void_p()
        #Flush Queues
        print(jaifactory.J_DataStream_FlushQueue(self.pDS, c_int(0)))
        print(jaifactory.J_DataStream_FlushQueue(self.pDS, c_int(1)))
        for i in range(self.m_iValidBuffers):
            #Remove the frame buffer from the Acquisition engine.
            print(jaifactory.J_DataStream_RevokeBuffer(self.pDS,self.m_pAquBufferID[i],byref(self.m_pAquBuffer[i]),byref(self.pPrivateData)))


load_library()        
cameras=update_camera_list("FD")
myCam=Camera()

myCam.open(cameras[1])
print(myCam.get_size())
#myCam.list_nodes()
myCam.get_pixel_format()
#Data stream manual acquisition

#......1......
#Allocate memeroy buffers
print(myCam.prepare_buffers())
#myCam.unprepare_buffers()
#......2......
#Create condition and registed event
#m_hStreamEvent = CreateEvent(NULL, true, false, NULL)
myCam.start_aquisition()
threadStream = threading.Thread(target=myCam.stream_thread, args=(" ",), daemon=True)
threadStream.start()
time.sleep(6)
#myCam.pauseThread()
#time.sleep(3)
#myCam.resumeThread()
#time.sleep(5)

myCam.stopThread()
myCam.stop_aquisition()
time.sleep(1)
myCam.close()




