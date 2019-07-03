

class camerasClass(list):
    def __init__(self):
        self.active=None
        #self=None
    def create(self):
        for i in range(2):
            self.append(i)
    def setactive(self,i):
        self.active=i

cameras=camerasClass()
print(cameras)
print(cameras.active)
cameras.create()
print(cameras)
print(cameras[0])
