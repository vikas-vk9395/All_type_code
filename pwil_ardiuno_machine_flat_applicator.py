from tendo import singleton
me = singleton.SingleInstance()

import os
import logging
import time
import sys, select, os
import serial
import tendo
import pymysql
import datetime
from datetime import datetime

import re

import pymysql
import webbrowser
import datetime
from datetime import date, datetime, timedelta
plcLastStoppedDateTime = datetime.now()
import sys
import json

#for copying files
import shutil
#for calling shell script
import subprocess
import signal

#For logging error
import logging
import traceback

db_user = 'root'
db_pass = 'insightzz123'
db_host = 'localhost'
db_name = 'PWIL_SURFACE_DEFECT_DB'

code_path = "/home/surface-defect/Insightzz/code/Algorithm/INFERENCE_TESTING/"
#Logging module
falogger = None
logging.basicConfig(filename=code_path+"ArdLog.log",filemode='a',format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
falogger=logging.getLogger("DEFECTLOG1_")
falogger.setLevel(logging.CRITICAL) #CRITICAL #DEBUG


processID = os.getpid()
print("This process has the PID", processID)
falogger.critical("This process has the PID"+str(processID))

def updateProcessId(processId):
    try:
        db_update = pymysql.connect(host=db_host,    # your host, usually localhost
                     user=db_user,         # your username
                     passwd=db_pass,  # your password
                     db=db_name)
        cur = db_update.cursor()
        query = "UPDATE PROCESS_ID_TABLE set PROCESS_ID = " + \
            str(processId) + " where PROCESS_NAME = 'ARDUINO'"
        cur.execute(query)
        db_update.commit()
        cur.close()
    except Exception as e:
        print('Exception in updateProcessId: '+str(e))
        falogger.critical('Exception in updateProcessId: '+str(e))

updateProcessId(processID)

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

ard_val_once1 = None
ard_val_once2 = None
ard_val = 11

counter=0
counter1=0
#counter2=0
#counter3=0

while True:
    #====== pressing enter will break loop ===========#
#    os.system('cls' if os.name == 'nt' else 'clear')
    #if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
      #  line = raw_input()
       # break
    try:
        #=========== For machine input =========#
        try:
            ard_value = int(ser.readline())
            
            ard_val_once1 = ard_value
            ard_value = 10
           # if ard_value == 10:
            if ard_val_once1 != ard_val_once2:
                print("ard_value is",ard_value)
                #ard_val_once2 = ard_val
                ard_val_once2 = ard_val_once1
                
                ##===================================== change sql row SE0101===========================================##
                if ard_value == 10 :
                    #ard_val_once2 = ard_val
                    def add_to_sql(counter):
                        b1 = (datetime.now().strftime('%y-%m-%d-')+str(counter))
                        print("b1=======",b1)
                        datetimevar = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        try:
                            db_select = pymysql.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
                            cur = db_select.cursor()
                            query = "SELECT WIRE_SIZE, WIRE_THICKNESS, PROD_NUMBER, OPERTOR_NAME, CUSTOMER_NAME, CPR, WIRE_TYPE, SHIFT, DEFECT_SIZE, CREATE_DATETIME, IS_ACTIVE_CONFIG FROM CONFIG_TABLE WHERE IS_ACTIVE_CONFIG = '1'"
                            cur.execute(query)
                            data_set = cur.fetchall()
                            cur.close()

                            try:
                                db_update = pymysql.connect(host=db_host,    # your host, usually localhost
                                             user=db_user,         # your username
                                             passwd=db_pass,  # your password
                                             db=db_name)
                                cur = db_update.cursor()
                                query = "update CONFIG_TABLE set IS_ACTIVE_CONFIG=0"
                                cur.execute(query)
                                db_update.commit()
                                cur.close()
                            except Exception as e:
                                print('Exception : ',e)                            
                            try:
                                db_insert = pymysql.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
                                cur = db_insert.cursor()
                                query = "INSERT INTO CONFIG_TABLE (WIRE_SIZE, WIRE_THICKNESS, PROD_NUMBER, OPERTOR_NAME, CUSTOMER_NAME, CPR, WIRE_TYPE, SHIFT, DEFECT_SIZE, CREATE_DATETIME, IS_ACTIVE_CONFIG) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                                values = (data_set[0][0],data_set[0][1], b1, data_set[0][3], data_set[0][4], data_set[0][5], data_set[0][6], data_set[0][7], data_set[0][8], datetimevar, '1')
                                print("insert query is :",query)
                                cur.execute(query, values)
                                db_insert.commit()
                                cur.close()
                            except Exception as e:
                                print(e)                                
                           
                    
                        except Exception as e:
                            print(e)
                    #if data_s 
                    try:
                        db_select = pymysql.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
                        cur = db_select.cursor()
                        query = "SELECT PROD_NUMBER,CREATE_DATETIME FROM CONFIG_TABLE WHERE IS_ACTIVE_CONFIG = '1'"
                        cur.execute(query)
                        data_set = cur.fetchall()
                        cur.close() 
                        var = data_set[0][0]
                        print("var is:",var)
                        #last_two_digits =var[-2:]
                        #print(last_two_digits)  # Output: "33"  
                        datetime_str = data_set[0][1]
                        date_str = datetime_str[:10]
                        print(f"data_set[0][0] :{data_set[0][0]}, data_set[0][1] : {date_str}")
                        last_number = re.findall(r'\d+', var)[-1]
                        
                        integer_value = int(last_number)
                        print("integer_value",integer_value)
                        
                        dateTimevar = str(datetime.now().strftime('%Y-%m-%d'))
                        if date_str == dateTimevar:
                            counter=integer_value+1 
                            add_to_sql(counter) 
                            print("Same Date")
                        else:
                            counter=counter+1 
                            add_to_sql(counter) 
                        print("=================change sql row SE0-103=================")    
                    except Exception as e:
                        print(e)                        
                    #counter=counter+1 
                    #add_to_sql(counter)             
                    
                               
                else:
                    
                    print("No value1 ")
                    pass
            else:
                pass
                        
        except:
            time.sleep(5)
            ard_val_once2 = ard_val
            #print("No value ")
            pass
            #print("No value ")
    except:
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
