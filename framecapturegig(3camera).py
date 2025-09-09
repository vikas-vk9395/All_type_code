#from tendo import singleton
#me = singleton.SingleInstance()

import cv2
import time
import os
import threading
import logging
from pypylon import pylon
import traceback
import multiprocessing as mp
#for recording time limit
import queue
import shutil
import datetime
import pymysql
import signal

img_number=-1
async_q=queue.Queue()
grab_state=True
frame_ctr=0
mv_logger = None
frame_logger = None

CAM1 = "24351855"
CAM2 = "24352346"
CAM3 = "24352344"

exposure = 15015
processID = os.getpid()


class mvrecordingObj:
    global grab_state,mv_logger
    logging.basicConfig(filename="MV_RECORD_ACT_.log",filemode='a',format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    mv_logger=logging.getLogger("MV_RECORD_ACT_")
    mv_logger.setLevel(logging.DEBUG)
    mv_logger.debug("CODE STARTED")    
    def __init__(self,vid_save_loc,vid_fl_prefx,vid_duration):
        global grab_state,mv_logger
        grab_state=True
        self.clear_raw_frames()     
    
    def __del__(self):
        pass
    

    def init_cam(self):

        try:
            # Pypylon get camera by serial number
            cam1=None
            cam2=None
            cam3=None

            for i in pylon.TlFactory.GetInstance().EnumerateDevices():
                if i.GetSerialNumber() == CAM1:
                    try:
                        cam1 = i
    
                    except Exception as e:
                        print("CAM1 error: "+str(e))
                        mv_logger.debug("CAm1 error: "+str(e))
                        
                elif i.GetSerialNumber() == CAM2:
                    try:
                        cam2 = i
    
                    except Exception as e:
                        print("CAM2 error: "+str(e))
                        mv_logger.debug("CAm2 error: "+str(e))
                elif i.GetSerialNumber() == CAM3:
                    try:
                        cam3 = i
    
                    except Exception as e:
                        print("CAM3 error: "+str(e))
                        mv_logger.debug("CAm3 error: "+str(e))
                                
    
            self.startframegrabing(cam1,cam2,cam3)
            
        except Exception as e:
            print("main() Exception : ", e)
            mv_logger.debug("main() Exception : "+str(e))
    
    def startframegrabing(self,cam1,cam2,cam3):
        global FRAME_LOCATION
        cam1_obj=None
        cam2_obj=None
        cam3_obj=None
        try:
            image_no_counter = 1
            
            if cam1 is not None:
                try:
                    cam1_obj = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(cam1))
                    cam1_obj.Open()
                    cam1_obj.GevSCPSPacketSize.SetValue(1500)          
                    cam1_obj.GevSCPD.SetValue(1000)          
                    cam1_obj.GevSCFTD.SetValue(1000)          
                    cam1_obj.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
                    cam1_obj.AcquisitionFrameRateEnable=True
                    cam1_obj.AcquisitionFrameRateAbs=30.00
                    cam1_obj.ExposureTimeAbs.SetValue(exposure)                
                    cam1_obj.ExposureTimeRaw.SetValue(exposure)             
                except Exception as e:
                    print("cam1 error : "+str(e))
                    mv_logger.debug("cam1 error : "+str(e))

            if cam2 is not None:
                try:
                    cam2_obj = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(cam2))
                    cam2_obj.Open()
                    cam2_obj.GevSCPSPacketSize.SetValue(1500)          
                    cam2_obj.GevSCPD.SetValue(1000)          
                    cam2_obj.GevSCFTD.SetValue(1000)          
                    cam2_obj.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
                    cam2_obj.AcquisitionFrameRateEnable=True
                    cam2_obj.AcquisitionFrameRateAbs=30.00
                    cam2_obj.ExposureTimeAbs.SetValue(exposure)                
                    cam2_obj.ExposureTimeRaw.SetValue(exposure)             
                except Exception as e:
                    print("cam2 error : "+str(e))
                    mv_logger.debug("cam2 error : "+str(e))

            if cam3 is not None:
                try:
                    cam3_obj = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(cam3))
                    cam3_obj.Open()
                    cam3_obj.GevSCPSPacketSize.SetValue(1500)          
                    cam3_obj.GevSCPD.SetValue(1000)          
                    cam3_obj.GevSCFTD.SetValue(1000)          
                    cam3_obj.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
                    cam3_obj.AcquisitionFrameRateEnable=True
                    cam3_obj.AcquisitionFrameRateAbs=30.00
                    cam3_obj.ExposureTimeAbs.SetValue(exposure)                
                    cam3_obj.ExposureTimeRaw.SetValue(exposure)             
                except Exception as e:
                    print("cam3 error : "+str(e))
                    mv_logger.debug("cam3 error : "+str(e))
                
            converter = pylon.ImageFormatConverter()
            converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
            
            cam1_path="CAM1"
            cam2_path="CAM2"
            cam3_path="CAM3"
            if not os.path.exists(cam1_path):
                os.mkdir(cam1_path)
            if not os.path.exists(cam2_path):
                os.mkdir(cam2_path)
            if not os.path.exists(cam3_path):
                os.mkdir(cam3_path)
            while True:
                try:
                    t1 = int(time.time()*1000) 
                    if cam1_obj.IsGrabbing():
                        grabResult = cam1_obj.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                        if grabResult.GrabSucceeded():
                            # Access the image data
                            image = converter.Convert(grabResult)
                            img = image.GetArray()
                            img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
                            cv2.imwrite(cam1_path+"/IMG_"+str(int(time.time())*1000)+".jpg",img)
                        
                except Exception as e:
                    print(e)
                try:
                    t1 = int(time.time()*1000) 
                    if cam2_obj.IsGrabbing():
                        grabResult = cam2_obj.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                        if grabResult.GrabSucceeded():
                            # Access the image data
                            image = converter.Convert(grabResult)
                            img = image.GetArray()
                            img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
                            cv2.imwrite(cam2_path+"/IMG_"+str(int(time.time())*1000)+".jpg",img)
                        
                except Exception as e:
                    print(e)
                try:
                    t1 = int(time.time()*1000) 
                    if cam3_obj.IsGrabbing():
                        grabResult = cam3_obj.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                        if grabResult.GrabSucceeded():
                            # Access the image data
                            image = converter.Convert(grabResult)
                            img = image.GetArray()
                            img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
                            cv2.imwrite(cam3_path+"/IMG_"+str(int(time.time())*1000)+".jpg",img)
                        
                except Exception as e:
                    print(e)
        
        except Exception as e:
            print("after while  Exception : ", e)
            mv_logger.debug("after while  Exception : "+str(e))
            threading.Timer(10.0,self.init_cam()).start()
            
    def clear_raw_frames(self):
        pass
            
        
    def run_module(self):
        #mv_logger.debug("MV Record Process Started")
        self.init_cam()
        #mv_logger.debug("Process ended")      

def run_once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)
    wrapper.has_run = False
    return wrapper

def call_error(cam_pos):
    print("Error in function my function "+str(cam_pos))

if __name__=="__main__":
    obj1=mvrecordingObj(os.getcwd(), "FNL_TST", 60)
    obj1.run_module()
