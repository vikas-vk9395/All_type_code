#for single instance
from tendo import singleton
me = singleton.SingleInstance()

import time
import sys, select, os
import serial
from mysql.connector import Error
import mysql.connector
import datetime
import logging

#for calling shell script
import subprocess
import signal

#for getting process id
import mysql.connector
from mysql.connector import Error

processID = os.getpid()
print("This process has the PID", processID)

INF_SCRIPT_POST_PATH = "/home/pwilsil03/Insightzz/code/Algorithms/ShellScripts/start_inf_post.sh"
POST_FRAMES_PATH = "/home/pwilsil03/Insightzz/code/Algorithms/FrameCapture/start_all_cam_post.sh"
ser = None
try:
    ser = serial.Serial('/dev/ttyACM0',9600,timeout = 1)
    time.sleep(3)
except:
    try:
        ser = serial.Serial('/dev/ttyACM1',9600,timeout = 1)
        time.sleep(3)
    except:
        try:
            ser = serial.Serial('/dev/ttyACM2',9600,timeout = 1)
            time.sleep(3)
        except Exception as e:
            print("Ardiuno Error :"+str(e))

logging.basicConfig(filename="/home/pwilsil03/Insightzz/code/Algorithms/ServiceCode/PWIL_SERVICE_POST.log",filemode='a',format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ser_logger=logging.getLogger("PWIL_SERVICE_POST")
ser_logger.setLevel(logging.DEBUG)
ser_logger.debug("PWIL_SERVICE STARTED")

class NumpyMySQLConverter(mysql.connector.conversion.MySQLConverter):
    """ A mysql.connector Converter that handles Numpy types """

    def _float32_to_mysql(self, value):
        return float(value)

    def _float64_to_mysql(self, value):
        return float(value)

    def _int32_to_mysql(self, value):
        return int(value)

    def _int64_to_mysql(self, value):
        return int(value)


config = {
    'user': 'root',
    'host': 'localhost',
    'password': 'insightzz123',
    'database': 'PWIL_DB'
}


def checkInferenceStatus():
    #ser_logger.debug("Inside checkInferenceStatus")
    try:
        mySQLconnection = mysql.connector.connect(**config)
        mySQLconnection.set_converter_class(NumpyMySQLConverter)
        sql_select_Query = "select PROCESS_ID from PWIL_DB.PROCESS_ID_TABLE where PROCESS_NAME IN ('CTC_INFERENCE', 'SURFACE_DEFECT_POST_INFERENCE', 'POST_CTC_TOP_CAM','POST_CTC_BOTTOM_CAM');"
        cursor = mySQLconnection .cursor()
        cursor.execute(sql_select_Query)
        records = cursor.fetchall()
        #print("Total number of rows is - ", records)
        for row in records:
            if row[0] > 0:
                #terminating processes
                try:
                    #print(row[0])   
                    os.kill(int(row[0]), signal.SIGKILL)
                except Exception as e:
                    pass
                    #print('Exception : ',e)
                    #ser_logger.critical("Error in main window close func:"+ str(e))                    
            else:
                pass
        cursor.close()
    except Error as e:
        print("checkInferenceStatus() : Error while connecting to MySQL", e)
    finally:
        # closing database connection.
        if(mySQLconnection .is_connected()):
            mySQLconnection.close()

def restartAllScripts():
    print("Inside restartAllScripts")
    ser_logger.debug("Inside restartAllScripts")
    try:
        subprocess.call(['sh', POST_FRAMES_PATH])
        time.sleep(2)
        subprocess.call(['sh', INF_SCRIPT_POST_PATH])
        ser_logger.debug("restartAllScripts started")
        print("restartAllScripts started")
    except Exception as e:
        print('Exception : ',e)
        ser_logger.critical("Error in start algo post func: calling post inference code : "+ str(e))

def updateProcessId(processId):
    try:
        mySQLconnection = mysql.connector.connect(**config)
        mySQLconnection.set_converter_class(NumpyMySQLConverter)
        sql_update_query = "UPDATE PROCESS_ID_TABLE set PROCESS_ID = " + \
            str(processId) + " where PROCESS_NAME = 'PWIL_SERVICE_POST'"
        cursor = mySQLconnection.cursor()
        result = cursor.execute(sql_update_query)
        # print("Update Result is ", result)
        mySQLconnection.commit()
    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        # closing database connection.
        if(mySQLconnection .is_connected()):
            mySQLconnection.close()

def main():
    global ser
    isConnected = False
    ard_value = 0
    print("Inside Main function")
    ser_logger.debug("Inside main()")
    while True:
        #ser_logger.debug("Inside main")
        #time.sleep(0.001)
        try:
            #=========== For machine input =========#
            try:
                ard_value = int(ser.readline())
            except:
                ard_value = 0
                isConnected = False
                print("Inner Exception")
            if ard_value == 1 and isConnected is False:
                isConnected = True 
                print("signal received")
                ser_logger.debug("signal received")
                checkInferenceStatus() 
                ser_logger.debug("Starting All Script 111")
                restartAllScripts()  
            elif ard_value == 0 and isConnected == False:
                checkInferenceStatus()
                #print("No Signal")
             
        except:
            ser_logger.debug("inside main exception")
            try:
                ser = serial.Serial('/dev/ttyACM0',9600,timeout = 1)
                time.sleep(3)
            except:
                try:
                    ser = serial.Serial('/dev/ttyACM1',9600,timeout = 1)
                    time.sleep(3)
                except:
                    try:
                        ser = serial.Serial('/dev/ttyACM2',9600,timeout = 1)
                        time.sleep(3)
                    except Exception as e:
                        print("Ardiuno Error :"+str(e))  


if __name__ == '__main__':
    updateProcessId(processID)
    main()  
