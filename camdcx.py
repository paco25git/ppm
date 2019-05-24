#This is a library for handle the Thorlabs DCx series
#This library was created specifically for the DCC1545M camera
#
#This is a transalation for use the uc480.dll file with python 
#In this version there isn't the whole set of instructions available 

import os.path
from ctypes import *
import numpy as np

class CameraOpenError(Exception):
	def __init__(self, mesg):
		self.mesg=mesg
	def __str__(self):
		return self.mesg
		
class Camera(object):
    def __init__(self):
        #uc480_file='C:\\Program Files\\Thorlabs\\Scientific Imaging\\ThorCam\\uc480.dll' #uc480_64.dll for 64bits
        uc480_file='C:\\Users\\namid\\Desktop\\pythonCamera\\ppmRep\\uc480.dll' #other location
        if os.path.isfile(uc480_file):
            self.bit_depth = None
            self.roi_shape = None
            self.camera = None
            self.handle = None
            self.meminfo = None
            self.exposure = None
            self.roi_pos = None
            self.framerate = None
            self.uc480 = cdll.LoadLibrary(uc480_file) #windll.LoadLibrary(uc480_file) for 64bits
        else:
            raise CameraOpenError("ThorCam drivers not available.")
	
    def open(self, bit_depth=8, roi_shape=(1280, 1024), roi_pos=(0,0), camera="ThorCam FS", exposure = 10, framerate = 10.0):
        self.bit_depth = bit_depth
        self.roi_shape = roi_shape
        self.camera = camera
        self.roi_pos = roi_pos
        
        is_InitCamera = self.uc480.is_InitCamera
        is_InitCamera.argtypes = [POINTER(c_int)]
        self.handle = c_int(0)
        i = is_InitCamera(byref(self.handle))       

        if i == 0:
            print("Thorlabs Camera opened successfully.")
            pixelclock = c_uint(30) #set pixel clock to 43 MHz (fastest)
            is_PixelClock = self.uc480.is_PixelClock
            is_PixelClock.argtypes = [c_int, c_uint, POINTER(c_uint), c_uint]
            is_PixelClock(self.handle, 6 , byref(pixelclock), sizeof(pixelclock)) #6 for setting pixel clock            
            self.uc480.is_SetColorMode(self.handle, 6) # 6 is for monochrome 8 bit. See uc480.h for definitions
            self.set_roi_shape(self.roi_shape)
            self.set_roi_pos(self.roi_pos)
            self.set_framerate(framerate)
            self.set_exposure(exposure)
        else:
            raise CameraOpenError("Opening the ThorCam failed with error code "+str(i))
			
    def close(self):
        if self.handle != None:
            self.stop_live_capture()
            i = self.uc480.is_ExitCamera(self.handle) 
            if i == 0:
                print("ThorCam closed successfully.")
            else:
                print("Closing ThorCam failed with error code "+str(i))
        else:
            return

	
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

        self.uc480.is_CaptureVideo(self.handle, 1)
		
    def stop_live_capture(self):
        print ('unlive now')
		#self.epix.pxd_goUnLive(0x1)
        self.uc480.is_StopLiveVideo(self.handle, 1)
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
        x=self.uc480.is_SetAllocatedImageMem(self.handle, xdim, ydim, 8, byref(c_buf), byref(memid))
        if x==0:
            print("Memory successfully allocated, memID= %d"%memid.value)
		#self.uc480.is_SetImageMem(self.handle, byref(c_buf), byref(memid))
        self.meminfo = [c_buf, memid]
        return self.meminfo
		
    def add_to_sequence(self,pcImgMem,nID):
        self.pcImgMem=pcImgMem
        self.nID=nID
        x=self.uc480.is_AddToSequence(self.handle,byref(pcImgMem),nID)
        if x==0:
            print("Memory successfully added to sequence")
        else:
            print("Memory couldn't added to sequence, error code= %d"%x)
			
    def get_active_image_mem(self):
        poin=c_int()
        id=c_int()
        self.uc480.is_GetActiveImageMem(self.handle,byref(poin),byref(id))
        return id.value
		
    def init_image_queue(self):
        self.uc480.is_InitImageQueue(self.handle,0)
	
    def set_bit_depth(self, set_bit_depth = 8):
        if set_bit_depth != 8:
            print("only 8-bit images supported")
    
    def set_roi_shape(self, set_roi_shape):
        class IS_SIZE_2D(Structure):
            _fields_ = [('s32Width', c_int), ('s32Height', c_int)]
        AOI_size = IS_SIZE_2D(set_roi_shape[0], set_roi_shape[1]) #Width and Height
            
        is_AOI = self.uc480.is_AOI
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
            
        is_AOI = self.uc480.is_AOI
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
        is_Exposure = self.uc480.is_Exposure
        is_Exposure.argtypes = [c_int, c_uint, POINTER(c_double), c_uint]
        is_Exposure(self.handle, 12 , exposure_c, 8) #12 is for setting exposure
        self.exposure = exposure_c.value
		
    def get_exposure(self):
        exposure_c=c_double()
        is_Exposure=self.uc480.is_Exposure
        is_Exposure.argtypes=[c_int,c_uint, POINTER(c_double), c_uint]
        is_Exposure(self.handle,7,exposure_c,8)
        ex=self.exposure
        return ex
	
    def set_framerate(self, framerate):
		#must reset exposure after setting framerate
		#frametime should be givin in ms. Framerate = 1/frametime
        is_SetFrameRate = self.uc480.is_SetFrameRate 
        
        if framerate == 0: framerate = 1
        
        set_framerate = c_double(0)
        is_SetFrameRate.argtypes = [c_int, c_double, POINTER(c_double)]
        is_SetFrameRate(self.handle, framerate, byref(set_framerate))
        self.framerate = set_framerate.value
		
    def get_framerate(self):
        framerate=c_double()
        is_GetFramesPerSecond=self.uc480.is_GetFramesPerSecond
        is_GetFramesPerSecond.argtypes=[c_int,c_double]
        is_GetFramesPerSecond(self.handle,framerate)
        fr=self.framerate
        return fr
		
    def freeze_video(self):
        res=self.uc480.is_FreezeVideo(self.handle,0)
        return res
    def set_external_trigger(self):
        self.uc480.is_SetExternalTrigger(self.handle,0x0008)
		
    def init_image_queue(self):
        self.uc480.is_InitImageQueue(self.handle,0)