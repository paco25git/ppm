"""
import camdcx
import time
import threading

class souce(object):
    def __init__(self):
        self.id=1
        self.hilo=self.Hilo()

class Hilo(threading.Thread):
    def __init__(self,x):
        threading.Thread.__init__(self)
        self.can_run=threading.Event()
        self.thing_done=threading.Event()
        self.thing_done.set()
        self.can_run.set()
        self.daemon=True
        
    def run(self):
        print("First things")
        while True:
            self.can_run.wait()
            try:
                self.thing_done.clear()
                print("working %d"%x)
                time.sleep(0.5)
            finally:
                self.thing_done.set()
    
    def pause(self):
        self.can_run.clear()
        self.thing_done.wait()

    def resume(self):
        self.can_run.set()

print("Starting main")
time.sleep(1)
x=2
print("creating thread")
thr=Hilo(x)
time.sleep(1)

print("starting thread")
thr.start()
time.sleep(2)
thr.pause()
x=88
print("thread paused")
time.sleep(2)
print("resuming")
thr.resume()
time.sleep(2)
"""
#!/usr/bin/env python



import cv2

import numpy as np

import argparse





'''

Create blended heat map with JET colormap 



'''



def create_heatmap(im_map, im_cloud, kernel_size=(5,5),colormap=cv2.COLORMAP_JET,a1=0.5,a2=0.5):

    '''

    img is numpy array

    kernel_size must be odd ie. (5,5)

    '''



    # create blur image, kernel must be an odd number

    im_cloud_blur = cv2.GaussianBlur(im_cloud,kernel_size,0)



    # If you need to invert the black/white data image

    # im_blur = np.invert(im_blur)

    # Convert back to BGR for cv2

    #im_cloud_blur = cv2.cvtColor(im_cloud_blur,cv2.COLOR_GRAY2BGR)



    # Apply colormap

    im_cloud_clr = cv2.applyColorMap(im_cloud_blur, colormap)



    # blend images 50/50

    return (a1*im_map + a2*im_cloud_clr).astype(np.uint8) 







if __name__ == "__main__":

    

    ap = argparse.ArgumentParser()

    ap.add_argument('-m','--map-image',default='map.png',required=True,help="Path to map image")

    ap.add_argument('-c','--cloud-image',default='clouds.png',required=True,help="Path to cloud image (grayscale)")

    ap.add_argument('-s','--save',action='store_true',default=False,help="Save image")



    #ap.add_argument('--cloud-pos',default=(0,0),required=False,help="Position of cloud, relative to map origin")

    args = ap.parse_args()



    im_map = cv2.imread(args.map_image)

    im_cloud =cv2.imread(args.cloud_image)

    # Normalize cloud image?

    im_heatmap = create_heatmap(im_map, im_cloud, a1=.5, a2=.5)

    if args.save:

        cv2.imwrite('clouds_map_out.png',im_heatmap)

    else:

        cv2.imshow('cloud cover',im_heatmap)

        cv2.waitKey(0)