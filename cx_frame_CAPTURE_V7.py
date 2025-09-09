import logging,time,os,traceback
from typing import Optional
import sys
import cv2
import xml.etree.ElementTree as ET
import subprocess
import shutil
import numpy as np
from pymodbus.client import ModbusTcpClient
import time
import pymysql
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "insightzz@123"
DB_NAME = "railclip_db"
XML_PATH="C:/INSIGHTZZ/RAILCLIP/RAILCLIP1/RAILCLIP.xml"
config_root=ET.parse(XML_PATH)
CODE_PATH=config_root.find("CODE_PATH").text
CX_FRAME_CAPTURE_V6=os.path.join(CODE_PATH,config_root.find("CX_LOG").text)
logger = None
log_format=logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger=logging.getLogger("CX_LOG")
logger.setLevel(logging.DEBUG)
logger_fh=logging.FileHandler(CX_FRAME_CAPTURE_V6,mode='a')
logger_fh.setFormatter(log_format)
logger_fh.setLevel(logging.DEBUG)
logger.addHandler(logger_fh)

def fetchtrigger():
    trigger=""
    global DB_USER,DB_NAME,DB_PASS,DB_HOST
    try:
        query = f"SELECT trigger1 FROM railclip_db.trigger order by ID desc limit 1;"
       # query=f"UPDATE `railclip_db`.`trigger` SET `trigger1` = 'TRUE' , inspect='{inspect}' WHERE (`ID` = '1');"
      #  query=f"UPDATE `railclip_db`.`history` SET `LENGTH` = '{length}', `WIDTH` = '{width}', `GAP1` = '{gap_1}', `GAP2` = '{gap_2}' WHERE (`ID` = '{line}');"
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, db=DB_NAME)
        cur = conn.cursor()
        cur.execute(query)
        data=cur.fetchall()
        for firstdata in data:
            trigger=firstdata[0]
           # inspect=firstdata[1]
        conn.close()
    except Exception as E:
        print(E)
       # logger.critical(str(E))
    return trigger



def updateIntoDB(trigger,inspect):
    global DB_USER,DB_NAME,DB_PASS,DB_HOST
    try:
        query=f"UPDATE `railclip_db`.`trigger` SET `trigger1` = 'TRUE' , inspect='{inspect}' WHERE (`ID` = '1');"
      #  query=f"UPDATE `railclip_db`.`history` SET `LENGTH` = '{length}', `WIDTH` = '{width}', `GAP1` = '{gap_1}', `GAP2` = '{gap_2}' WHERE (`ID` = '{line}');"
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, db=DB_NAME)
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
        conn.close()
    except Exception as E:
        print(E)
       # logger.critical(str(E))

# p1=subprocess.Popen(['python',"MODBUS_READ_WRITE.py"])
def initClient():
    client = ModbusTcpClient("192.168.1.5", port=502, timeout=10)
    client.connect()
    return client
def closeClient():
    if client is not None:
        client.close()
    
########################################### READ METHODS ########################################################
def readFromPlc(register):  
    global client
    try:
        result = client.read_holding_registers(address =register ,count=1)
        
        val=result.registers
        return val[0]
    except Exception as e:
        print(f"error while reading from plc :{register} _ {e}")
        

##################################### WRITE METHODS ######################################################

def writeToPlc(register,val):
    global client
    try:
        time.sleep(0.01)
        client.write_register(address = register,value=val)
        time.sleep(0.01)
        # print(f"write value is {val} for register {register} written sucessfully_1")
    except Exception as e:
        print(f"Error while writing value :{register} _ {e}")


##################################### WRITEAGAIN METHODS ######################################################
        
# 1. Setup of logging environment for better trouble shooting
client=initClient()


#start cycle
CHECK_START_SIGNAL_REGISTER=4100
TRIGGER_INPUT0_ACT_REGISTER=4098
TRIGGER_INPUT1_ACT_REGISTER=4099
TRIGGER_INPUT2_ACT_REGISTER=4101
LASER_REGISTER=4103
LIGHT_REGISTER=4102
OUT0_REGISTER=4108
OUT1_REGISTER=4109
OUT2_REGISTER=4107
SERVO_ON_REGISTER=4112
SERVO_RESET=4113
SERVO_SETUP=4114
DRIVE_REGISTER=4115
OUT_INP_REGISTER=4110
STOP_TIMER=15 #in mins
INP_WAIT_TIMEOUT=5 #seconds

start_cycle=False
startTime=int(time.time())

def TRIGGER_ACT_SETUP():
    global SERVO_SETUP
    try:
        writeToPlc(SERVO_SETUP,1)
        time.sleep(0.01)
        writeToPlc(SERVO_SETUP,0)

    except Exception as e:
        print(f"TRIGGER_ACT_SETUP:{e}")
        print(traceback.format_exc())
        logger.critical()

def RETURN_TO_ORIGIN():
    global SERVO_ON_REGISTER
    try:
        retstatus=False
        ctr=0
        while ctr<=10:
            SERVON_STATUS=int(readFromPlc(SERVO_ON_REGISTER))
            if SERVON_STATUS==1:
                TRIGGER_ACT_SETUP()
                #wait for INP signal 
                waitStart=int(time.time())
                while int(time.time()-waitStart)<=INP_WAIT_TIMEOUT:
                    inpRead=int(readFromPlc(OUT_INP_REGISTER))
                    if inpRead==1:
                        retstatus=True
                        ctr=100
                        break
                    time.sleep(0.01)
                
            else:
                writeToPlc(SERVO_ON_REGISTER,1)
            ctr+=1
        return(retstatus)
    except Exception as e:
        print(f"RETURN_TO_ORIGIN:{e}")
        print(traceback.format_exc())
        return(None)

def singnalDelay(tm=0.01):
    time.sleep(tm)

def POSITION_ACT(stepNumber):
    try:
        global TRIGGER_INPUT0_ACT_REGISTER,TRIGGER_INPUT1_ACT_REGISTER,TRIGGER_INPUT2_ACT_REGISTER,INP_WAIT_TIMEOUT
        reqTRIGGER=None
        reqDelay=0.1
        retstatus=False
        if stepNumber==0:
            reqTRIGGER=TRIGGER_INPUT0_ACT_REGISTER
        elif stepNumber==1:
            reqTRIGGER=TRIGGER_INPUT1_ACT_REGISTER
            reqDelay=1.26
        elif stepNumber==2:
            reqTRIGGER=TRIGGER_INPUT2_ACT_REGISTER
        else:
            print("Invalid stepnumer")
            return(False)
        if reqTRIGGER is not None:
            writeToPlc(reqTRIGGER,1)
            singnalDelay(0.02)
            writeToPlc(DRIVE_REGISTER,1)
            singnalDelay(reqDelay)
            writeToPlc(DRIVE_REGISTER,0)
            writeToPlc(reqTRIGGER,0)
            #wait for INP signal 
            waitStart=int(time.time())
            while int(time.time()-waitStart)<=INP_WAIT_TIMEOUT:
                inpRead=int(readFromPlc(OUT_INP_REGISTER))
                if inpRead==1:
                    retstatus=True
                    
                    break
                # print(F"STEP {stepNumber}: {inpRead}")
        return(retstatus)
        
    except Exception as e:
        print(f"POSITION_ACT {stepNumber}:{e}")
        print(traceback.format_exc())
        return(None)


TMP_SAV=False


class Errors(Exception):
    pass

class CAMERA_PARAMETER_INVALID_VALUE(Errors):
    def __init__(self):
        self.msg="The parameter in camera configuration XML is invalid"
        
# 1. Setup of logging environment for better trouble shooting
from cx.device import Device
from cx.device_factory import DeviceFactory
import cx.cx_cam as cam
import cx.cx_base as base

# writeZEROPlc(4102,0)
# writeAgainPlc(4103,1)
logging.basicConfig(level=logging.CRITICAL)
device: Optional[Device] = None

def setCamParam(device,param,paramType,configRoot):
    try:
        ReqParameter=configRoot.find(param) if configRoot.find(param) is not None else ""
        if ReqParameter!="":
            ReqParameterVal=ReqParameter.text
            #convert parameter
            finalParamVal=None
            if paramType=="INT":
                finalParamVal=int(ReqParameterVal)
            elif paramType=="BOOL":
                finalParamVal=bool(ReqParameterVal)
            else:
                finalParamVal=str(ReqParameterVal)
            print(device.getParam(ReqParameter))
            device.setParam(param,finalParamVal)
            print(device.getParam(ReqParameter))
            return(device)
        else:
            raise CAMERA_PARAMETER_INVALID_VALUE
    except CAMERA_PARAMETER_INVALID_VALUE as error:
        print(error.msg)
        print(traceback.format_exc())
    except Exception as e:
        print(e)
        print(traceback.format_exc())        
        
def grabImage():
    # 4.1 Grab image buffer, wait for image with optional timeout
    dev_buffer = device.waitForBuffer(10000)
    if dev_buffer is None:
        logging.error("Failed to get buffer")
        exit(0)
    # 4.2 get image from buffer
    # the img object holds a reference to the data in the internal buffer, if you need the image data after cx_queueBuffer you need to copy it!
    img = dev_buffer.getImage()
    if img is None:
        logging.error("Failed get image from buffer")
        exit(0)
    # copy img.data
    img_data = np.copy(img.data)
    # 4.3 Queue back the buffer. From now on the img.data is not valid anymore and might be overwritten with new image data at any time!
    if dev_buffer.queueBuffer() is False:
        logging.error("Failed to queue back buffer")
        exit(0)
    return img_data

devices = DeviceFactory.findDevices()
if len(devices) < 1:
    print("No cameras found")
    exit(0)
print(len(devices))
# Connecting first device via factory returns a Device object

device = DeviceFactory.openDevice(devices[0].DeviceUri)
try:
    if 'C6-2040' in devices[0].DeviceModel:
        print("3d cam")
        if device is None:
            print(f"Could not connect to camera device {devices[0].DeviceModel} - {devices[0].DeviceIP}")
            exit(0)
        print(f"Successfully connected to camera device {devices[0].DeviceModel} - {devices[0].DeviceIP}")
    else:
        device.close()
        device = DeviceFactory.openDevice(devices[1].DeviceUri)
        if device is None:
            print(f"Could not connect to camera device {devices[1].DeviceModel} - {devices[1].DeviceIP}")
            exit(0)
        print(f"Successfully connected to camera device {devices[1].DeviceModel} - {devices[1].DeviceIP}")
    
       
except:
    pass

#PLC Registers
#4098- 4099 4101- actuator
#cycle start 4100
#4102 light
#4103- laser
homePosStatus=RETURN_TO_ORIGIN()
writeToPlc(LIGHT_REGISTER,0)
singnalDelay()
writeToPlc(LASER_REGISTER,1)
singnalDelay()
if homePosStatus is True:
    logger.critical("Actuator at Origin.")


mode=device.getParam("DeviceScanType")
device.setParam("DeviceScanType","Linescan3D")
device.setParam("ExposureTime",600.0)
device.setParam("ComponentSelector","Range")#"Range"
#linescan capture
# 2. Allocate and queue internal buffers.
if device.allocAndQueueBuffer(64) is False:
    # Further error messages are logged by the Device class
    exit(0)

# 3. Start acquisition.
if device.startAcquisition() is False:
    exit(0)
ctr=0
imageToStich=[]
Stiched_image=None
fctr=int(time.time())
stop_once=False
started=False
START=0
cnt=0
once=True
#writeAgainPlc(4103,1)
IMG_STICH_COUNT = 5
START_FRAME = 4
# reset positions
position1Status=False
position2Status=False
homePosStatus=False
resetToOrg=False
reruncycle=False
frame_counter=0
while True:
    
    if client.connected==True:
        img_data = grabImage()
        if (readFromPlc(CHECK_START_SIGNAL_REGISTER)==1 and started is False) or reruncycle is True:
            START=int(time.time())*1000
            started=True
            reruncycle=False
            resetToOrg=False
            frame_counter=0
            # time.sleep(0.1)
            writeToPlc(LIGHT_REGISTER,0)
            singnalDelay()
            writeToPlc(LASER_REGISTER,1)
            singnalDelay()
            position1Status=POSITION_ACT(0)
            if position1Status is True:
                position2Status=POSITION_ACT(1)
                if position2Status is not True:
                    print(f"Position 2 not reached. Reset cycle.")
                    resetToOrg=True
                    reruncycle=True
            else:
                print(f"Position 1 not reached. Reset cycle.")
                resetToOrg=True
                reruncycle=True
        if resetToOrg is True or reruncycle is True:
            homePosStatus=RETURN_TO_ORIGIN()
            if homePosStatus is True:
                started=False
                once=True
                ctr=0
                imageToStich=[]
                Stiched_image=None
                fctr=int(time.time())
                frame_counter=0
                logger.critical("Error in actuator, reset cycle triggered.")
            else:
                started=False
                once=True
                ctr=0
                imageToStich=[]
                Stiched_image=None
                fctr=int(time.time())
                frame_counter=0
                logger.critical("Error in returning to home position.")
            continue


        if len(imageToStich)==IMG_STICH_COUNT and started is True:
            # writeZEROPlc(4099,0)
            # time.sleep(0.02)
            writeToPlc(LASER_REGISTER,0)
            singnalDelay()
            writeToPlc(LIGHT_REGISTER,1)
            Stiched_image=cv2.vconcat(imageToStich)
            folderpath=f"C:/INSIGHTZZ/RAILCLIP/RAILCLIP1/IMAGES_3D/{START}"
            if not os.path.exists(folderpath) :
                os.makedirs(folderpath)
            fname=f"{folderpath}/IMG_{START}_{fctr}.tif"
            #+fname=os.path.join(f"C:/INSIGHTZZ/RAILCLIP/RAILCLIP1/IMAGES_3D/{START}/IMG_{START}_{fctr}.tif")
            cv2.imwrite(fname,Stiched_image)
            imageToStich=[]
            once_reverse=True
            print("3D stop"+str(int(time.time())*1000))
            once=True
            started=False
            time.sleep(0.5)
            fd=open("START_3D.txt",'w')
            fd.write(str(START))
            fd.flush()
            fd.close()
            try:
                os.rename("START_3D.txt","C:/INSIGHTZZ/RAILCLIP/RAILCLIP1/TRIGGER/START_3D.txt")
                updateIntoDB(trigger="TRUE",inspect=START)
            except:
                pass
            fd=open("start.txt",'w')
            fd.write(str(START))
            fd.flush()
            fd.close()
            time.sleep(0.7)
            # if not os.path.exists('C:/INSIGHTZZ/RAILCLIP/RAILCLIP1/Algorithm/start.txt'):
            #     os.rename('start.txt','C:/INSIGHTZZ/RAILCLIP/RAILCLIP1/Algorithm/start.txt')
            # else:
            #     os.remove('C:/INSIGHTZZ/RAILCLIP/RAILCLIP1/Algorithm/start.txt')
            #     os.rename('start.txt','C:/INSIGHTZZ/RAILCLIP/RAILCLIP1/Algorithm/start.txt')
        if started==True and len(imageToStich)<=IMG_STICH_COUNT:
            frame_counter=frame_counter+1
            current_time=int(time.time())*1000
            
            # print(img_data.shape)
            if frame_counter>=START_FRAME and frame_counter<=IMG_STICH_COUNT+START_FRAME: 
                imageToStich.append(img_data)
        if started is False and once is True :
            # if  trigger_fetch == "FALSE":
            once=False
            print("enter in trigger ______________________")  
            homePosStatus=POSITION_ACT(2)
            if homePosStatus is True:
                writeToPlc(LIGHT_REGISTER,0)
                singnalDelay()
                writeToPlc(LASER_REGISTER,1)
                singnalDelay()
                print("Home position reached")
            else:
                print("Home position not reached.")

    else:
        client.close()
        time.sleep(1)
        client=initClient()

if device.stopAcquisition() is False:
    exit(0)

# 6. cleanup
if device.freeBuffers() is False:
    exit(0)

device.close()
