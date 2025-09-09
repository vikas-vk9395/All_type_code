import cv2
import os
#============================= Getting data from xml ==========================================#
config_path = os.path.join("/home/viks/Insightzz/CODE/Algoritham/RAWAN_ULTRATECH/detection_CAM12.xml")
import ast
import xml.etree.ElementTree as ET
config_parse = ET.parse(config_path)
config_root = config_parse.getroot()
code_path = config_root[0].text

#DB credentials
import pymysql
db_user = config_root[1].text
db_pass = config_root[2].text
db_host = config_root[3].text
db_name = config_root[4].text

def updatePlc_healthStatus(plcStatus):
    try:
        db_update = pymysql.connect(host=db_host,    # your host, usually localhost
                     user=db_user,                   # your username
                     passwd=db_pass,                 # your password
                     db=db_name)
        cur = db_update.cursor()
        query = f"UPDATE HELTH_STATUS set PROCESS_ID = {str(plcStatus)} where PLC_STATUS = 'ALGORITHM_CONVEYOR'"
        cur.execute(query)
        db_update.commit()
        cur.close()
        db_update.close()
        #print(data_set)
    except Exception as e:
        print(f"Exception in updatePlc_healthStatus : {e}")
        #dalogger.critical(f"Exception in update process id : {e}")


def updatePlc_service():
    try:
        if os.system("ping 192.168.1.5"):
            print("PLC Connected")
            updatePlc_healthStatus(ACTIVE)
        else:
            print("PLC Not Connected")
            updatePlc_healthStatus(ACTIVE)
    except Exception as e:
        print("Excrption in updatePlc_service",e)
        #dalogger.critical(f"transfer error : {e}")        
    
        
if __name__ == '__main__':
    updatePlc_service()
        