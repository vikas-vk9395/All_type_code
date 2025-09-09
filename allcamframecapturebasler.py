# from tendo import singleton
# me = singleton.SingleInstance()
import subprocess
CODE_PATH="c:/Users/Admin/Documents/IMAGE_SAVE/ROSR_DATA/"

cam1_path=CODE_PATH+"cam1_09"
cam2_path=CODE_PATH+"cam2_09"
# cam3_path=CODE_PATH+"cam33"
# cam4_path=CODE_PATH+"cam44"
cam1_path = "c:/Users/Admin/Documents/IMAGE_SAVE/ROSR_DATA/ROSR_FRAME_DRY_OK3/"
cam2_path = "c:/Users/Admin/Documents/IMAGE_SAVE/ROSR_DATA/ROSR_FRAME/"
# process_1=subprocess.Popen(['/usr/bin/python3','flir_cams.py'])
# DB_HOST = "localhost"
# DB_USER = "root"
# DB_NAME = "spring_inspection_db"
# DB_PASS = "insightzz123"
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
# from plc_communication_v1 import PLCCommunication
# ##pc_ip=192.168.1.240 ###########################################################


if not os.path.exists(cam1_path):
    os.mkdir(cam1_path)
# if not os.path.exists(cam2_path):
#     os.mkdir(cam2_path)
# if not os.path.exists(cam3_path):
#     os.mkdir(cam3_path)
# if not os.path.exists(cam4_path):
#     os.mkdir(cam4_path)



img_number=-1
async_q=queue.Queue()
grab_state=True
frame_ctr=0
frame_logger = None
cam_count=1
cam_1 = "24511502"
cam_2 = "24550047"
# cam_3 = "24151854"
# cam_4 = "24151857"

#to set exp time 
# exposure_cam1 = 500
# #to change fps-frame per second
# framerate_cam1=1
# exposure_cam2 = 500
# framerate_cam2=1
# exposure_cam3 = 5000
# framerate_cam3=1
# exposure_cam4 = 5000
# framerate_cam4=1

# plcIPAddress = "192.168.0.5"
# plcIPAddress = "000.168.0.5"

# dbReadNumber = 2
# dbWriteNumber = 2
# plcCommunicationObj = PLCCommunication(plcIPAddress, dbReadNumber, dbWriteNumber)
# clientConn = plcCommunicationObj.createConnection()
# IS_OK = ""
# barCode= ""

# class PLC_Read_Trigger_Value:
#     PLC_TRIGGER_CYCLE_WAITING = 0
#     PLC_TRIGGER_CYCLE_START = 1

# class PLC_Write_Trigger_Value:
#     PLC_TRIGGER_CYCLE_RESET = 0
#     PLC_TRIGGER_INSP_OK = 1
#     PLC_TRIGGER_INSP_NOT_OK = 2
    
# class PLC_READ_DB_COLUMN_BUFFER_POSITION:
#     COL_CYCLE_START_INT_start_buffer = 0
#     COL_INSP_RESULT_INT_start_buffer = 2
#     COL_BAR_CODE_STRING_start_buffer = 8

processID = os.getpid()
print("This process has the PID", processID)

class mvrecordingObj:
    global grab_state
    def __init__(self,vid_save_loc,vid_fl_prefx,vid_duration):
        global grab_state
        grab_state=True
        self.clear_raw_frames()        
    
    #def __del__(self):
        #p1.kill()
        #p2.kill()
        
    
    def init_cam(self):
        try:
        
            # Pypylon get camera by serial numberp1
            cam1 = None
            cam2 = None
            # cam3 = None
            # cam4 = None
          

            for i in pylon.TlFactory.GetInstance().EnumerateDevices():
                if i.GetSerialNumber() == cam_1:
                    try:
                        cam1 = i
     
                    except Exception as e:
                        print("cam1 error: "+str(e))
                        
                # elif i.GetSerialNumber() == cam_2:
                #     try:
                #         cam2 = i
     
                #     except Exception as e:
                #         print("cam2 error: "+str(e))
                # elif i.GetSerialNumber() == cam_3:
                #      try:
                #         cam3 = i
     
                #      except Exception as e:
                #          print("cam1 error: "+str(e))
                # elif i.GetSerialNumber() == cam_4:
                #     try:
                #         cam4 = i
     
                #     except Exception as e:
                #         print("cam4 error: "+str(e))
          
                        
   
            self.startframegrabing(cam1,cam2)
            # self.startframegrabing(cam1)
            
        except Exception as e:
            print("main() Exception : ", e)
    
    def startframegrabing(self,cam1,cam2):
    # def startframegrabing(self,cam1):
        global FRAME_LOCATION
        cnt=1
        try:
            image_no_counter = 1
            # VERY IMPORTANT STEP! To use Basler PyPylon OpenCV viewer you have to call .Open() method on you camera
            if cam1 is not None:
                try:
                    cam1 = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(cam1))
                    cam1.Open()
                    cam1.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
                    # cam1.AcquisitionFrameRateEnable=True
                    # cam1.AcquisitionFrameRate=framerate_cam1
                    # cam1.ExposureTime=exposure_cam1        
                except Exception as e:
                    print("cam1 error : "+str(e))

            # if cam2 is not None:
            #     try:
            #         cam2 = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(cam2))
            #         cam2.Open()
            #         cam2.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            #         # cam2.AcquisitionFrameRateEnable=True
            #         # cam2.AcquisitionFrameRate=framerate_cam2
            #         # cam2.ExposureTime=exposure_cam2        
            #     except Exception as e:
            #         print("cam2 error : "+str(e))


            # if cam3 is not None:
            #     try:
            #         cam3 = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(cam3))
            #         cam3.Open()
            #         cam3.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            #         cam3.AcquisitionFrameRateEnable=True
            #         cam3.AcquisitionFrameRate=framerate_cam3
            #         cam3.ExposureTime=exposure_cam3
            #     except Exception as e:
            #         print("cam3 error : "+str(e))
                            
            # if cam4 is not None:
            #     try:
            #         cam4 = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(cam4))
            #         cam4.Open()
            #         cam4.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            #         cam4.AcquisitionFrameRateEnable=True
            #         cam4.AcquisitionFrameRate=framerate_cam4
            #         cam4.ExposureTime=exposure_cam4        
            #     except Exception as e:
            #         print("cam4 error : "+str(e))
                
     
                
            converter = pylon.ImageFormatConverter()
            converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
            
            top_once1 = True
            top_once2 = True

            top2_once1 = True
            top2_once2 = True

            in_once1 = True
            in_once2 = True

            out_once1 = True
            out_once2 = True

  
            PLC_CONNECTED = 1
            PLC_NOT_CONNECTED = 2
            isPLCNotConnected = False

            while True:
                ############# Top Post ###################
                total_t = int(time.time()*1000)
                try:
                    
                    ############################################## ok ###########################################
                    cnt=cnt+1
                    t1 = int(time.time()*1000) 
                    if cam1.IsGrabbing():
                        grabResult = cam1.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                    if grabResult.GrabSucceeded():
                        image = converter.Convert(grabResult)
                        img = image.GetArray()
                        cv2.imwrite(cam1_path+"/tmp.jpg",img)
                        #cv2.imwrite(cam1_path+"/tmp.jpg",cam1_path+"/"+str(time.time())+str(cnt)+".jpg")   
                        print("Cam-01 image save")
                        if image_no_counter == 1:
                           shutil.move(cam1_path+"/tmp.jpg",cam1_path+"/"+str(time.time())+str(cnt)+".jpg")                
                    if(cam1 is not None):
                        grabResult.Release()
                    #print("time for cam1 frame : ", int(time.time()*1000) - t1) 
                    #print("Camera -01 not connected")
                    top_once1 = True
                   
                    #     for f in os.listdir(cam1_path):
                    #         os.remove(cam1_path+"/"+f)
                    if top_once2:
                        top_once2 = False
                except Exception as e:
                    if top_once1:
                        top_once2 = True
                        print("Exception cam1", e) 
                        top_once1 = False
                
            #     ############# Top2 Post ###################
                total_t = int(time.time()*1000)
                # try:
                #     #t1 = int(time.time()*1000) 
                #     if cam2.IsGrabbing():
                #         grabResult = cam2.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                #     if grabResult.GrabSucceeded():
                #         #  Access the image data
                #         image = converter.Convert(grabResult)
                #         img = image.GetArray()
                #         cv2.imwrite(cam2_path+"/tmp.jpg",img)
                #         #cv2.imwrite(cam2_path+"/tmp.jpg",cam2_path+"/"+str(time.time())+str(cnt)+".jpg")
                #         print("Cam-02 image save")
                #         if image_no_counter == 1:
                #             shutil.move(cam2_path+"/tmp.jpg",cam2_path+"/"+str(time.time())+str(cnt)+".jpg")                
                #     if(cam2 is not None):
                #         grabResult.Release()
                #     #print("time for cam2 frame : ", int(time.time()*1000) - t1) 
                #     top2_once1 = True
                #     if(len(os.listdir(cam1_path))>1):
                #          grabResult.Release()

                #     # if(len(os.listdir(cam2_path))>20):
                #     #     for f in os.listdir(cam2_path):
                #     #         os.remove(cam2_path+"/"+f)

                #     if top2_once2:
                #         top2_once2 = False
                # except Exception as e:
                #     if top2_once1:
                #         top2_once2 = True
                #         print("Exception CAM2 ", e) 
                #         top2_once1 = False
                
           
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                # cam1.StopGrabbing()
                # cam2.StopGrabbing()
                # # cam3.StopGrabbing()
                # # cam4.StopGrabbing()

            if(cam1 is not None):
                cam1.StopGrabbing()
                cam1.close() 
            # if(cam2 is not None):
            #     cam2.StopGrabbing()
            #     cam2.close()            
            # if(cam3 is not None):
            #     cam3.StopGrabbing()
            #     cam3.close()
            # if(cam4 is not None):
            #     cam4.StopGrabbing()
            #     cam4.close() 
          
        except Exception as e:
            print("after while  Exception : ", e)
            threading.Timer(10.0,self.init_cam()).start()
        print("time for all loop frame : ", int(time.time()*1000) - total_t)     
            
    def clear_raw_frames(self):
        pass
            
        
    def run_module(self):
        self.init_cam()  



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
