#This is a library for handle the Thorlabs DCx series
#This library was created specifically for the DCC1545M camera
#
#This is a transalation for use the uc480.dll file with python 
#In this version there isn't the whole set of instructions available 

import os.path
from ctypes import *
import numpy as np
import win32event
import threading

uc480=None

#Function for load the uc480.dll dinamic library and use the function defined inside it
def load_library():
    global uc480
    uc480_file=os.path.dirname(os.path.realpath(__file__))+"\\includesThL\\uc480.dll"
    if os.path.isfile(uc480_file):
        uc480=cdll.LoadLibrary(uc480_file)
        return True
    else:
        raise CameraOpenError("ThorCam drivers not available.")

def list_cameras_connected():  
    cams=[]
    class UC480_CAMERA_INFO(Structure):
        _fields_ = [('dwCameraID', c_uint), ('dwDeviceID', c_uint), ('dwSensorID', c_uint), ('dwInUse', c_uint), ('SerNo', c_char*16), ('Model', c_char*16), ('dwStatus', c_uint), ('dwReserved', c_uint*2), ('FullModelName', c_char*32), ('dwReserved2', c_uint*5)]
        camType="ThorlabsCam"
    class UC480_CAMERA_LIST(Structure):
        _fields_= [('dwCount',c_uint),('uci',UC480_CAMERA_INFO*1)]
    
    nNumCam=c_uint()  
    if uc480.is_GetNumberOfCameras(byref(nNumCam))==0: #IS_SUCCESS=0 defined in uc480.h
        if nNumCam.value>=1:
            print("%d cameras founded"%nNumCam.value)
            #Create new list with suitable size
            pucl=UC480_CAMERA_LIST()
            pucl.dwCount=nNumCam
            if uc480.is_GetCameraList(byref(pucl))==0:
                for i in range(nNumCam.value):
                    print("Camera %d: "%i)
                    print("Camera ID : %d"%pucl.uci[i].dwCameraID)
                    print("Device ID : %d"%pucl.uci[i].dwDeviceID)
                    print("Model : %s"%pucl.uci[i].Model.decode("utf-8"))
                    print("Serial number : %s"%pucl.uci[i].SerNo.decode("utf-8"))
                    print("In use? : %d"%pucl.uci[i].dwInUse) #0=camera is not being used, 1=camera is being used
                    cams.append(pucl.uci[i])
            return cams
        else:
            print("No cameras founded")
            return cams
    else:
        print("error finding cameras")
        raise CameraOpenError(" ")
        


class CameraOpenError(Exception):
	def __init__(self, mesg):
		self.mesg=mesg
	def __str__(self):
		return self.mesg
		
class Camera(object):
    def __init__(self,cameraInfo=None):
        if uc480==None:
            raise CameraOpenError("uc480.dll file not open, use load_library() method")
        else:
            self.camType="ThorlabsCam"
            self.cameraInfo = cameraInfo
            self.bit_depth = None
            self.roi_shape = None
            self.name = None
            self.handle = None
            self.meminfo = None
            self.exposure = None
            self.roi_pos = None
            self.framerate = None
            self.NBuff=None
            #thread variables
            self.can_run=threading.Event()
            self.thing_done=threading.Event()
            self.end_thread=threading.Event()
            self.thing_done.set()
            self.can_run.set()
            self.end_thread.clear()
            self.isOpen=False

    def stream_thread(self,imqueue=None,app=None,threadname='Thorlabs_Stream'):
        print("Thorlabs Stream Thread initied")
        self.frame=0
        while True:
            self.can_run.wait() #Wait
            try:
                self.waitEvent=win32event.WaitForSingleObject(self.handleEvent,1000)
                self.ID=self.get_active_image_mem()-1
                if self.ID==0:
                    self.ID=self.NBuff 
                if self.waitEvent==win32event.WAIT_TIMEOUT:
                    print("Timed out")
                elif self.waitEvent==win32event.WAIT_OBJECT_0:
                    arr=self.get_image_v2(self.memID.get(self.ID))
                    if imqueue:
                        imqueue.put(arr)
                    if app:
                        app.setImage(arr)
                    self.frame+=1      
                if self.frame>len(self.mem):
                    self.frame=0
            finally:
                self.thing_done.set() #Task done
                if self.end_thread.is_set():
                    break
        print("Thread stoped")

    def pauseThread(self):
        self.can_run.clear()
        print("Camera stream thread paused")
        self.thing_done.wait()

    def resumeThread(self):
        print("Camera stream thread resumed")
        self.can_run.set()

    def stopThread(self):
        self.end_thread.set()

    def open(self, bit_depth=8, roi_shape=(1280, 1024), roi_pos=(0,0), name="Thorlabs", exposure = 10, framerate = 20.0):
        self.bit_depth = bit_depth
        self.roi_shape = roi_shape
        self.name = name
        self.roi_pos = roi_pos
        
        is_InitCamera = uc480.is_InitCamera
        is_InitCamera.argtypes = [POINTER(c_int)]
        self.handle = c_int(0)
        i = is_InitCamera(byref(self.handle))       

        if i == 0:
            print("Thorlabs Camera opened successfully.")
            pixelclock = c_uint(30) #set pixel clock to 43 MHz (fastest)
            is_PixelClock = uc480.is_PixelClock
            is_PixelClock.argtypes = [c_int, c_uint, POINTER(c_uint), c_uint]
            is_PixelClock(self.handle, 6 , byref(pixelclock), sizeof(pixelclock)) #6 for setting pixel clock            
            uc480.is_SetColorMode(self.handle, 6) # 6 is for monochrome 8 bit. See uc480.h for definitions
            self.set_roi_shape(self.roi_shape)
            self.set_roi_pos(self.roi_pos)
            self.set_framerate(framerate)
            self.set_exposure(exposure)
            self.isOpen=True
            return True
        else:
            #raise CameraOpenError("Opening the ThorCam failed with error code "+str(i))
            return False
			
    def close(self):
        if self.handle != None:
            self.stop_live_capture()
            i = uc480.is_ExitCamera(self.handle) 
            if i == 0:
                self.isOpen=False
                print("ThorCam closed successfully.")
            else:
                print("Closing ThorCam failed with error code "+str(i))
        else:
            return

    def create_sequence(self,N=5):
        self.memID={}
        self.mem=[]
        self.NBuff=N
        #self.set_external_trigger()
        for i in range(self.NBuff):
            self.mem.append(self.initialize_memory())
            self.add_to_sequence(self.mem[i][0],self.mem[i][1])
            self.memID[self.mem[i][1].value]=self.mem[i][0]
        return self.mem
	
    def get_image(self, buffer_number=None):
        #buffer number not yet used
        #if buffer_number is None:
        #    buffer_number = self.epix.pxd_capturedBuffer(1)

        im = np.frombuffer(self.meminfo[0], c_ubyte).reshape(self.roi_shape[1], self.roi_shape[0])
        return im
			
    def get_image_v2(self,addrs):
        #buffer number not yet used
        #if buffer_number is None:
		#    buffer_number = self.epix.pxd_capturedBuffer(1)
        self.addrs=addrs
        ima = np.frombuffer(self.addrs, c_ubyte).reshape(self.roi_shape[1], self.roi_shape[0])
        return ima
	
    def start_continuous_capture(self, buffersize = None):

        '''
		buffersize: number of frames to keep in rolling buffer
        '''

        uc480.is_CaptureVideo(self.handle, 1)
		
    def stop_live_capture(self):
        print ('unlive now')
		#self.epix.pxd_goUnLive(0x1)
        uc480.is_StopLiveVideo(self.handle, 1)
    """
	def alloc_image_mem(self):
		id=c_int()
		pid=pointer(id)
		pcImgMem=c_int()
		ppcImgMem=pointer(pcImgMem)
		bitspixel=c_int(8)
		height=c_int(self.roi_shape[1])
		width=c_int(self.roi_shape[0])
		#is_AllocImageMem=self.uc480.is_AllocImageMem
		#is_AllocImageMem.argtypes=[c_int,c_int,c_int,POINTER(c_int),POINTER(c_int)]
		x=self.uc480.is_AllocImageMem(self.handle,width,height,byref(pcImgMem),byref(pid))
		#self.uc480.is_SetImageMem(self.handle,ppcImgMem, pid)
		return pcImgMem,id,x
	"""	
    def initialize_memory(self):
		#if self.meminfo != None:
		#	self.uc480.is_FreeImageMem(self.handle, self.meminfo[0], self.meminfo[1])
        
        xdim = self.roi_shape[0]
        ydim = self.roi_shape[1]
        imagesize = xdim*ydim
            
        memid = c_int(0)
		#pmemid=pointer(memid)
        c_buf = (c_ubyte * imagesize)(0)
        x=uc480.is_SetAllocatedImageMem(self.handle, xdim, ydim, 8, byref(c_buf), byref(memid))
        if x==0:
            print("Memory successfully allocated, memID= %d"%memid.value)
		#self.uc480.is_SetImageMem(self.handle, byref(c_buf), byref(memid))
        self.meminfo = [c_buf, memid]
        return self.meminfo
		
    def add_to_sequence(self,pcImgMem,nID):
        self.pcImgMem=pcImgMem
        self.nID=nID
        x=uc480.is_AddToSequence(self.handle,byref(pcImgMem),nID)
        if x==0:
            print("Memory successfully added to sequence")
        else:
            print("Memory couldn't added to sequence, error code= %d"%x)

    def get_active_image_mem(self):
        poin=c_int()
        id=c_int()
        uc480.is_GetActiveImageMem(self.handle,byref(poin),byref(id))
        return id.value
		
    def init_image_queue(self):
        uc480.is_InitImageQueue(self.handle,0)
	
    def set_bit_depth(self, set_bit_depth = 8):
        if set_bit_depth != 8:
            print("only 8-bit images supported")
    
    def set_roi_shape(self, set_roi_shape):
        class IS_SIZE_2D(Structure):
            _fields_ = [('s32Width', c_int), ('s32Height', c_int)]
        AOI_size = IS_SIZE_2D(set_roi_shape[0], set_roi_shape[1]) #Width and Height
            
        is_AOI = uc480.is_AOI
        is_AOI.argtypes = [c_int, c_uint, POINTER(IS_SIZE_2D), c_uint]
        i = is_AOI(self.handle, 5, byref(AOI_size), 8 )#5 for setting size, 3 for setting position
        is_AOI(self.handle, 6, byref(AOI_size), 8 )#6 for getting size, 4 for getting position
        self.roi_shape = [AOI_size.s32Width, AOI_size.s32Height]
        
        if i == 0:
            print("ThorCam ROI size set successfully.")
			#self.initialize_memory()
        else:
            print("Set ThorCam ROI size failed with error code "+str(i))

    def set_roi_pos(self, set_roi_pos):
        class IS_POINT_2D(Structure):
            _fields_ = [('s32X', c_int), ('s32Y', c_int)]
        AOI_pos = IS_POINT_2D(set_roi_pos[0], set_roi_pos[1]) #Width and Height
            
        is_AOI = uc480.is_AOI
        is_AOI.argtypes = [c_int, c_uint, POINTER(IS_POINT_2D), c_uint]
        i = is_AOI(self.handle, 3, byref(AOI_pos), 8 )#5 for setting size, 3 for setting position
        is_AOI(self.handle, 4, byref(AOI_pos), 8 )#6 for getting size, 4 for getting position
        self.roi_pos = [AOI_pos.s32X, AOI_pos.s32Y]
        
        if i == 0:
            print("ThorCam ROI position set successfully.")
        else:
            print("Set ThorCam ROI size failed with error code "+str(i))
    
    def set_exposure(self, exposure):
        #exposure should be given in ms
        exposure_c = c_double(exposure)
        is_Exposure = uc480.is_Exposure
        is_Exposure.argtypes = [c_int, c_uint, POINTER(c_double), c_uint]
        is_Exposure(self.handle, 12 , exposure_c, 8) #12 is for setting exposure
        self.exposure = exposure_c.value
		
    def get_exposure(self):
        exposure_c=c_double()
        is_Exposure=uc480.is_Exposure
        is_Exposure.argtypes=[c_int,c_uint, POINTER(c_double), c_uint]
        is_Exposure(self.handle,7,exposure_c,8)
        ex=self.exposure
        return ex
	
    def set_framerate(self, framerate):
		#must reset exposure after setting framerate
		#frametime should be givin in ms. Framerate = 1/frametime
        is_SetFrameRate = uc480.is_SetFrameRate 
        
        if framerate == 0: framerate = 1
        
        set_framerate = c_double(0)
        is_SetFrameRate.argtypes = [c_int, c_double, POINTER(c_double)]
        is_SetFrameRate(self.handle, framerate, byref(set_framerate))
        self.framerate = set_framerate.value
		
    def get_framerate(self):
        framerate=c_double()
        is_GetFramesPerSecond=uc480.is_GetFramesPerSecond
        is_GetFramesPerSecond.argtypes=[c_int,c_double]
        is_GetFramesPerSecond(self.handle,framerate)
        fr=self.framerate
        return fr
		
    def freeze_video(self):
        res=uc480.is_FreezeVideo(self.handle,0) #IS_DONT_WAIT=0x0000  IS_WAIT=1 defined in uc480.h
        return res

    def set_external_trigger(self):
        uc480.is_SetExternalTrigger(self.handle,0x0008)

    def enable_event(self):
        s= uc480.is_EnableEvent(self.handle,self.which)
        return s
		
    def init_event(self, which=2):
        self.which=c_int(which)
        self.handleEvent=win32event.CreateEvent(None,False,False,None)
        s=uc480.is_InitEvent(self.handle, c_int(self.handleEvent), self.which)
        return self.handleEvent

    def get_sensor_info(self):
        class SENSORINFO(Structure):
            _fields_= [('SensorID',c_uint),('strSensorName',c_char*32),('nColorMode',c_char),('nMaxWidth',c_uint),('nMaxHeight',c_uint),('bMasterGain',c_bool),('bRGain',c_bool),('bGGain',c_bool),('bBGain',c_bool),('bGlobShutter',c_bool),('wPixelSize',c_uint),('nUpperLeftBayerPixel',c_char),('Reserved',c_char*13)]
        self.sensorInf=SENSORINFO()
        if uc480.is_GetSensorInfo(self.handle, byref(self.sensorInf))!=0:
            print("Error getting sensor info")
            return False
        else:
            print("Sensor ID: %d"%self.sensorInf.SensorID)
            print("Sensor name: %s"%self.sensorInf.strSensorName.decode('utf-8'))
            print("Color mode: %s"%self.sensorInf.nColorMode.decode('utf-8'))
            print("Max Width: %d"%self.sensorInf.nMaxWidth)
            print("Max Height: %d"%self.sensorInf.nMaxHeight)
            print("Master Gain?: %r"%self.sensorInf.bMasterGain)
            print("Red Gain?: %r"%self.sensorInf.bRGain)
            print("Green Gain?: %r"%self.sensorInf.bGGain)
            print("Blue Gain?: %r"%self.sensorInf.bBGain)
            print("Global shutter?: %r"%self.sensorInf.bGlobShutter)
            print("Global shutter?: %r"%self.sensorInf.bGlobShutter)
            print("Pixel Size: %d"%self.sensorInf.wPixelSize)
            print("Upper Left Bayer Pixel: %s"%self.sensorInf.nUpperLeftBayerPixel)
            return self.sensorInf
    
    def get_gain_values(self):
        self.mGain=uc480.is_SetHardwareGain(self.handle,c_int(0x8000),c_int(-1),c_int(-1),c_int(-1))
        print("Master Gain= %d"%self.mGain)
    """
    def set_master_gain(self,value):
        self.masterGain=value
        self.
        if uc480.is_SetHardwareGain(self.handle,)
    """    
        
        
        
        