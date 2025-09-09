import os
import logging
import traceback
import time
import datetime
from logging import handlers
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
import pymysql
import requests
import json
import base64

''' UI Process ID and Base Code Path '''
BASE_PATH = os.getcwd()

debugMode=False
log_name="1_"+os.path.basename(__file__[:-2])+"-1"+"log"
logger=logging.getLogger(log_name[:-4])
if debugMode==True:
    log_level=logging.DEBUG
else:
    log_level=logging.ERROR

logger.setLevel(log_level)
log_format=logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log_fl=handlers.RotatingFileHandler(log_name,maxBytes=104857600,backupCount=3) # 1MB log files max
log_fl.setFormatter(log_format)
log_fl.setLevel(log_level)
logger.addHandler(log_fl)
logger.critical("Mail Service Module Initialized")

'''Databese Details '''
db_user = 'root'
db_pass = 'insightzz123'
db_host = 'localhost'
db_name = 'MANIKGARH_CONVEYOR_DB'
if debugMode is True:
    db_pass = 'insightzz123'

PLANT_NAME = "ManikgarhCementPlant"
PROJECT_NAME = "ConveyorInspection"
MODULE_NAME = "MAIL_SMS_MODULE"

BASE_REPORT_PATH = "/home/insightzz-conveyor-01/insightzz/Code/MailService/ReportData/"
HTTP_LINK =  "http://www.insightzz-ultratech.com/SMSModule/"
# BASE_REPORT_PATH = "/home/vikram/Insightzz/eclipse-python-workspace/ConveyorInspection/src/mail/"
        
def fetchDefectListforGivenDateTime(startDate, endDate):
    data_set = []
    try:
        db_select = pymysql.connect(host=db_host,user=db_user,passwd=db_pass,db=db_name)
        cur = db_select.cursor()
        query = f"SELECT DEFECT_TYPE FROM MANIKGARH_CONVEYOR_DB.IMAGE_PROCESSING_TABLE where timestamp(CREATE_DATETIME) > timestamp('{startDate}') and timestamp(CREATE_DATETIME) <= timestamp('{endDate}') group by DEFECT_TYPE;"
        cur.execute(query)
        data_set = cur.fetchall()
    except Exception as e:
        logger.error(f"fetchDefectListforGivenDateTime() Exception is : {e}")
    finally:
        cur.close()
        db_select.close()
    return data_set

def break_list_of_strings(strings):
    sublists = []
    current_sublist = []

    for string in strings:
        if sum(len(s) for s in current_sublist) + len(string) <= 30:
            current_sublist.append(string)
        else:
            sublists.append(current_sublist)
            current_sublist = [string]

    if current_sublist:
        sublists.append(current_sublist)

    return sublists

def sendSMSToServer(startDate, endDate):
    try:
        json_data = {}
        projectName = "Conveyor"
        siteName = "1"
        userList = []
        
        # startDate = "2023-04-19 12:12:10"
        # endDate = "2023-06-01 00:51:32"
        
        message = ""
        defectList = fetchDefectListforGivenDateTime(startDate, endDate)
        defectListNew = []
        for item in defectList:
            defectListNew.append(item[0])
        sublists = break_list_of_strings(defectListNew)
        print(sublists)
        if len(sublists) == 0:
            insertIntoLogDetailTable("OK_STATUS", f"No Defect Found between date {startDate} To {endDate}", "sendSMSToServer", "")
            return
        insertIntoLogDetailTable("OK_STATUS", f"SMS sent between date {startDate} To {endDate}", "sendSMSToServer", "")
        for item in sublists:
            message = ",".join(str(item) for item in item)
            
            json_data["projectName"] = projectName
            json_data["siteName"] = siteName
            json_data["message"] = message
            json_data["userList"] = userList
            
            # print(json_data)
            ''' Send Data JSON file to Server '''
            url_post = f"{HTTP_LINK}AjaxRequestController?apiName=sendSMS"
            ''' A POST request to the API '''
            post_response = requests.post(url_post, json=json_data)
            
            ''' Print the response '''
            post_response_json = post_response.json()
            logger.critical(f"sendSMSToServer() post_response_json data for {message} is : {post_response_json} ")
            time.sleep(5)
            
    except Exception as e:
        logger.critical(f"sendSMSToServer() Exception is : {e} ")
        insertIntoLogDetailTable("NOT_OK_STATUS", f"Exception in sending SMS between date {startDate} To {endDate}", "sendSMSToServer", str(e))


def mainFunction():
    while True:
        try:            
            ''' Mail Sending Code At every Hour '''
            todaysDate = datetime.datetime.now().strftime("%Y-%m-%d %H")  
            start_time_str = f"{todaysDate}:00:00"
            end_time_str = f"{todaysDate}:00:10"
            # start_time_str = f"2023-10-18 12:00:10"
            start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
            end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
            one_hours_ago = start_time - datetime.timedelta(hours=4)
            # print(f"sending Mail {datetime.datetime.now()}")
            # if True:
            if datetime.datetime.now() < end_time and datetime.datetime.now() > start_time:
                ''' Send SMS to users '''
                date, timeStr = start_time_str.split(" ")
                # Split the time component to extract the hour
                hour = timeStr.split(":")[0]
                if hour in ["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","23"]:
                    print(f"sending Mail {datetime.datetime.now()}")
                    sendMails(one_hours_ago,start_time)
                    # sendSMSToServer(one_hours_ago,start_time)
                # sendMails("2023-04-19 12:12:10","2023-04-19 16:52:14")
                time.sleep(10)
            time.sleep(2)    
            
        except Exception as e:
            logger.error(f"mainFunction() Inside While Exception is : {e}")

def fetchReportDetails(startDateTime, endDateTime):
    data_set = []
    try:
        db_select = pymysql.connect(host=db_host,user=db_user,passwd=db_pass,db=db_name)
        cur = db_select.cursor()
        query = f"SELECT DEFECT_TYPE, DEFECT_SIDE, DEFECT_LOCATION, count(DEFECT_TYPE) as COUNT FROM MANIKGARH_CONVEYOR_DB.IMAGE_PROCESSING_TABLE where DISTANCE_IN_METER >= 2 and timestamp(CREATE_DATETIME) >= timestamp('{startDateTime}') and timestamp(CREATE_DATETIME) < timestamp('{endDateTime}') group by DEFECT_TYPE order by DEFECT_SIDE desc;"
        cur.execute(query)
        data_set = cur.fetchall()
    except Exception as e:
        logger.error(f"fetchReportDetails() Exception is : {e}")
    finally:
        cur.close()
        db_select.close()
    return data_set

def fetchCompleteReportDetails(startDateTime, endDateTime):
    data_set = []
    try:
        db_select = pymysql.connect(host=db_host,user=db_user,passwd=db_pass,db=db_name)
        cur = db_select.cursor()
        query = f"SELECT DEFECT_TYPE, DEFECT_SIDE, DISTANCE_IN_METER, DEFECT_LOCATION, CREATE_DATETIME, IMAGE_PATH FROM MANIKGARH_CONVEYOR_DB.IMAGE_PROCESSING_TABLE where DISTANCE_IN_METER >= 2 and timestamp(CREATE_DATETIME) >= timestamp('{startDateTime}') and timestamp(CREATE_DATETIME) < timestamp('{endDateTime}') order by DEFECT_SIDE desc;"
        cur.execute(query)
        data_set = cur.fetchall()
    except Exception as e:
        logger.error(f"fetchReportDetails() Exception is : {e}")
    finally:
        cur.close()
        db_select.close()
    return data_set

def insertIntoLogDetailTable(LOG_TYPE, MESSAGE, FUNCTION_NAME, EXCEPTION_DETAILS):
    dbconnection = None
    cur = None
    try:
        dbconnection = pymysql.connect(host=db_host,user=db_user,passwd=db_pass,db=db_name)
        cur = dbconnection.cursor()
        query = f"insert into LOG_DETAIL_TABLE(PLANT_NAME,PROJECT_NAME,MODULE_NAME,LOG_TYPE,MESSAGE,FUNCTION_NAME,EXCEPTION_DETAILS) values('{PLANT_NAME}','{PROJECT_NAME}','{MODULE_NAME}','{LOG_TYPE}','{MESSAGE}','{FUNCTION_NAME}','{EXCEPTION_DETAILS}')"
        cur.execute(query)
        dbconnection.commit()
    except Exception as e:
        logger.critical(f"insertIntoLogDetailTable() Exception is : {e}")
    finally:
        dbconnection.close()
        cur.close()

def sendMails(start_time,end_time):
    try:
        # Set the sender's and recipient's email addresses and credentials
        sender_email = "insightzz.ultratech.reports@gmail.com"
        sender_password = "hwnpcbdtknuojdix"
        # receiver_email = ['vikram.jethmal@insightzz.com']
        receiver_email = ['vikram.jethmal@insightzz.com', "harshal.wadikar@insightzz.com", "prashant.meshram@adityabirla.com","nv.mande@adityabirla.com","kishor.upganlawar@adityabirla.com","sachin.wandhare@adityabirla.com","shyam.mohitkar@adityabirla.com","dharmesh.thakur@adityabirla.com","jp.pandey@adityabirla.com","chetan.urkude@adityabirla.com"]
        todaysDate = datetime.datetime.now().strftime("%Y-%m-%d")
        startDate = start_time 
        endDate = end_time  
         
        # Create a message object
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = ", ".join(receiver_email)
        message['Subject'] = f"Conveyor Report from : {startDate} To {endDate}"
        
        data_set = fetchReportDetails(startDate, endDate)
        if len(data_set) == 0:
            logger.debug(f"No defect found between  {startDate} To {endDate}")
            insertIntoLogDetailTable("OK_STATUS", f"No Defect Found between date {startDate} To {endDate}", "sendMails", "")
            return
        insertIntoLogDetailTable("OK_STATUS", f"Email is sent between date {startDate} To {endDate}", "sendMails", "")
        table_html = ""
        for item in data_set:
            defect_type = item[0]
            table_html += "<tr>"
            table_html += "<td>{}</td>".format(defect_type.title())
            defect_side = item[1]
            table_html += "<td>{}</td>".format(defect_side)
            location = item[2]
            table_html += "<td>{}</td>".format(location)
            defect_count = item[3]
            table_html += "<td>{}</td>".format(defect_count)
            table_html += "</tr>"
        # print(table_html)

        # Add the message body
        HTML = "<!DOCTYPE html> <html> <head> <meta charset='utf-8' /> <style type='text/css'>  table { background: white; border-radius:3px; border-collapse: collapse; height: auto; max-width: 900px; padding:5px;  width: 100%; animation: float 5s infinite; } th { color:#D5DDE5;; background:#1b1e24;  border-bottom: 4px solid #9ea7af;  font-size:14px;font-weight: 300; padding:10px;text-align:center;vertical-align:middle;}tr {  border-top: 1px solid #C1C3D1;border-bottom: 1px solid #C1C3D1;border-left: 1px solid #C1C3D1; color:#666B85;font-size:16px;font-weight:normal;} tr:hover td {background:#4E5066;  color:#FFFFFF; border-top: 1px solid #22262e; } td {background:#FFFFFF;  padding:10px;  text-align:left; vertical-align:middle;font-weight:300; font-size:13px; border-right: 1px solid #C1C3D1; } </style> </head> <br> <table> <thead> <tr style='border: 1px solid #1b1e24;'> <th>Defect Type</th> <th>Camera Top/Bottom</th> <th>Position</th> <th>Defect Count</th> </tr> </thead> <tbody> "+table_html+"</table> <br> </html>"
        body = "Dear All, <br><br>Please find attached Conveyor Report from : " + str(startDate) +" To "+str(endDate)+" <br>Attachment Name : \"Conveyor_Report_"+str(endDate)+".csv\" <br><br>Below are the list & count of defect detected for Conveyor . <br> "+HTML+"  <br>Thanks & Regards <br>Insightzz Team "
        
        message.attach(MIMEText(body, 'html'))
        DOWNLOAD_PATH = BASE_REPORT_PATH
        data_set = fetchCompleteReportDetails(startDate, endDate)
        if not os.path.exists(DOWNLOAD_PATH+(todaysDate)):
            os.makedirs(DOWNLOAD_PATH+(todaysDate))
        
        DOWNLOAD_PATH = DOWNLOAD_PATH+(todaysDate)
        tag = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = "Conveyor_Report_"+tag+".csv"
        #csv_path = DOWNLOAD_PATH+(todaysDate)+"/"+ file_name
        csv_path = DOWNLOAD_PATH +"/"+ file_name
                 
        f = open(csv_path,'w')
        dataStr = "DEFECT_TYPE"+','+"DEFECT_SIDE"+','+"DISTANCE_IN_METER"+','+"DEFECT_LOCATION"+','+"CREATE_DATETIME"
        f.write(dataStr + '\n') 
        unique_image_type_dict = {}
        for row in range(len(data_set)):
            DEFECT_TYPE = str(data_set[row][0]).title()
            DEFECT_SIDE = str(data_set[row][1])
            DISTANCE_IN_METER = str(data_set[row][2])+" m"
            DEFECT_LOCATION = str(data_set[row][3])
            CREATE_DATETIME = str(data_set[row][4])
            dataStr = DEFECT_TYPE+','+DEFECT_SIDE+','+DISTANCE_IN_METER+','+DEFECT_LOCATION+','+CREATE_DATETIME
            f.write(dataStr + '\n')

            try:
                if DEFECT_TYPE not in unique_image_type_dict.keys():
                    IMAGE_PATH = str(data_set[row][5])
                    unique_image_type_dict[DEFECT_TYPE] = IMAGE_PATH
            except Exception as e:
                logger.critical(f"sendMails() : Exception is : {e}")
                logger.critical(f"sendMails() : Traceback Exception is : {traceback.format_exc()}")

        f.close()
        
        
        ''' Adding Attachment '''
        attachment = open(csv_path, "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(file_name))
        message.attach(part)
        
        for key, img_file_path in unique_image_type_dict.items():
            try:
                img_file_basename = os.path.basename(img_file_path)
                attachment = open(img_file_path, "rb")
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', "attachment; filename= %s" % img_file_basename)
                message.attach(part)
            except Exception as e:
                logger.critical(f"sendMails() Image File Attachment Loop : Exception is : {e}")
                logger.critical(f"sendMails() Image File Attachment Loop : Traceback Exception is : {traceback.format_exc()}")

        # Connect to Gmail's SMTP server
        smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_server.starttls()
        
        # Login to the sender's Gmail account
        smtp_server.login(sender_email, sender_password)
        
        # Send the email
        smtp_server.sendmail(sender_email, receiver_email, message.as_string())
        
        # Close the SMTP server connection
        smtp_server.quit()
        print(f"Mail Send To : {receiver_email}")
    except Exception as e:
        logger.error(f"mainFunction() Exception is : {e}")
        insertIntoLogDetailTable("NOT_OK_STATUS", f"Exception in sending email between date {startDate} To {endDate}", "sendMails", str(e))

'''
This function is used to disable the ONLY_FULL_GROUP_BY by functionality in Mysql engine.
'''
def disableGroupByFeatureInMysqlDB():
    try:
        db_object = pymysql.connect(host = db_host,user = db_user,password = db_pass,db = db_name)
        cur = db_object.cursor()
        query="SET GLOBAL sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));"
        cur.execute(query)
    except Exception as e:
        logger.critical(f"disableGroupByFeatureInMysqlDB() Exception is : {e}")
    finally:
        cur.close()
        db_object.close()
if __name__=="__main__":
    disableGroupByFeatureInMysqlDB()
    # sendMails("2023-06-28 00:00:10","2023-06-30 12:12:00")
    mainFunction()
    
    
    
    
