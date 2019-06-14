import camdcx
import time
import threading

class souce(object):
    def __init__(self):
        self.id=1
        self.hilo=self.Hilo()

class Hilo(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.can_run=threading.Event()
        self.thing_done=threading.Event()
        self.thing_done.set()
        self.can_run.set()
        self.daemon=True

    def run(self):
        while True:
            self.can_run.wait()
            try:
                self.thing_done.clear()
                print("working")
            finally:
                self.thing_done.set()
    
    def pause(self):
        self.can_run.clear()
        self.thing_done.wait()

    def resume(self):
        self.can_run.set()

print("Starting main")
time.sleep(1)
print("creating thread")
thr=Hilo()
time.sleep(1)
print("starting thread")
thr.start()
time.sleep(2)
thr.pause()
print("thread paused")
time.sleep(2)
print("resuming")
thr.resume()