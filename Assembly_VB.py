import random
from click import DateTime

from tendo import singleton
me = singleton.SingleInstance()

from calendar import c
from itertools import count
import os
from shutil import ExecError
import sys
import cv2
from numpy import number
import datetime
#import date
from datetime import date
from datetime import timedelta
import time
import threading
import shutil
import subprocess
import subprocess, sys
# from pytz import HOUR
from tensorboard import summary
import ast
import xml.etree.ElementTree as ET
import pymysql
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui ,QtWidgets, uic
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
#from main import Ui_MainWindow
from login import Ui_Login
from ImageviewWindow import Ui_ImageviewWindow
#========import SOme Comman Library============#
import logging
import traceback
from matplotlib import axes
""" Canvas Library Imports """
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
""" Graph Library Import """
# from plotnine.data import economics
# from plotnine import ggplot, aes, geom_line, geom_bar
# from plotnine.data import mpg
import pandas as pd
import numpy as np
import math

from matplotlib.dates import date2num
from matplotlib import pyplot as plt, dates as mdates
from matplotlib import style
import matplotlib.dates as mdates

from add_customer_login import Ui_add_customer_login
from MAIL_SERVICE_V2 import GEmailClass
#import schedule
#import time
#import subprocess

config_path = "/home/pwil-pp/INSIGHTZZ/LIMESTONE/CODE/ULTRATECH_UI/config.xml"

config_parse = ET.parse(config_path)
config_root = config_parse.getroot()
UI_CODE_PATH = config_root[0].text
db_user = config_root[1].text
db_pass = config_root[2].text
db_host = config_root[3].text
db_name = config_root[4].text
DOWNLOAD_PATH = config_root[5].text
#Logging module
uilogger = None
# logging.basicConfig(filename=UI_CODE_PATH+"Ultatech_UI_RECORD_ACT_.log",filemode='a',format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# uilogger=logging.getLogger("Ultatech_UI_RECORD_ACT_")
# uilogger.setLevel(logging.CRITICAL) #CRITICAL #DEBUG

logging.basicConfig(filename=os.path.join(UI_CODE_PATH, "Ultatech_UI_RECORD.log"),filemode='a',format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
uilogger=logging.getLogger("Ultatech_UI_RECORD")
uilogger.setLevel(logging.CRITICAL) #CRITICAL #DEBUG

NO_IMAGE_PATH = UI_CODE_PATH+"no-image-found.png"
CAM1_IMAGE_LINK = "/home/pwil-pp/INSIGHTZZ/LIMESTONE/CODE/FRAME_CAPTURE/CameraData/SITE_1/TMP/TMP.jpg"
CAM2_IMAGE_LINK = "/home/pwil-pp/INSIGHTZZ/LIMESTONE/CODE/FRAME_CAPTURE/CameraData/SITE_2/INF/TMP.jpg"

start_frame_capture_both = "/home/pwil-pp/INSIGHTZZ/LIMESTONE/CODE/SHELL_SCRIPTS/start_all_cam.sh"
start_algo_capture_both = "/home/pwil-pp/INSIGHTZZ/LIMESTONE/CODE/SHELL_SCRIPTS/start_all_inf_algo.sh"



''' Currently disabled need to start after proper checking '''
start_plc_Helath = "/home/pwil-pp/INSIGHTZZ/LIMESTONE/CODE/ULTRATECH_UI/plcStatus.sh"
kill_PLC_STATUS_sh = "/home/pwil-pp/INSIGHTZZ/LIMESTONE/CODE/ULTRATECH_UI/kill_all.sh"
start_plc_service_sh = "/home/pwil-pp/INSIGHTZZ/LIMESTONE/CODE/ULTRATECH_UI/Service_Code/hirami_limestone.sh"
start_camAfter_reboot = "/home/pwil-pp/INSIGHTZZ/LIMESTONE/CODE/SHELL_SCRIPTS/start_camAfter_reboot.sh"
ScriptRun_Every10Min = "/home/pwil-pp/INSIGHTZZ/LIMESTONE/CODE/Algoritham/MemoryCheck/Every10_Min.sh"
MODBUS_READ_WRITE_TEST = "/home/pwil-pp/INSIGHTZZ/LIMESTONE/CODE/Algoritham/FOR_SHUT_DOWN/MODBUS_READ_WRITE_TEST.sh"
''' End Off - Currently disabled need to start after proper checking '''

DOWNLOAD_PATH_DUMPING = "/home/pwil-pp/Desktop/DOWNLOAD_DATA/DUMPING_CAMERA/"
DOWNLOAD_PATH_CONVEYOR = "/home/pwil-pp/Desktop/DOWNLOAD_DATA/CONVEYOR_CAMERA/"

processID = os.getpid()
print("This process has the PID", processID)

subprocess.Popen(["sh", start_frame_capture_both])
subprocess.Popen(["sh", start_algo_capture_both])


import psutil
disk_usage = psutil.disk_usage('/')
StorgeCheck = 900

def updateProcessId(processId):
    try:
        db_update = pymysql.connect(host=db_host,    # your host, usually localhost
                     user=db_user,                   # your username
                     passwd=db_pass,                 # your password
                     db=db_name)
        cur = db_update.cursor()
        query = f"UPDATE PROCESS_ID_TABLE set PROCESS_ID = {str(processId)} where PROCESS_NAME = 'ASSEMBLY'"
        cur.execute(query)
        db_update.commit()
        cur.close()
        db_update.close()
        print("updateProcessId in tabel")
    except Exception as e:
        print(f"Exception in update process id : {e}")
        
#=================================Start Mainwindow Funcation===========================#
class mainwindow(QtWidgets.QMainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(mainwindow, self).__init__(*args, **kwargs)      
        uic.loadUi(UI_CODE_PATH+"MainWindow.ui", self)  
        self.setWindowTitle("MainWindow")
        self.addConfig_Conveyor.clicked.connect(self.ConveyorConfigLogin)
        self.addConfig_Dumping.clicked.connect(self.Dumping_ConfigLogin)

        # report generate
        self.fetch_button_ReportCone.clicked.connect(self.fetchdata_ConveyorReport)
        self.from_timeEdit_ReportCone.hide()
        self.to_timeEdit_ReportCone.hide()
        self.defectSizeComboboxConve.hide()
        self.download_button_ReportCone.clicked.connect(self.downloadConvReport)
        self.from_timeEdit_analyticsConve.hide()
        self.to_timeEdit_analyticsConve.hide()
        self.from_timeEdit_reportDump.hide()
        self.to_timeEdit_reportDump.hide()
        # self.numberOfdefect_comboboxDum1.hide()
        self.defectSize_Dump1.hide()
        self.PercentageCombobox1.hide()
        self.defectSizeComboboxConve1.hide()
        self.from_timeEdit_analyticsDump.hide()
        self.to_timeEdit_analyticsDump.hide()

        self.fetch_button_report_Dump.clicked.connect(self.fetchdata_DumperReport)
        self.download_button_reportDump.clicked.connect(self.downloadButton)


        # set prev date in from date and today's date in to date field for report and analysis
        date1 = datetime.datetime.now()
        tday = QDate(date1.year, date1.month, date1.day)
        date2 = date1 - timedelta(days=1)
        prevDate = QDate(date2.year, date2.month, date2.day)
        self.from_dateEdit_ReportCone.setDate(prevDate)
        self.to_dateEdit_ReportCone.setDate(tday)

        self.from_dateEdit_analyticsConve.setDate(prevDate)
        self.to_dateEdit_analyticsConve.setDate(tday)
        self.from_dateEdit_reportDump.setDate(prevDate)
        self.to_dateEdit_reportDump.setDate(tday)
        self.from_dateEdit_analyticsDump.setDate(prevDate)
        self.to_dateEdit_analyticsDump.setDate(tday)


        #===================== Graph percentage conveyor ====================#
        self.figure = plt.figure()
        # self.canvas1 = FigureCanvas(self.figure)
        self.canvas1 = FigureCanvas(self.figure)
        layout1 = self.layout1
        layout1.addWidget(self.canvas1)
        self.setLayout(layout1)

        self.fetch_button_analyticsConve.clicked.connect(self.plotGraphPercentage)
        self.download_button_analyticsConve.clicked.connect(self.downloadConvGraph)

        self.defectSIze_reportCombo_ReportCone.hide()
        self.defecttype_label_ReportCone.hide()
        self.defectSIze_reportCombo_Dump.hide()
        self.defecttype_label_Dump.hide()
        self.from_timeEdit_reportDump.hide()
        self.to_timeEdit_reportDump.hide()
        self.numberOfdefect_comboboxDum1.hide()

        
        self.fetch_button_analyticsDump.clicked.connect(self.plotGraphDumperPercentage)
        self.download_button_analyticsDump.clicked.connect(self.dumperGraphDownload)

        #================update_cam_health with timer================#
        self.update_cam_health()
        self.timer_health=QTimer(self)
        self.timer_health.timeout.connect(self.update_cam_health)
        self.timer_health.start(20000)

        self.StorgeCheck=QTimer(self)
        self.StorgeCheck=QTimer(self)
        self.StorgeCheck.timeout.connect(self.StorgeCheck_fun)
        self.StorgeCheck.start(100000)


        
        self.show_processed_dataDumper()
        self.timer_processed_data=QTimer(self)
        self.timer_processed_data.timeout.connect(self.show_processed_dataDumper)
        self.timer_processed_data.start(1500)

        self.update_image()
        self.timer_img=QTimer(self)
        self.timer_img.timeout.connect(self.update_image)
        self.timer_img.start(1000) #200


        self.lastFiveConveyorDetect()
        self.timer_img=QTimer(self)
        self.timer_img.timeout.connect(self.lastFiveConveyorDetect)
        self.timer_img.start(300)


        self.lastConfigFromDB()
        #================Start some sh script================#
        self.StartAlgo.clicked.connect(self.start_process)
        self.StartAlgo_2.clicked.connect(self.startDumperCameraProcess)
        self.StartAlgo.hide()
        self.StartAlgo_2.hide()
        #================Calling pushButton funcation================#
        # self.imageView_button5.clicked.connect(self.post_button_5)
        self.pushButtonDumper1.clicked.connect(self.post_buttonDumper_1)
        self.pushButtonDumper2.clicked.connect(self.post_buttonDumper_2)
        self.pushButtonDumper3.clicked.connect(self.post_buttonDumper_3)
        self.pushButtonDumper4.clicked.connect(self.post_buttonDumper_4)
        self.pushButtonDumper5.clicked.connect(self.post_buttonDumper_5)
        #================Last5 Defct update tabel row size============#
        self.tableWidget.setColumnWidth(0, 170) #110
        self.tableWidget.setColumnWidth(1, 100) #200
        self.tableWidget.setColumnWidth(2, 150) #100
        
        self.tableWidget_3.setColumnWidth(0, 80)
        self.tableWidget_3.setColumnWidth(1, 150)
        self.tableWidget_3.setColumnWidth(2, 100)

        per = 150
        self.tableWidget_2.setColumnWidth(0, 200)
        self.tableWidget_2.setColumnWidth(1, 180)
        self.tableWidget_2.setColumnWidth(2, per)
        self.tableWidget_2.setColumnWidth(3, per)
        self.tableWidget_2.setColumnWidth(4, per)
        self.tableWidget_2.setColumnWidth(5, per)
        self.tableWidget_2.setColumnWidth(6, per)
        self.tableWidget_2.setColumnWidth(7, per)
        self.tableWidget_2.setColumnWidth(8, per)


        self.tableWidget_2_reportDump.setColumnWidth(0, 300)
        self.tableWidget_2_reportDump.setColumnWidth(1, 300)
        self.tableWidget_2_reportDump.setColumnWidth(2, 300)
        self.tableWidget_2_reportDump.setColumnWidth(3, 400)
        
        
        self.analyticsDataDumping()
        #self.analyticsDataConveyor()

    def Dumping_ConfigLogin(self):
        add_customer_login_object.show()    

    def ConveyorConfigLogin(self):
        add_customer_login_object.show() 


    def lastConfigFromDB(self):
        # #================== Populating Combobox =======================#
        try:
            db_fetch = pymysql.connect(host=db_host,    # your host, usually localhost
                            user=db_user,         # your username
                            passwd=db_pass,  # your password
                            db=db_name)
            cur = db_fetch.cursor()
            query = "select NO_OF_DEFECTS, DEFECT_SIZE from CONFIG_DUMPER_TABLE where IS_ACTIVE_CONFIG='1'"
            cur.execute(query)
            data_set = cur.fetchall()
            #print("data_set is vk :",data_set)
            cur.close()
            db_fetch.close()
            dumpingLast_list = []
            numberOfList = (data_set[0][0])
            sizeOfList = (data_set[0][1])
            # print("numberOfList is",numberOfList)
            # print("sizeOfList is",sizeOfList)
            self.numberOfdefect_comboboxDum.setText(str(numberOfList))#(prodn_list[i])
            self.defectSize_Dump.setText(str(sizeOfList))
        except Exception as e:
            print('last seen combo Exception : ',e)
            uilogger.critical("Error in login func-populating last seen combo:"+ str(e))
            uilogger.critical(str(traceback.print_exc()))                            
            
        # #================== populating last active configurations ===================#
        
        try:
            db_fetch = pymysql.connect(host=db_host,    # your host, usually localhost
                            user=db_user,         # your username
                            passwd=db_pass,  # your password
                            db=db_name)
            cur = db_fetch.cursor()
            query = "select PERCENTAGE, DEFECT_SIZE from CONFIG_TABLE where IS_ACTIVE_CONFIG='1'"
            cur.execute(query)
            data_set = cur.fetchall()
            cur.close()
            db_fetch.close()
            Percentage = (data_set[0][0])
            defectSizeConve = (data_set[0][1])
            # print("numberOfList is",Percentage)
            # print("sizeOfList is",defectSizeConve)

            self.PercentageCombobox.setText(str(Percentage))
            #main_object.defectSizeComboboxConve.setText(str(defectSizeConve))
        except Exception as e:
            print('prodn_list Exception : ',e)
            uilogger.critical("Error in login func-populating  configurations:"+ str(e))
            uilogger.critical(str(traceback.print_exc()))                            

    def dumperGraphDownload(self):
        from_date_temp = self.from_dateEdit_analyticsDump.date().toPyDate().strftime('%Y_%m_%d')
        from_time_temp = self.from_timeEdit_reportDump.time().toPyTime().strftime('%H:%M:%S') 
        
        to_date_temp = self.to_dateEdit_analyticsDump.date().toPyDate().strftime('%Y_%m_%d')
        to_time_temp = self.to_timeEdit_reportDump.time().toPyTime().strftime('%H:%M:%S')   
        startDate = from_date_temp 
        endDate = to_date_temp 
        #path1 = f'{DOWNLOAD_PATH}DumperGraph{from_date_temp}_{to_date_temp}.jpg'
        path1 = DOWNLOAD_PATH_DUMPING+datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        buttonReply = QMessageBox.question(self, 'Message', f"Are you sure you want to download graph? \n Download path: {path1}", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            # df.to_csv(f'/home/nikhil/Desktop/coding/ConvGraph{fromDate}_{toDate}.csv', sep=',', index=False,header=True)
            shutil.copy2("DUMPPING_GRAPH.jpg", path1)
            #print("+=========================================================== VK ==================================================================#")
            #shutil.copy2("/home/nikhil/Desktop/rAWAN bACKUP/newUI/ULTRATECH_UI/DUMPPING_GRAPH.jpg", path1)
            #print("donload data successfully.")
            self.show_message("DumperYard Graph Download successfully")    

        else:
            print("Not downloaded.")
            pass
        # shutil.copy2("output.jpg", "copy.jpg")
        print("file moved")

    def downloadConvGraph(self):
        from_date_temp = self.from_dateEdit_reportDump.date().toPyDate().strftime('%Y_%m_%d')
        from_time_temp = self.from_timeEdit_reportDump.time().toPyTime().strftime('%H:%M:%S') 
        
        to_date_temp = self.to_dateEdit_reportDump.date().toPyDate().strftime('%Y_%m_%d')
        to_time_temp = self.to_timeEdit_reportDump.time().toPyTime().strftime('%H:%M:%S')   
        startDate = from_date_temp 
        endDate = to_date_temp 
        #path1 = f'{DOWNLOAD_PATH_CONVEYOR}ConvGraph{from_date_temp}_{to_date_temp}.jpg'
        path1 = DOWNLOAD_PATH_CONVEYOR+datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        buttonReply = QMessageBox.question(self, 'Message', f"Are you sure you want to download graph? \n Download path: {path1}", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            # df.to_csv(f'/home/nikhil/Desktop/coding/ConvGraph{fromDate}_{toDate}.csv', sep=',', index=False,header=True)
            shutil.copy2("CONVEYOR_GRAPH.jpg", path1)
            #print("donload data successfully.")
            self.show_message("Conveyor Graph Download successfully")   
        else:
            print("Not downloaded.")
            pass
        # shutil.copy2("CONVEYOR_GRAPH.jpg", "copy.jpg")
        print("file moved")

    def lastFiveConveyorDetect(self):
        from_date_temp = str(self.from_dateEdit_reportDump.date().toPyDate())
        from_time_temp = self.from_timeEdit_reportDump.time().toPyTime().strftime('%H:%M:%S') 
        
        to_date_temp = str(self.to_dateEdit_reportDump.date().toPyDate())
        to_time_temp = self.to_timeEdit_reportDump.time().toPyTime().strftime('%H:%M:%S')   
        startDate = from_date_temp + " "+from_time_temp
        endDate = to_date_temp + " "+to_time_temp        
        Cameradefect = self.defectSIze_reportCombo_Dump.currentText() #defecttype_comboBox
        
        try:            
            db_fetch = pymysql.connect(host = db_host,
                                       user = db_user,
                                       passwd = db_pass,
                                       db = db_name)
            cur = db_fetch.cursor() 
           
            fromDate = self.from_dateEdit_ReportCone.date().toPyDate().strftime('%Y-%m-%d')
            toDate = (self.to_dateEdit_ReportCone.date().toPyDate()+timedelta(days=1) ).strftime('%Y-%m-%d') 

            query = f'''select substring(t1.shiftDaywise,1,10) as date1, substring(t1.shiftDaywise,11,1) as SHIFT, t1.pag80  from
                        (select concat(date_format(CURR_DATE,'%Y-%m-%d'),SHIFT) as shiftDaywise, sum(S0_25_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa0_25, sum(S26_40_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa26_40, sum(S41_50_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa41_50, sum(S51_75_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa51_75, sum(S76_80_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa76_80, sum(G80_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pag80 FROM LIMESTONE_DB.PERCENTAGE_ANALYSIS group by shiftDaywise order by shiftDaywise desc) as t1   limit 5 ;
                    '''
            cur.execute(query)
            data_set = cur.fetchall()
            #print("fetchdata Conveyor Prec  data_set is :",data_set)
            cur.close()
            db_fetch.close()
            #header = self.tableWidget_2.horizontalHeader()
            header = self.tableWidget.horizontalHeader()
                    
            # self.summary_data_lable.setText("Total Violation is :-"+str(len(data_set)))
            counter = 1
            #self.tableWidget_2.setRowCount(len(data_set))  
            self.tableWidget.setRowCount(len(data_set))  

            has_none = False
            newPre25mm_2 = False
            for data in data_set:
                if None in data:
                    has_none = True
                    break
                else:
                    newPre25mm_2 = True
            newPre25mm = False
            if has_none:
                #print("1")
                newPre25mm = True
                data_set = [[0 if x is None else x for x in tup] for tup in data_set] 

 
            for row in range(len(data_set)):
                    
                    self.tableWidget.setItem(row,0, QTableWidgetItem(f"{data_set[row][0].replace('_','-')}"))
                    self.tableWidget.setItem(row,1, QTableWidgetItem(f"{data_set[row][1]}"))
                    self.tableWidget.setItem(row,2, QTableWidgetItem("%.2f" % data_set[row][2]+"%"))
                         
        except Exception as e:
            uilogger.critical("Exception: lastFiveConveyorDefect()",e)
            print('fetch data Excption:', e)            

    def tab_7Fun(self):
        print("Clicked on tab_7")

    #  ========plotGraphPercentage =========
    def plotGraphPercentage(self):
        #print("you are in plotGraphPercentage function")
        plt.clf()
        ax = plt.subplot()
        ax.clear()
        x = [
            datetime.datetime(2023, 1, 4),
            datetime.datetime(2023, 1, 5),
            # datetime.datetime(2023, 1, 6)
        ]
        x = date2num(x)
        
        myFmt = mdates.DateFormatter('%d-%m-%Y')
        y = [4, 9, 2]
        z = [1, 2, 3]
        k = [11, 12, 13]
        p1 = [14,15,11]
        p2 = [14,15,11]
        p3 = [14,15,11]

        db_fetch = pymysql.connect(host = db_host,
                                       user = db_user,
                                       passwd = db_pass,
                                       db = db_name)
        cur = db_fetch.cursor() 
        if self.from_dateEdit_analyticsConve.date().toPyDate()  > self.to_dateEdit_analyticsConve.date().toPyDate():
            self.summary_data_analyticsConve.setText("Select Proper from date to Last date.")
        fromRowDate = self.from_dateEdit_analyticsConve.date().toPyDate()
        toRowDate = self.to_dateEdit_analyticsConve.date().toPyDate()+timedelta(days=1)
        # fromDate = self.from_dateEdit_analyticsConve.date().toPyDate().strftime('%Y-%m-%d')
        # toDate = (self.to_dateEdit_analyticsConve.date().toPyDate()+timedelta(days=1) ).strftime('%Y-%m-%d')     
        fromDate = str(fromRowDate.year)+"-"+str(fromRowDate.month)+"-"+str(fromRowDate.day) 
        toDate = str(toRowDate.year)+"-"+str(toRowDate.month)+"-"+str(toRowDate.day)
        #print("from date",fromDate,"Todate ",toDate,)
        
        fromDate = self.from_dateEdit_analyticsConve.date().toPyDate().strftime('%Y-%m-%d')
        toDate = (self.to_dateEdit_ReportCone.date().toPyDate()+timedelta(days=1) ).strftime('%Y-%m-%d') 
        
        query = f'''select date_format(CURR_DATE,'%Y-%m-%d') as shiftDaywise, sum(S0_25_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa0_25, sum(S26_40_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa26_40, sum(S41_50_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa41_50, sum(S51_75_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa51_75, sum(S76_80_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa76_80, sum(G80_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pag80 FROM LIMESTONE_DB.PERCENTAGE_ANALYSIS 
                    where CURR_DATE between "{fromDate}" and "{toDate}" 
                    group by shiftDaywise;'''
                
        cur.execute(query)
        
        data_set = cur.fetchall()
        #print("plotGraphPercentage Conveyor data_set is :",data_set)
        cur.close()
        db_fetch.close()
        header = self.tableWidget_2.horizontalHeader()
          
        self.summary_data_lable.setText("Total Violation is :-"+str(len(data_set)))
        counter = 1       
        self.tableWidget_2.setRowCount(len(data_set))  
        # if len(data_set) == 0:
        #     self.show_message("No Data Found" )
        #     return   
        # print(len(data_set),data_set)  
        # print('dataset printed......')
        date1 = []
        shift = []
        s0_25 = []
        s26_40 = []
        s41_50 = []
        s51_75 = []
        s76_80 = []
        g80 = []

        for row in range(len(data_set)):
            #print(row)
            date1.append(data_set[row][0])
            # shift.append(data_set[row][1])
            newPer = float(100-(data_set[row][2]+data_set[row][3]+data_set[row][4]+data_set[row][5]+data_set[row][6]))
            # s0_25.append(data_set[row][1])
            s0_25.append(newPer)
            s26_40.append(data_set[row][2])
            s41_50.append(data_set[row][3])
            s51_75.append(data_set[row][4]) 
            s76_80.append(data_set[row][5]) 
            g80.append(data_set[row][6]) 

        if len(s0_25) == 0:
            self.summary_data_analyticsConve.setText("Data is not available for this timeframe ")
            # return 0
        else:
            self.summary_data_analyticsConve.setText("Graph is ploted.")

        ndate = []
        for i in date1:
            #print(i)
            ndate.append(datetime.datetime.strptime(i, '%Y-%m-%d'))
            #print(i,datetime.datetime.strptime(i, '%Y-%m-%d'), type(datetime.datetime.strptime(i, '%Y-%m-%d')))    
        x = ndate
        x = date2num(x)
        
        myFmt = mdates.DateFormatter('%d-%m-%Y')

        ax = plt.subplot(111)
        ax.bar(x-0.2, s0_25, width=0.1, color='c', align='center', label="0-25")
        ax.bar(x-0.1, s26_40, width=0.1, color='b', align='center',label="26-40")
        ax.bar(x, s41_50, width=0.1, color='g', align='center',label="41-50")
        ax.bar(x+0.1, s51_75, width=0.1, color='r', align='center',label="51-75")
        ax.bar(x+0.2, s76_80, width=0.1, color='m', align='center',label="76-80")
        ax.bar(x+0.3, g80, width=0.1, color='y', align='center',label=">80")
        # plt.addlabels(x, s0_25)
        for i in range(len(x)):
            plt.text(i,s0_25[i],s0_25[i])
        
        ax.xaxis.set_major_formatter(myFmt)
        ax.legend()
        plt.xticks(rotation=20)

        ax.set(ylabel='Percentage', xlabel='Date')
        colors = {'G60':'red', '>80':'red', '60_80':'green'}
        ax.plot(kind='barh', stacked=True, alpha=0.7, ax=ax, color=colors)

        ax.xaxis_date()
        	# refresh canvas
        # plt.savefig(f'{DOWNLOAD_PATH}/graph{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")}.png')
        plt.savefig("CONVEYOR_GRAPH.jpg")

        self.canvas1.draw()

        print("you are in plotGraphPercentage function")
        uilogger.critical("you are in plotGraphPercentage function")


    def plotGraphDumperPercentage(self):
        db_fetch = pymysql.connect(host = db_host,
                                       user = db_user,
                                       passwd = db_pass,
                                       db = db_name)
        cur = db_fetch.cursor() 
        #print("You are in SOFTWARE()")
        if self.from_dateEdit_analyticsDump.date().toPyDate()  > self.to_dateEdit_analyticsDump.date().toPyDate():
            self.summary_data_lable_analyticsDump.setText("Select Proper from date to Last date.")

        fromDate = self.from_dateEdit_analyticsDump.date().toPyDate().strftime('%Y-%m-%d')
        toDate = (self.to_dateEdit_analyticsDump.date().toPyDate()+timedelta(days=1) ).strftime('%Y-%m-%d') 
        fromRowDate = self.from_dateEdit_analyticsDump.date().toPyDate()  
        toRowDate = self.to_dateEdit_analyticsDump.date().toPyDate()+timedelta(days=1)
        startDate = str(fromRowDate.year)+"-"+str(fromRowDate.month)+"-"+str(fromRowDate.day) 
        endDate = str(toRowDate.year)+"-"+str(toRowDate.month)+"-"+str(toRowDate.day)  

        query = f'''SELECT sum(NO_OF_DEFECT_COUNT), date_format(CREATE_DATETIME,'%d_%m_%Y') as fdate FROM LIMESTONE_DB.PROCESSING_DUMPER_TABLE 
                    where defect_size >= 1000 and CREATE_DATETIME between "{fromDate}" and "{toDate}" 
                    group by fdate;'''  
        #print("Query : ",query)        
        cur.execute(query)
        data_set = cur.fetchall()
        #print("plotGraphDumperPercentage Conveyor data_set is :",data_set)
        cur.close()
        db_fetch.close()
        header = self.tableWidget_2.horizontalHeader()
       
        self.summary_data_lable.setText("Total Violation is :-"+str(len(data_set)))
        counter = 1
        self.tableWidget_2.setRowCount(len(data_set))  
        date1 = []
        # shift = []
        sumOfStones = []
   

        for row in range(len(data_set)):
            #print(row)
            date1.append(data_set[row][1])
            sumOfStones.append(data_set[row][0])

        if len(sumOfStones) == 0:
            self.summary_data_analyticsConve.setText("Data is not available for this timeframe ")
            # return 0
        else:
            self.summary_data_analyticsConve.setText("Graph is ploted.")

        ndate = []
        for i in date1:
            # print(i)
            # print(i,type(i))
            ndate.append(datetime.datetime.strptime(i, '%d_%m_%Y'))
            #print(i,datetime.datetime.strptime(i, '%d_%m_%Y'), type(datetime.datetime.strptime(i, '%d_%m_%Y')))    

        x = ndate
        x1 = date2num(x)        
        myFmt = mdates.DateFormatter('%d-%m-%Y')

            # fetch_button_analyticsDump
        if self.from_dateEdit_analyticsDump.date().toPyDate()  > self.to_dateEdit_analyticsDump.date().toPyDate():
            self.summary_data_analyticsConve.setText("Select Proper from date to Last date.")
            return 0


        #print("you are in plotGraphDumperPercentage function")
        # plt.clf()
        data = [random.random() for i in range(10)]
        # clearing old figure
        self.figure.clear()
        plt.clf()
        ax = plt.subplot(111)
        # ax.bar(x-0.2, y, width=0.2, color='b', align='center')
        #print(x1)
        ax.bar(x1, sumOfStones, width=0.2, color='g', align='center',label="No. of Stones")
        # ax.bar(x+0.2, k, width=0.2, color='r', align='center')
        ax.xaxis_date()
        plt.xticks(rotation=15)
        ax.xaxis.set_major_formatter(myFmt)
        ax.set(ylabel='No. of Stones', xlabel='Date')
        # from matplotlib.pyplot import figure
        # figure(figsize=(4, 2), dpi=80)
        # ax.xlabel("Date")
        # plt.ylabel("No. of Stones.")
        # plt.figure().set_figheight(2)
        # self.dumperGraphImg.set
        ax.legend()
        plt.gcf().set_size_inches(10, 4)
        self.summary_data_lable_analyticsDump.setText(f"We found {len(data_set)} days of record.")
        plt.savefig("DUMPPING_GRAPH.jpg")
        self.dumperGraphImg.setPixmap(QtGui.QPixmap("DUMPPING_GRAPH.jpg"))
        self.plotGraphPercentage()
        # plt.savefig("outpu3.jpg")
        uilogger.critical("you are in plotGraphDumperPercentage function")


    def downloadConvReport(self):
        db_fetch = pymysql.connect(host = db_host,
                                       user = db_user,
                                       passwd = db_pass,
                                       db = db_name)
        cur = db_fetch.cursor() 
        #print("You are in downloadConvReport()")
        if self.from_dateEdit_ReportCone.date().toPyDate() > self.to_dateEdit_ReportCone.date().toPyDate():
                print("right")
                self.summary_data_ReportCone.setText("Select Proper from date to Last date.")
                return 0
        # fromDate = self.from_dateEdit_ReportCone.date().toPyDate().strftime('%d-%m-%Y')
        # toDate = (self.to_dateEdit_ReportCone.date().toPyDate()+timedelta(days=1) ).strftime('%d-%m-%Y') 
        fromDate = self.from_dateEdit_ReportCone.date().toPyDate().strftime('%Y-%m-%d')
        toDate = (self.to_dateEdit_ReportCone.date().toPyDate()+timedelta(days=1) ).strftime('%Y-%m-%d')

        ##print("from date",fromDate,"Todate ",toDate,)
        query = f'''select substring(t1.shiftDaywise,1,10) as date1, substring(t1.shiftDaywise,11,1) as SHIFT, t1.pa0_25, t1.pa26_40, t1.pa41_50, t1.pa51_75, t1.pa76_80, t1.pag80  from
                        (select concat(date_format(CURR_DATE,'%Y-%m-%d'),SHIFT) as shiftDaywise, sum(S0_25_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa0_25, sum(S26_40_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa26_40, sum(S41_50_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa41_50, sum(S51_75_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa51_75, sum(S76_80_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa76_80, sum(G80_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pag80 FROM LIMESTONE_DB.PERCENTAGE_ANALYSIS where CURR_DATE between "{fromDate}" and "{toDate}" group by shiftDaywise) as t1;'''
                     
        cur.execute(query)
        data_set = cur.fetchall()
        #print("fetchdata Conveyor data_set is :",data_set)
        cur.close()
        db_fetch.close()
        header = self.tableWidget_2.horizontalHeader()
                
        self.summary_data_lable.setText("Total Violation is :-"+str(len(data_set)))
        counter = 1
        self.tableWidget_2.setRowCount(len(data_set))  
        # if len(data_set) == 0:
        #     self.show_message("No Data Found" )
        #     return   
        # print(len(data_set),data_set)  
        # print('dataset printed......')
        path1 = DOWNLOAD_PATH_CONVEYOR+datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        dataStr = " DATE "+','+" SHIFT "+','+" 0-25 "+','+" 26-40 "+','+" 41-50 "+','+" 51-75 "+','+" 76-80 "+','+" >80 "
        f = open(path1+'.csv','w')
        f .write(dataStr+'\n')  
        date1 = []
        shift = []
        s0_25 = []
        s26_40 = []
        s41_50 = []
        s51_75 = []
        s76_80 = []
        g80 = []
        for row in range(len(data_set)):
            date1 = str(data_set[row][0])
            shift = str(data_set[row][1])
            newPer = float(100 - (data_set[row][3]+data_set[row][4]+data_set[row][5]+data_set[row][6]+data_set[row][7]))
            s0_25 = str(newPer)+"%"
            #s0_25 = str(data_set[row][2])+"%" 
            s26_40 = str("%.2f"%data_set[row][3])+"%"
            s41_50 = str("%.2f"%data_set[row][4])+"%"
            s51_75 = str("%.2f"%data_set[row][5])+"%"
            s76_80 = str("%.2f"%data_set[row][6])+"%"
            g80 = str("%.2f"%data_set[row][7])+"%"
            #print(f"=01=================date1 : {date1}, shift : {shift}, s0_25 : {s0_25}, s26_40 : {s26_40}, s41_50 : {s41_50}=================")

            dataStr =  date1+','+shift+','+s0_25+','+s26_40+','+s41_50+', '+s51_75+','+s76_80+','+g80 
         
            f.write(dataStr + '\n')

        path1 = DOWNLOAD_PATH_CONVEYOR+datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        buttonReply = QMessageBox.question(self, 'Message', f"Are you sure you want to download? \n Download path: {path1}", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            #df.to_csv(path1, sep=',', index=False,header=True)
            print("download data successfully.")
            self.show_message("Conveyor Report Download successfully")  
        else:
            uilogger.critical("Data now downloaded Successfully.")
        f.close()    
       
    def cameraWiseCorrelationDataDayWise1(self, startDate, endDate):
        #print("Your in cameraWiseCorrelationDataDayWise1 fun sdate and edate are:",startDate,endDate)
        iba_count_list = []
        cam_count_listConvyer = []
        cam_count_listDumper = []
        pd_date_list = pd.date_range(startDate.split(" ")[0], endDate.split(" ")[0], freq='D')
        date_list = []
        for i in pd_date_list:
            date_list.append(i.strftime('%Y-%m-%d'))
            iba_count_list.append(0)
            cam_count_listConvyer.append(0)
            cam_count_listDumper.append(0)
            
        try:
            db_conn = pymysql.connect(host=db_host,user=db_user, passwd=db_pass,db= db_name)
            cur = db_conn.cursor()
            ''' Query From VISION-Processing Table '''
            query=f"SELECT sum(30_60MM) AS S30, sum(60_80MM) AS S60_80, sum(G80MM) AS SG80, CAST(DATE_TIME AS DATE) from CONVEYOR_BELT.PERCENTAGE_ANALYSIS  WHERE DATE_TIME BETWEEN  '{startDate}'AND '{endDate}' group by CAST(DATE_TIME AS DATE);"
            #print(query)
            cur.execute(query)
            data_set = cur.fetchall()
            #print("cameraWiseCorrelationDataDayWise data_set", data_set)
            S30_60 = []
            S60_80 = []
            SG80 = []
            SDateTime = []
            for row_number, row_data in enumerate(data_set):
               # print(row_number,row_data)
                S30_60.append(row_data[0])
                S60_80.append(row_data[1])
                SG80.append(row_data[2])
                SDateTime.append(row_data[3])
                # index = date_list.index(str(date))
                # cam_count = row_data[1]
                # print("Convyer cam_count",cam_count)
                # cam_count_listConvyer = cam_count
                # print("Convyer cam_count_listConvyer[index]",cam_count_listConvyer)
                    
            cur.close()
            db_conn.close()
        except Exception as e:
            uilogger.critical("Exception: cameraWiseCorrelationDataDayWise1()",e)
            print(f"camerWiseData convyer() Exception is : {e}")
 
        cam_count_list = cam_count_listConvyer + cam_count_listDumper
       # print("cam_count_list both",cam_count_list)
       # print(S30_60,S60_80,SG80,SDateTime)
        return S30_60,S60_80,SG80,SDateTime
    

    
    #====================LogOut Funcation Start==================#   
    def logout(self):
            uilogger.critical("LOGOUT - FUNCTION STARTS")
            buttonReply = QMessageBox.question(self, 'Message', "Are you sure you want to logout?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if buttonReply == QMessageBox.Yes:
                main_object.hide()
                login_object.show()
            # else:
            #     pass
            uilogger.critical("LOGOUT - FUNCTION ENDS")
    #====================LogOut Funcation End==================#  

    #========Save ConvyerUserData Funcation Start===============#
    def save_post_data(self):

        uilogger.critical("SAVE POST DATA - FUNCTION STARTS")   

        percentage = self.PercentageCombobox.text()
        #defectSize = self.defectSizeComboboxConve.text()
        try:
            number = int(percentage)
        except:
            data_type_check = 1
            # self.show_message("defectSizeDumping must be int") 
            print("Enter Valid Number")  
            self.ConveyorLaberConfig.setText("Enter Valid Number") 
            self.ConveyorLaberConfig.setStyleSheet("color: red;")
            #setStyleSheet("background-color: rgb(255, 1, 1);")
            #self.conveyorLabelConfig.setText("Enter Valid Number") 
            return 0     
        
        self.conveyorLabelConfig.setText("")      
        if  int(self.PercentageCombobox.text())!="":
            self.ConveyorLaberConfig.clear()   
            precenLabelConve = int(self.PercentageCombobox.text())
            timeVar = datetime.datetime.now()
            datetimevar = str(timeVar.strftime("%Y-%m-%d %H:%M:%S"))
         
            #======================= checking data type ======================#
            data_type_check = 0  #data_type_check should be 0. if 1 the saving should not happen   
            # try:
            #     number = int(defectSizeComboboxConve)
            # except:
            #     data_type_check = 1
            #     self.show_message("defectSizeComboboxConve must be int")         
            try:
                number = int(precenLabelConve)
            except:
                data_type_check = 1
                self.show_message("precenLabelConve must be int")    

            if data_type_check == 0:
                buttonReply = QMessageBox.question(self, 'Message', "Are you sure you want to save?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if buttonReply == QMessageBox.Yes:
                    # try:
                    #     db_update = pymysql.connect(host=db_host,    # your host, usually localhost
                    #                  user=db_user,         # your username
                    #                  passwd=db_pass,  # your password
                    #                  db=db_name)
                    #     cur = db_update.cursor()
                    #     query = "update CONFIG_TABLE set IS_ACTIVE_CONFIG = 0 "
                    #     cur.execute(query)
                    #     db_update.commit()
                    #     cur.close()
                    # except Exception as e:
                    #     print('Exception : ',e)
                    #     uilogger.critical("Error in save post data func:"+ str(e))
                    #     uilogger.critical(str(traceback.print_exc()))                    
                    #     cur.close()                
                    try:
                        db_update = pymysql.connect(host=db_host,    # your host, usually localhost
                                     user=db_user,         # your username
                                     passwd=db_pass,  # your password
                                     db=db_name)
                        cur = db_update.cursor()
                        print("vk")
                        #query = f"insert into CONFIG_TABLE (PERCENTAGE , IS_ACTIVE_CONFIG) values ('{precenLabelConve}',1)"
                        query = f"UPDATE CONFIG_TABLE set PERCENTAGE = {str(precenLabelConve)}, IS_ACTIVE_CONFIG = {str(1)} where (`ID` = '1')"
                        cur.execute(query)
                        db_update.commit()
                        #,'"+self.prod_no_lineEdit+"', timestamp('"+datetimevar+"'), 1)" 
                        cur.close()
                        db_update.close()
                        self.show_message("Details saved successfully!")                        
                    except Exception as e:
                        print('Exception : ',e)
                        uilogger.critical("Error in save post data func:"+ str(e))
                        uilogger.critical(str(traceback.print_exc()))                    
                else:
                    pass
            else:
                pass
        else:
            self.show_message("Please fill all the configurations before saving")
        uilogger.critical("SAVE CONVEYOR - FUNCTION ENDS")  
    #===============Save ConvyerUserData Funcation End===============#

    #===============Save addConfigDumper Funcation Start===============#
    def addConfigDumper(self):
       #print("addConfigDumper")
        uilogger.critical("SAVE DATA DUMPER - FUNCTION STARTS")

        #def Dumping_ConfigLogin(self):
        #add_customer_login_object.show()

        defectSizeDumping = self.defectSize_Dump.text()
        noOfDefectDumping = self.numberOfdefect_comboboxDum.text()
        try:
            number = int(defectSizeDumping)
        except:
            data_type_check = 1
            # self.show_message("defectSizeDumping must be int") 
            uilogger.critical("Enter Valid Number addConfigDumper()")
            print("Enter Valid Number")  
            self.dumperLaberConfig.setText("Enter Valid Number") 
            self.dumperLaberConfig.setStyleSheet("color: red;")
            return 0     
        try:
            number = int(noOfDefectDumping)
        except:
            data_type_check = 1
            # self.show_message("noOfDefectDumping must be int") 
            # print("Enter Valid Number") 
            self.dumperLaberConfig.setText("Enter Valid Number") 
            self.dumperLaberConfig.setStyleSheet("color: red;")
            
            return 0  
        self.dumperLaberConfig.setText("")
        if int(self.numberOfdefect_comboboxDum.text())!="" and int(self.defectSize_Dump.text())!="":
            self.dumperLaberConfig.clear()
            defectSizeDumping = int(self.defectSize_Dump.text())
            noOfDefectDumping = int(self.numberOfdefect_comboboxDum.text())
            timeVar_2 = datetime.datetime.now()
            datetimevar_2 = str(timeVar_2.strftime("%Y-%m-%d %H:%M:%S"))

            #======================= checking data type ======================#
            data_type_check = 0  #data_type_check should be 0. if 1 the saving should not happen  
            try:
                number = int(defectSizeDumping)
            except:
                data_type_check = 1
                # self.show_message("defectSizeDumping must be int") 
                print("Enter Valid Number")  
                self.dumperLaberConfig.setText("Enter Valid Number") 
                return 0     
            try:
                number = int(noOfDefectDumping)
            except:
                data_type_check = 1
                # self.show_message("noOfDefectDumping must be int") 
                # print("Enter Valid Number") 
                self.dumperLaberConfig.setText("Enter Valid Number") 
                return 0  
            self.dumperLaberConfig.setText("")
            if data_type_check == 0:
                buttonReply = QMessageBox.question(self, 'Message', "Are you sure you want to save?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if buttonReply == QMessageBox.Yes:
                                  
                    try:
                        db_update = pymysql.connect(host=db_host,    # your host, usually localhost
                                    user=db_user,         # your username
                                    passwd=db_pass,  # your password
                                    db=db_name)
                        cur = db_update.cursor()
                        print("vk")   
                        query = f"UPDATE CONFIG_DUMPER_TABLE set DEFECT_SIZE = {str(defectSizeDumping)}, NO_OF_DEFECTS = {str(noOfDefectDumping)},IS_ACTIVE_CONFIG = {str(1)} where (`ID` = '1')"   
                       # query = "update LIMESTONE_DB.CONFIG_DUMPER_TABLE set IS_ACTIVE_CONFIG = 0"
                        #query = f"update into CONFIG_DUMPER_TABLE (DEFECT_SIZE, NO_OF_DEFECTS, IS_ACTIVE_CONFIG) values ('{defectSizeDumping}','{noOfDefectDumping}',1) where IS_ACTIVE_CONFIG = 1"                   
                        #print("query is===== :",query)    
                        cur.execute(query)
                        db_update.commit()
                        cur.close()
                        db_update.close()
                        self.show_message("Details saved successfully!")                        
                    except Exception as e:
                        print('Exception : ',e)
                        uilogger.critical("Error in save post data func:"+ str(e))
                        uilogger.critical(str(traceback.print_exc()))                    
                else:
                    pass
            else:
                self.show_message("Please fill all the configurations before saving")
                pass
        else:
            pass
            #self.show_message("Please fill all the configurations before saving")
        uilogger.critical("SAVE DATA DUMPER - FUNCTION ENDS")
    # #===============Save addConfigDumper Funcation Start===============#

    def closeEvent(self, event):
        quit_msg = "Are you sure you want to close the program?"
        reply = QtWidgets.QMessageBox.question(self, 'Message', 
                         quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            subprocess.Popen(["sh", kill_PLC_STATUS_sh])
            event.accept()
            #subprocess.Popen(["sh", kill_health_sh])
            #subprocess.Popen(["sh", kill_algo_sh])

            
        else:
            event.ignore()

    def show_message(self, message):
        choice = QMessageBox.information(self, 'Message!',message)

    #=================================== start Algo_process ===============================================#
    def start_process(self):
        if self.StartAlgo.isChecked():
            buttonReply = QMessageBox.question(self, 'Message', "Do you want to start Convyer Camera processing?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if buttonReply == QMessageBox.Yes:
                print("Convyer Camera algorithm started")
                self.show_message("It will take around 10-15 seconds to start")
                self.StartAlgo.setStyleSheet("background-color: rgb(255, 0, 0);")
                self.StartAlgo.setText(QtCore.QCoreApplication.translate("MainWindow", "Stop")) 
                #subprocess.Popen(["sh", start_algo_sh])
        else:
            buttonReply = QMessageBox.question(self, 'Message', "Do you want to stop Convyer Camera processing?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if buttonReply == QMessageBox.Yes:
                self.StartAlgo.setStyleSheet("background-color: rgb(0, 170, 255)")
                self.StartAlgo.setText(QtCore.QCoreApplication.translate("MainWindow", "Start")) 
                #subprocess.Popen(["sh", kill_algo_sh])
                print("Convyer Camera algorithm stop")

    #================================ start_process DumpingCamera==========================================#
    def startDumperCameraProcess(self):
        if self.StartAlgo_2.isChecked():
            buttonReply = QMessageBox.question(self, 'Message', "Do you want to start Dumping Camera processing?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if buttonReply == QMessageBox.Yes:
                print("Dumping Camera algorithm started")
                self.show_message("It will take around 10-15 seconds to start")
                self.StartAlgo_2.setStyleSheet("background-color: rgb(255, 0, 0);")
                self.StartAlgo_2.setText(QtCore.QCoreApplication.translate("MainWindow", "Stop")) 
                #subprocess.Popen(["sh", start_algo_sh])
        else:
            buttonReply = QMessageBox.question(self, 'Message', "Do you want to stop Dumping Camera processing?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if buttonReply == QMessageBox.Yes:
                self.StartAlgo_2.setStyleSheet("background-color: rgb(0, 170, 255)")
                self.StartAlgo_2.setText(QtCore.QCoreApplication.translate("MainWindow", "Start")) 
                #subprocess.Popen(["sh", kill_algo_sh])
                print("Dumping Camera StartAlgo_2algorithm stop")  
                
    #================================ start_process DumpingCamera==========================================#
    def dataSync(self):
        ##########try:
        subprocess.call(['python3', '/home/dhar-limestone/INSIGHTZZ/code/Algoritham/ALGORITHAM_CODE/CodeFor_DataSync/DataSyncServiceV3.py'])
        #except Exception as e:
            #print('Exception : ',e) 
    
    def sendEmailToUser(self):
        EMAIL_HOURS = ["05","13","21"]
        project_name= "Ultratech - Hirmai Limestone Plant " 
        # receiver_email_list = ["vikram.jethmal@insightzz.com"] 
        receiver_email_list = ["vikram.jethmal@insightzz.com","sgn@insightzz.com","vikas.jadhav@insightzz.com","dipali.mandlik@insightzz.com","pratiksha.chavan@insightzz.com","knv.murthy@adityabirla.com", "m.senthil@adityabirla.com", "madala.srinivas@adityabirla.com", "devendra.indora@adityabirla.com", "bhaktilaxmi.sahoo@adityabirla.com", "pinaki.dutta@adityabirla.com", "ravindra.mane@adityabirla.com","santoshkumar.sharma@adityabirla.com", "Balu.Jat@adityabirla.com" ,"satya.rathore@adityabirla.com", "sandeep.patrange@adityabirla.com","bholanath.pandey@adityabirla.com", "amjhad.ali@adityabirla.com", "surendra.namdeo@adityabirla.com","prahlad.joshi@adityabirla.com","akshat.agrawal@adityabirla.com", "ekansh.pathak@adityabirla.com","awadh.yadav@adityabirla.com","Daya.tiwari@adityabirla.com","Abhishek.rajpurohit@adityabirla.comAbhishek.rajpurohit@adityabirla.comAbhishek.rajpurohit@adityabirla.com","Awinash.barange@aditybirla.com"]
        gMailObj = GEmailClass(project_name, receiver_email_list)
        # enableFullGroupBy()
        print("Sending Email")

        try:            
            ''' Mail Sending Code At every Hour '''
            todaysDate = datetime.datetime.now().strftime("%Y-%m-%d %H")  
            start_time_str = f"{todaysDate}:55:00"
            end_time_str = f"{todaysDate}:59:00"
            start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
            end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
            if datetime.datetime.now() < end_time and datetime.datetime.now() > start_time:
                print(f"sending Mail {datetime.datetime.now()}")
                ''' Send Email to users '''
                date, timeStr = start_time_str.split(" ")
                # Split the time component to extract the hour
                hour = timeStr.split(":")[0]
              #  hour = "21"
                if hour in EMAIL_HOURS:
                    if hour == "05":
                        gMailObj.sendReportMails("C")
                    elif hour == "13":
                        gMailObj.sendReportMails("A")
                    elif hour == "21":
                        gMailObj.sendReportMails("B")
                    time.sleep(600)
                    #time.sleep(10)
                else:
                    print(f"mainFunction() While loop break, For starting code again.")
                time.sleep(10)
                
            #time.sleep(10)
            del(gMailObj)
        except Exception as e:
            print(f"mainFunction() While loop break, Exception is : {e}.")  
        	
    #=================================== updating health =============================================#
    def update_cam_health(self):
        self.sendEmailToUser()
        try:
            db_select = pymysql.connect(host=db_host,    # your host, usually localhost
                         user=db_user,                   # your username
                         passwd=db_pass,                 # your password
                         db=db_name)
            cur = db_select.cursor()
            query = "SELECT ITEM, HEALTH FROM HEALTH_STATUS_TABLE"
            cur.execute(query)
            data_set = cur.fetchall()
            print("HEALTH_STATUS_TABLE is :",data_set)
            cur.close()
            db_select.close()
            for cam_pos in data_set:
                #print(cam_pos[0])
                try:
                    #subprocess.Popen(["sh", MODBUS_READ_WRITE_TEST])
                    #subprocess.Popen(["sh", start_plc_service_sh])
                    if cam_pos[0] == "HIKVISION_CAMERA" and cam_pos[1] == "OK":
                        self.BottomCam_HealthLabel.setText("DumpingCamera : ACTIVE")
                        self.BottomCam_HealthLabel.setStyleSheet("background-color: rgb(0, 170, 0);")                
                    elif cam_pos[0] == "HIKVISION_CAMERA" and cam_pos[1] == "NOTOK":
                        #print("CAM2 is not connnected")
                        uilogger.critical("CAM2 is not connnected")
                        self.BottomCam_HealthLabel.setText("DumpingCamera : INACTIVE")
                        self.BottomCam_HealthLabel.setStyleSheet("background-color: rgb(255, 1, 1);")
                        subprocess.Popen(["sh", kill_PLC_STATUS_sh])
                        time.sleep(3)

                        subprocess.Popen(["sh", start_frame_capture_both])
                        time.sleep(2)
                        subprocess.Popen(["sh", start_algo_capture_both])

                        



                    if cam_pos[0] == "CONVEYOR_CAMERA" and cam_pos[1] == "OK":
                        self.TopCam_HealthLabel.setText("ConveyorCamera : ACTIVE")
                        self.TopCam_HealthLabel.setStyleSheet("background-color: rgb(0, 170, 0);")                
                    elif cam_pos[0] == "CONVEYOR_CAMERA" and cam_pos[1] == "NOTOK":
                        #print("CAM1 is not connnected")
                        uilogger.critical("CAM1 is not connnected")
                        self.TopCam_HealthLabel.setText("ConveyorCamera : INACTIVE")
                        self.TopCam_HealthLabel.setStyleSheet("background-color: rgb(255, 1, 1);")

                        subprocess.Popen(["sh", kill_PLC_STATUS_sh])
                        time.sleep(3)

                        subprocess.Popen(["sh", start_frame_capture_both])
                        time.sleep(2)
                        subprocess.Popen(["sh", start_algo_capture_both])


                    if cam_pos[0] == "PLC_CONNECTIVITY" and cam_pos[1] == "OK":
                        self.plcConnectBoth.setText("PLC_Connectivity :ACTIVE")
                        self.plcConnectBoth.setStyleSheet("background-color: rgb(0, 170, 0);")  
                        self.plcConnectBoth_2.setText("PLC_Connectivity :ACTIVE")
                        self.plcConnectBoth_2.setStyleSheet("background-color: rgb(0, 170, 0);")               
                    elif cam_pos[0] == "PLC_CONNECTIVITY" and cam_pos[1] == "NOTOK":
                        #print("CAM1 is not connnected")
                        uilogger.critical("plc is not connnected")
                        self.plcConnectBoth.setText("PLC_Connectivity :INACTIVE")
                        self.plcConnectBoth.setStyleSheet("background-color: rgb(255, 1, 1);")
                        self.plcConnectBoth_2.setText("PLC_Connectivity :INACTIVE")
                        self.plcConnectBoth_2.setStyleSheet("background-color: rgb(255, 1, 1);")

                        subprocess.Popen(["sh", kill_PLC_STATUS_sh])
                        time.sleep(3)

                        subprocess.Popen(["sh", start_frame_capture_both])
                        time.sleep(2)
                        subprocess.Popen(["sh", start_algo_capture_both])
                except Exception as e:
                    print('Exception : ',e)
                    uilogger.critical("Error in update_cam_health:"+ str(e))

                
        except Exception as e:
            print('Exception : ',e)
            uilogger.critical(f"update cam health : "+ str(e))
    
    #============== updating defect data for Convyer Camera =============================#
    def show_image(self,image_link):
        print(image_link)
        #os.system(f"scp ccr3server@18.78.0.206:{image_link} /home/ccr03/insightzz/code/UI/TEMP_IMG/TMP.jpg")
        #image_link = "/home/ccr03/insightzz/code/UI/TEMP_IMG/TMP.jpg"
        if os.path.exists(image_link):
            imagewindow_object.setWindowTitle(image_link.split("/")[-1])
            imagewindow_object.loadImage(image_link)
        else:
            image_link = NO_IMAGE_PATH
            imagewindow_object.setWindowTitle(image_link.split("/")[-1])
            imagewindow_object.loadImage(image_link)
    #========================ConvyerCamera last 5 defect==================================#  
    def post_button_1(self):
        self.imageView_button1.setStyleSheet("background-color : blue")
        
        #cell = QTableWidgetItem("Image")
        #font = QFont("Arial",15)
        #cell.setFont(font)
        #self.imageView_button1.setFont(cell)
        image_link = self.imageList[0]
        self.show_image(image_link)
        
    def post_button_2(self):
        self.imageView_button2.setStyleSheet("background-color : blue")
        image_link = self.imageList[1]
        self.show_image(image_link)
        
    def post_button_3(self):
        self.imageView_button3.setStyleSheet("background-color : blue")
        image_link = self.imageList[2]
        self.show_image(image_link)
        
    def post_button_4(self):
        self.imageView_button4.setStyleSheet("background-color : blue")
        image_link = self.imageList[3]
        self.show_image(image_link)
        
    def post_button_5(self):
        self.imageView_button5.setStyleSheet("background-color : blue")
        image_link = self.imageList[4]
        self.show_image(image_link)
    #========================DumpingCamera last 5 defect================================#    
    def post_buttonDumper_1(self):       
        self.pushButtonDumper1.setStyleSheet("background-color : blue")
        image_link = self.imageList[0]
        self.show_image(image_link)
        
    def post_buttonDumper_2(self):
        self.pushButtonDumper2.setStyleSheet("background-color : blue")
        image_link = self.imageList[1]
        self.show_image(image_link)
        
    def post_buttonDumper_3(self):
        self.pushButtonDumper3.setStyleSheet("background-color : blue")
        image_link = self.imageList[2]
        self.show_image(image_link)
        
    def post_buttonDumper_4(self):
        self.pushButtonDumper4.setStyleSheet("background-color : blue")
        image_link = self.imageList[3]
        self.show_image(image_link)
        
    def post_buttonDumper_5(self):
        self.pushButtonDumper5.setStyleSheet("background-color : blue")
        image_link = self.imageList[4]
        self.show_image(image_link)

    #========================DumpingCamera last 5defect fun End=========================#
    def show_processed_data(self):
        try:
            db_select = pymysql.connect(host=db_host,    # your host, usually localhost
                    user=db_user,         # your username
                    passwd=db_pass,  # your password
                    db=db_name)
            cur = db_select.cursor()
            query = "SELECT DATETIME, IMAGE_LINK, DEFECT_SIZE  FROM PROCESSING_TABLE where IS_RECORD_DEFECTED='1' order by ID desc limit 5"
            cur.execute(query)
            data_set = cur.fetchall()
            #print("show_processed_data Cooonver is :",data_set)
            cur.close()
            db_select.close()
 
            self.tableWidget.setRowCount(len(data_set))
            self.imageList = []
            counter = 1
            for row in range(0,len(data_set)):
                # cell = QTableWidgetItem(str(data_set[row][0]))
                # font = QFont("Arial",15)
                # cell.setFont(font)
                # cell.setTextAlignment(Qt.AlignCenter)
                # self.tableWidget.setItem(row, 0,cell)

                cell = QTableWidgetItem(str(data_set[row][2]))
                font = QFont("Arial",15)
                cell.setFont(font)
                cell.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 0,cell)

                cell = QTableWidgetItem(str(data_set[row][0]))
                font = QFont("Arial",15)
                cell.setFont(font)
                cell.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 1,cell)

                cell = QTableWidgetItem(str(data_set[row][1]))
                font = QFont("Arial",15)
                cell.setFont(font)
                cell.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 2,cell)
                self.imageList.append(data_set[row][1])
        except Exception as e:
            print('Exception : ',e)
            uilogger.critical(f"update Covyer cam images : "+ str(e))

    def show_processed_dataDumper(self):
        try:
            db_select = pymysql.connect(host=db_host,    # your host, usually localhost
                    user=db_user,         # your username
                    passwd=db_pass,  # your password
                    db=db_name)
            cur = db_select.cursor()
           
            query = '''SELECT CREATE_DATETIME, DEFECT_SIZE, NO_OF_DEFECT_COUNT, IMAGE_LINK FROM LIMESTONE_DB.PROCESSING_DUMPER_TABLE  order by ID DESC LIMIT 5;''' #WHERE DEFECT_SIZE >=1000
            cur.execute(query)
            data_set = cur.fetchall()
            # print("data_set show_processed_dataDumper ",data_set)
            cur.close()
            db_select.close()


            # image_link_1 = data_set[0][3]
            # self.BottomCam_Label.setPixmap(QtGui.QPixmap(image_link_1))

            self.tableWidget_3.setRowCount(len(data_set))
            self.imageList = []
            counter = 1
            for row in range(0,len(data_set)):

                cell = QTableWidgetItem(str(data_set[row][2]))
                font = QFont("Arial",10)
                cell.setFont(font)
                cell.setTextAlignment(Qt.AlignCenter)
                self.tableWidget_3.setItem(row, 0,cell)
                

                cell = QTableWidgetItem(str(data_set[row][0]))
                font = QFont("Arial",10)
                cell.setFont(font)
                cell.setTextAlignment(Qt.AlignCenter)
                self.tableWidget_3.setItem(row, 1,cell)

                cell = QTableWidgetItem(str(data_set[row][1]))
                font = QFont("Arial",10)
                cell.setFont(font)
                cell.setTextAlignment(Qt.AlignCenter)
                self.tableWidget_3.setItem(row, 2,cell)
                self.imageList.append(data_set[row][3])
                
        except Exception as e:
            print('Exception : ',e)
            uilogger.critical(f"show_processed_dataDumper : "+ str(e))


    def update_cam1_image(self):
        if os.path.exists(CAM1_IMAGE_LINK):
            self.TopCam_Label.setPixmap(QtGui.QPixmap(CAM1_IMAGE_LINK))
        else:
            pass #self.TopCam_Label.setPixmap(QtGui.QPixmap(NO_IMAGE_PATH))
        
        try:
            os.remove(CAM1_IMAGE_LINK)
        except Exception as e:
            print(f"Error in detecting CAM1_IMAGE_LINK")

    def update_cam2_image(self):
        print("DUMPINGImage")
        if os.path.exists(CAM2_IMAGE_LINK):
            self.BottomCam_Label.setPixmap(QtGui.QPixmap(CAM2_IMAGE_LINK))
        else:
            pass #self.BottomCam_Label.setPixmap(QtGui.QPixmap(NO_IMAGE_PATH))

        try:
            os.remove(CAM2_IMAGE_LINK)
        except Exception as e:
            print(f"Error in detecting CAM2_IMAGE_LINK")

    def update_image(self):
        self.update_cam1_image()
        self.update_cam2_image()

     #========================= SUSTEM STORGE CHECK =============================#
    def StorgeCheck_fun(self):
        total_gb = int(disk_usage.total / (1024 ** 3))
        used_gb = int(disk_usage.used / (1024 ** 3))
        available_gb = int(disk_usage.free / (1024 ** 3))
        #p=subprocess.run(['python','C:/Insightzz/Arrow_model_and_code_23/frame_cap_code_28_03_23.py'])

        # print(f"Total Storage: {total_gb} GB")
        # print(f"Used Storage: {used_gb} GB")
        # print(f"Available Storage: {available_gb} GB")  

        message = f"Total Storage: {total_gb} GB\n" \
          f"Used Storage: {used_gb} GB\n" \
          f"Available Storage: {available_gb} GB\n"\
          f"Please Clear System Storage"

        if used_gb > StorgeCheck:
            #self.show_messageStorge()
           # QtWidgets.QMessageBox.information(self,"Storge OverLode ","Data downloded in reports folder.")
            QtWidgets.QMessageBox.information(self, "Storage Overload", message, QtWidgets.QMessageBox.Ok)
        else:
            pass         
   
    def analyticsDataDumping(self):
        self.from_dateEdit_reportDump.setCalendarPopup(True)
        self.to_dateEdit_reportDump.setCalendarPopup(True)
        current_date = datetime.date.today()
        
        self.from_timeEdit_reportDump.setDate(current_date)
        self.to_timeEdit_reportDump.setDate(current_date)
        current_time = datetime.datetime.now().time()
        prev_time = (datetime.datetime.now() - datetime.timedelta(hours=2)).time()
        
        self.from_timeEdit_reportDump.setTime(prev_time)
        self.to_timeEdit_reportDump.setTime(current_time)
        self.defectSIze_reportCombo_Dump.setCurrentText("Defect_OverSize")
        # self.fetch_button_report_Dump.clicked.connect(self.fetchdata_ConveyorReport)
        # self.download_button_reportDump.clicked.connect(self.downloadButton)      
        
    def fetchdata_ConveyorReport(self):
        #print("you are in fetchdata_ConveyorReport()")
        from_date_temp = str(self.from_dateEdit_reportDump.date().toPyDate())
        from_time_temp = self.from_timeEdit_reportDump.time().toPyTime().strftime('%H:%M:%S') 
        
        to_date_temp = str(self.to_dateEdit_reportDump.date().toPyDate())
        to_time_temp = self.to_timeEdit_reportDump.time().toPyTime().strftime('%H:%M:%S')   

        
        startDate = from_date_temp + " "+from_time_temp
        endDate = to_date_temp + " "+to_time_temp        
        Cameradefect = self.defectSIze_reportCombo_Dump.currentText() #defecttype_comboBox
        
        try:            
            db_fetch = pymysql.connect(host = db_host,
                                       user = db_user,
                                       passwd = db_pass,
                                       db = db_name)
            cur = db_fetch.cursor() 
                   
            if self.from_dateEdit_ReportCone.date().toPyDate() > self.to_dateEdit_ReportCone.date().toPyDate():
                #print("right")
                self.summary_data_ReportCone.setText("Select Proper from date to Last date.")
                return 0
            # fromDate = self.from_dateEdit_ReportCone.date().toPyDate().strftime('%d-%m-%Y')
            # toDate = (self.to_dateEdit_ReportCone.date().toPyDate()+timedelta(days=1) ).strftime('%d-%m-%Y')
            fromDate = self.from_dateEdit_ReportCone.date().toPyDate().strftime('%Y-%m-%d')
            toDate = (self.to_dateEdit_ReportCone.date().toPyDate()+timedelta(days=1) ).strftime('%Y-%m-%d')     

            #print("from date",fromDate,"Todate ",toDate,)
            
            
           
            query = f'''select substring(t1.shiftDaywise,1,10) as date1, substring(t1.shiftDaywise,11,1) as SHIFT, t1.pa0_25, t1.pa26_40, t1.pa41_50, t1.pa51_75, t1.pa76_80, t1.pag80  from
                        (select concat(date_format(CURR_DATE,'%Y-%m-%d'),SHIFT) as shiftDaywise, sum(S0_25_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa0_25, sum(S26_40_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa26_40, sum(S41_50_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa41_50, sum(S51_75_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa51_75, sum(S76_80_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pa76_80, sum(G80_PIXELS)*100/(sum(NO_OF_FRAMES)*821741) as pag80 FROM LIMESTONE_DB.PERCENTAGE_ANALYSIS where CURR_DATE between "{fromDate}" and "{toDate}" group by shiftDaywise) as t1;'''
            cur.execute(query)
            data_set = cur.fetchall()
            #print("fetchdata Conveyor data_set is :",data_set)
            cur.close()
            db_fetch.close()
            header = self.tableWidget_2.horizontalHeader()
                    
            self.summary_data_ReportCone.setText("Total shifts are :-"+str(len(data_set)))
            counter = 1
            self.tableWidget_2.setRowCount(len(data_set))  
            has_none = False
            newPre25mm_2 = False
            for data in data_set:
                if None in data:
                    has_none = True
                    break
                else:
                    newPre25mm_2 = True
            newPre25mm = False
            if has_none:
                print("1")
                newPre25mm = True
                data_set = [[0 if x is None else x for x in tup] for tup in data_set] 

            for row in range(len(data_set)):
                    
                    self.tableWidget_2.setItem(row,0, QTableWidgetItem(f"{data_set[row][0].replace('_','-')}"))
                    self.tableWidget_2.setItem(row,1, QTableWidgetItem(f"{data_set[row][1]}"))

                    if data_set[row][2] and data_set[row][3] and data_set[row][4] and data_set[row][5] and data_set[row][6] and data_set[row][7] == "0":
                        print("Con -01")
                        #self.tableWidget_2.setItem(row,2, QTableWidgetItem("%.2f"% data_set[row][2]+ "%")) #0.00%
                        self.tableWidget_2.setItem(row,2, QTableWidgetItem("0.000%"))
                    
                    elif  data_set[row][2] == 0: 
                        print("Con -02") 
                        print("vk all value is - 0")  
                        self.tableWidget_2.setItem(row,2, QTableWidgetItem("0.000%"))
                        self.tableWidget_2.setItem(row,3, QTableWidgetItem("0.000%"))
                        self.tableWidget_2.setItem(row,4, QTableWidgetItem("0.000%"))
                        self.tableWidget_2.setItem(row,5, QTableWidgetItem("0.000%"))
                        self.tableWidget_2.setItem(row,6, QTableWidgetItem("0.000%")) 
                        self.tableWidget_2.setItem(row,7, QTableWidgetItem("0.000%"))

                    elif data_set[row][2] or data_set[row][3] or data_set[row][4] or data_set[row][5] or data_set[row][6] or data_set[row][7] == 0: 
                        print("Con -03") 
                        newPercentage = float(100 - (data_set[row][3]+data_set[row][4]+data_set[row][5]+data_set[row][6]+data_set[row][7]))
                        self.tableWidget_2.setItem(row,2, QTableWidgetItem("%.2f"% newPercentage+ "%"))     

                    elif data_set[row][2] and data_set[row][3] and data_set[row][4] and data_set[row][5] and data_set[row][6] and data_set[row][7] != 0: 
                        print("++++++++++++++++++++++++ newPercentage =======================") 
                        print("Con -04")
                        newPercentage = float(100 - (data_set[row][3]+data_set[row][4]+data_set[row][5]+data_set[row][6]+data_set[row][7]))
                        # self.tableWidget_2.setItem(row,2, QTableWidgetItem("%.2f"% data_set[row][2]+ "%"))
                        self.tableWidget_2.setItem(row,2, QTableWidgetItem("%.2f"% newPercentage+ "%")) 

                    self.tableWidget_2.setItem(row,3, QTableWidgetItem("%.2f"% data_set[row][3]+ "%"))
                    self.tableWidget_2.setItem(row,4, QTableWidgetItem("%.2f"% data_set[row][4]+ "%"))
                    self.tableWidget_2.setItem(row,5, QTableWidgetItem("%.2f"% data_set[row][5]+ "%")) 
                    self.tableWidget_2.setItem(row,6, QTableWidgetItem("%.2f"% data_set[row][6]+ "%")) 
                    self.tableWidget_2.setItem(row,7, QTableWidgetItem("%.2f"% data_set[row][7]+ "%")) 
                    # self.tableWidget_2.setItem(row,4, QTableWidgetItem(f"{data_set[row][3]}"))     
                       

                # qSelectButton = QPushButton("OpenImage")
                # qSelectButton.clicked.connect(lambda checked, agr1=IMAGE_LINK#, agr2= DATETIME: self.show_folder(agr1))
                # self.tableWidget_2.setCellWidget(row,3, qSelectButton)                           
        except Exception as e:
            print('fetch data Excption:', e)  
            uilogger.critical(f"fetchdata_ConveyorReport : "+ str(e))
                

    def fetchdata_DumperReport(self):
        try:
            db_select = pymysql.connect(host=db_host,    # your host, usually localhost
                    user=db_user,         # your username
                    passwd=db_pass,  # your password
                    db=db_name)
            cur = db_select.cursor()
            # from_date_temp = str(self.from_dateEdit_reportDump.date().toPyDate())
            from_date_temp = self.from_dateEdit_reportDump.date().toPyDate()
            # print("Type of date temp ",type(from_date_temp), from_date_temp.month, )
            # # from_date_temp = f"{from_date_temp.year}{from_date_temp.month}-{from_date_temp.day}"
            # print("new date:",from_date_temp)

            if from_date_temp > self.to_dateEdit_reportDump.date().toPyDate():
                self.summary_data_lable.setText("Enter proper Date.")
                return 0


            from_date_temp = self.from_dateEdit_reportDump.date().toPyDate().strftime('%Y-%m-%d')
            fromDate = self.from_dateEdit_reportDump.date().toPyDate()
            from_date_temp = str(fromDate.year) + "-"+str(fromDate.month) + "-"+str(fromDate.day)
            from_time_temp = self.from_timeEdit_reportDump.time().toPyTime().strftime('%H:%M:%S') 
            
            # to_date_temp = self.to_dateEdit_reportDump.date().toPyDate().strftime('%Y-%m-%d')
            toDate=self.to_dateEdit_reportDump.date().toPyDate() +timedelta(days=1)
            to_date_temp = str(toDate.year)+"-"+str(toDate.month)+"-"+str(toDate.day)
            to_time_temp = self.to_timeEdit_reportDump.time().toPyTime().strftime('%H:%M:%S')   
            startDate = from_date_temp + " "+from_time_temp
            endDate = to_date_temp + " "+to_time_temp 
            # print(startDate,endDate)
            # print(type(from_date_temp),type(from_time_temp),type(to_date_temp),type(to_time_temp))
            
            startDate = from_date_temp + " "+from_time_temp
            endDate = to_date_temp + " "+to_time_temp 
            # query = f'SELECT DATE_TIME, NO_COUNT, DEFECT_SIZE, IMAGE_LINK FROM CONVEYOR_BELT.PROCESSING_TABLE_DUMPER   where DATE_TIME between "{from_date_temp}" and "{to_date_temp}"  order by Date_time desc;'
            query = f'SELECT CREATE_DATETIME, NO_OF_DEFECT_COUNT, DEFECT_SIZE, IMAGE_LINK FROM LIMESTONE_DB.PROCESSING_DUMPER_TABLE where DEFECT_SIZE >=1000 and CREATE_DATETIME between "{from_date_temp}" and "{to_date_temp}"  order by CREATE_DATETIME desc ;'

            #print("fetchdata_DumperReport query is :",query)
            cur.execute(query)
            data_set = cur.fetchall()
            cur.close()
            db_select.close()

            self.tableWidget_2_reportDump.setRowCount(len(data_set))
            self.imageList = []
            counter = 0
            for row in range(0,len(data_set)):
                counter += 1

                dateTime = str(data_set[row][0])
                nuberOfCount = str(data_set[row][1])
                defectSize = str(data_set[row][2])   
                IMAGE_LINK = str(data_set[row][3])   

                self.tableWidget_2_reportDump.setItem(row,0, QTableWidgetItem(f"{data_set[row][0]}"))
                self.tableWidget_2_reportDump.setItem(row,1, QTableWidgetItem(f"{data_set[row][1]}"))
                self.tableWidget_2_reportDump.setItem(row,2, QTableWidgetItem(f"{data_set[row][2]}"))
                self.tableWidget_2_reportDump.setItem(row,3, QTableWidgetItem(f"{data_set[row][3]}"))          

                
                #========================================vk==============================================#
                qSelectButton = QPushButton("Image")
                qSelectButton.clicked.connect(lambda checked, arg1=IMAGE_LINK, arg2 = dateTime
                                              : self.showImage(arg1))

                self.tableWidget_2_reportDump.setCellWidget(row,3, qSelectButton)
            s1 = f"Total Violation is :- {len(data_set)}"
            self.summary_data_lable.setText(s1)
            # self.summary_data_lable.setText("Hello world")
            print("Total Violation is :-" +str(len(data_set)),s1)
                
        except Exception as e:
            print('Exception : ',e)
            uilogger.critical(f"fetchdata_DumperReport : "+ str(e))  
        
    def showImage(self,imagelink):
        try:
            if os.path.exists(imagelink):
                imagewindow_object.setWindowTitle(imagelink.split("/")[-1])
                imagewindow_object.loadImage(imagelink)
            else:
                imagelink = NO_IMAGE_PATH
                imagewindow_object.setWindowTitle(imagelink.split("/")[-1])
                imagewindow_object.loadImage(imagelink)
        except Exception as e:
            print("show_image  Exception is : "+str(e))

    def downloadButton(self):
            #print("You are in download buttotn***********************")
            try:
                db_select = pymysql.connect(host=db_host,    # your host, usually localhost
                        user=db_user,         # your username
                        passwd=db_pass,  # your password
                        db=db_name)
                cur = db_select.cursor()
                # from_date_temp = str(self.from_dateEdit_reportDump.date().toPyDate())
                from_date_temp = self.from_dateEdit_reportDump.date().toPyDate()
                # print("Type of date temp ",type(from_date_temp), from_date_temp.month, )
                # # from_date_temp = f"{from_date_temp.year}{from_date_temp.month}-{from_date_temp.day}"
                # print("new date:",from_date_temp)

                from_date_temp = self.from_dateEdit_reportDump.date().toPyDate().strftime('%Y-%m-%d')
                fromDate = self.from_dateEdit_reportDump.date().toPyDate()
                from_date_temp = str(fromDate.year) + "-"+str(fromDate.month) + "-"+str(fromDate.day)
                from_time_temp = self.from_timeEdit_reportDump.time().toPyTime().strftime('%H:%M:%S') 
                
                # to_date_temp = self.to_dateEdit_reportDump.date().toPyDate().strftime('%Y-%m-%d')
                toDate=self.to_dateEdit_reportDump.date().toPyDate() #+timedelta(days=1)
                to_date_temp = str(toDate.year)+"-"+str(toDate.month)+"-"+str(toDate.day)
                to_time_temp = self.to_timeEdit_reportDump.time().toPyTime().strftime('%H:%M:%S')   
                startDate = from_date_temp + " "+from_time_temp
                endDate = to_date_temp + " "+to_time_temp 
                # print(startDate,endDate)
                # print(type(from_date_temp),type(from_time_temp),type(to_date_temp),type(to_time_temp))
                
                startDate = from_date_temp + " "+from_time_temp
                endDate = to_date_temp + " "+to_time_temp 
               # print("start & end date******",startDate, endDate)

                # if from_date_temp > to_date_temp:
                #     self.summary_data_lable.setText("Select Proper from date to Last date.")
                #     return 0
                # query = "SELECT DATETIME, IMAGE_LINK, DEFECT_SIZE  FROM PROCESSING_TABLE_DUMPER where IS_RECORD_DEFECTED='1' order by ID desc limit 5"
                #query = f'SELECT DATE_TIME, NO_COUNT,DEFECT_SIZE,IMAGE_LINK FROM CONVEYOR_BELT.PROCESSING_TABLE_DUMPER   where DATE_TIME between "{from_date_temp}" and "{to_date_temp}"  order by Date_time desc;'
                query = f'SELECT CREATE_DATETIME, NO_OF_DEFECT_COUNT, DEFECT_SIZE, IMAGE_LINK FROM LIMESTONE_DB.PROCESSING_DUMPER_TABLE where CREATE_DATETIME between "{from_date_temp}" and "{to_date_temp}"  order by CREATE_DATETIME desc ;'
                cur.execute(query)
                data_set = cur.fetchall()
                cur.close()
                db_select.close()

                self.tableWidget_2_reportDump.setRowCount(len(data_set))
                self.imageList = []
                counter = 1
                date1 = []
                no_count = []
                defectSize = []
                imgLink = []
        
                
                #print("Original DataFrame:")
                #print('Data from Users.csv:')
                fromDate = fromDate.strftime('%Y-%m-%d').replace('-','_')
                toDate = toDate.strftime('%Y-%m-%d').replace('-',"_")
               # p=f'{DOWNLOAD_PATH_DUMPING}DumpingData{fromDate}_{toDate}{random.randint(0, 100)}.csv'
                path1 = DOWNLOAD_PATH_DUMPING+datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
                #print(f'{DOWNLOAD_PATH_DUMPING}DumpingData{fromDate}_{toDate}{random.randint(0, 100)}.csv')
                cdate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                image_path = DOWNLOAD_PATH_DUMPING+str(date.today())+"/"+"IMG_"+str(cdate)
                if not os.path.exists(image_path):
                    os.makedirs(image_path)
                
                f = open(path1+'.csv','w')
                dataStr = "DATE"+','+"NUMBER OF DEFECT"+','+"DEFECT SIZE"+','+"IMAGE_NAME"
                f.write(dataStr + '\n')
                for row in range(len(data_set)):
                    date1 = str(data_set[row][0])
                    no_count = str(data_set[row][1])
                    defectSize = str(data_set[row][2])
                    
                    IMAGE_LINK = str(data_set[row][3])
                    IMAGE_LINK1 = os.path.basename(IMAGE_LINK)
                    #print("IMAGE_LINK==============+++++++++++++++++++++++",IMAGE_LINK)
                   # print("IMAGE_LINK1============++++++++++++++++++++++++",IMAGE_LINK1)
                    # Use the basename function to get the filename of the source image file
                    image_file_name = os.path.basename(IMAGE_LINK)
                    destination_image_path = os.path.join(image_path, image_file_name)

                    try:
                        #shutil.copyfile(IMAGE_LINK1,image_path+os.path.basename(os.path.normpath(IMAGE_LINK)))
                        shutil.copyfile(IMAGE_LINK, destination_image_path)
                    except Exception as e:
                        print('Exception in copying image: ',e)
                        
                    dataStr = date1+','+no_count+','+defectSize+','+os.path.basename(IMAGE_LINK1)
                    f.write(dataStr + '\n')    
                   

                buttonReply = QMessageBox.question(self, 'Message', f"Are you sure you want to download? \n Download path: {path1}", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if buttonReply == QMessageBox.Yes:
                 
                    self.show_message("DumperYard Data Download successfully")   
                else:
                    print("Data not saved.")
                    pass            

                f.close()
            except Exception as e:
                print('Exception : ',e)
                uilogger.critical(f"update Dumper cam image : "+ str(e))   

                
class PhotoViewer(QtWidgets.QGraphicsView):
    photoClicked = QtCore.pyqtSignal(QtCore.QPoint)
    def __init__(self, parent):
        super(PhotoViewer, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QtWidgets.QGraphicsScene(self)
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def hasPhoto(self):
        return not self._empty

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0

    def setPhoto(self, pixmap=None):
        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())
        self.fitInView()

    def wheelEvent(self, event):
        if self.hasPhoto():
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            else:
                self._zoom = 0

    def toggleDragMode(self):
        if self.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def mousePressEvent(self, event):
        if self._photo.isUnderMouse():
            self.photoClicked.emit(self.mapToScene(event.pos()).toPoint())
        super(PhotoViewer, self).mousePressEvent(event)

class loginwindow(QtWidgets.QMainWindow,Ui_Login):
    def __init__(self, *args, obj=None, **kwargs):
        super(loginwindow, self).__init__(*args, **kwargs) 
        #uic.loadUi(UI_CODE_PATH+"login.ui", self)        
        self.setupUi(self)
        self.Enter_pushButton.clicked.connect(self.login)      
        self.password_lineEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.setWindowTitle("Drishti - Machine Vision Plateform")
        
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.login()
        #return super().keyPressEvent(a0)
 
    
    def login(self):
        uilogger.critical("LOGIN FUNCTION STARTS")
        name = str(self.username_lineEdit.text())
        password = str(self.password_lineEdit.text())
        print("=================loginwindow")
        if name == "" and password == "": 
            self.wrong_cred_label.setText(QtCore.QCoreApplication.translate("Login", "Username or Password can not be empty!"))
        elif name == "":
            self.wrong_cred_label.setText(QtCore.QCoreApplication.translate("Login", "Username can not be empty!"))
        elif password == "":
            self.wrong_cred_label.setText(QtCore.QCoreApplication.translate("Login", "Password can not be empty!"))                        
        else:
            try:
                #subprocess.Popen(["sh", start_plc_Helath])
                #subprocess.Popen(["sh", start_plc_service_sh])
                db_fetch = pymysql.connect(host=db_host,    # your host, usually localhost
                                            user=db_user,         # your username
                                            passwd=db_pass,  # your password
                                            db="LIMESTONE_DB")
                cur = db_fetch.cursor()
                query = "select USERNAME, PASSWORD from LIMESTONE_DB.LOGIN_TABLE"
                cur.execute(query)
                data_set = cur.fetchall()
                print("Login is :",data_set)
                cur.close()
                db_fetch.close()
                for row in range(0,len(data_set)):
                    if name == data_set[row][0] and password == data_set[row][1]:
                        print("correct")
                        main_object.show()
                        login_object.hide()
                        self.username_lineEdit.clear()
                        self.password_lineEdit.clear()
                        self.wrong_cred_label.clear()
            
                        # #================== Populating Combobox =======================#
                        try:
                            db_fetch = pymysql.connect(host=db_host,    # your host, usually localhost
                                         user=db_user,         # your username
                                         passwd=db_pass,  # your password
                                         db=db_name)
                            cur = db_fetch.cursor()
                            query = "select NO_OF_DEFECTS, DEFECT_SIZE from CONFIG_DUMPER_TABLE where IS_ACTIVE_CONFIG='1'"
                            cur.execute(query)
                            data_set = cur.fetchall()
                            print("data_set is vk :",data_set)
                            cur.close()
                            db_fetch.close()
                            dumpingLast_list = []
                            numberOfList = (data_set[0][0])
                            sizeOfList = (data_set[0][1])
                            print("numberOfList is",numberOfList)
                            print("sizeOfList is",sizeOfList)
                            main_object.numberOfdefect_comboboxDum.setText(str(numberOfList))#(prodn_list[i])
                            main_object.defectSize_Dump.setText(str(sizeOfList))
                        except Exception as e:
                            print('last seen combo Exception : ',e)
                            uilogger.critical("Error in login func-populating last seen combo:"+ str(e))
                            uilogger.critical(str(traceback.print_exc()))                                                    

                        # #================== populating last active configurations ===================#
                        
                        try:
                            db_fetch = pymysql.connect(host=db_host,    # your host, usually localhost
                                         user=db_user,         # your username
                                         passwd=db_pass,  # your password
                                         db=db_name)
                            cur = db_fetch.cursor()
                            query = "select PERCENTAGE, DEFECT_SIZE from CONFIG_TABLE where IS_ACTIVE_CONFIG='1'"
                            cur.execute(query)
                            data_set = cur.fetchall()
                            cur.close()
                            db_fetch.close()
                            Percentage = (data_set[0][0])
                            defectSizeConve = (data_set[0][1])
                            #print("numberOfList is",Percentage)
                            #print("sizeOfList is",defectSizeConve)

                            main_object.PercentageCombobox.setText(str(Percentage))
                            main_object.defectSizeComboboxConve.setText(str(defectSizeConve))
                        except Exception as e:
                            print('prodn_list Exception : ',e)
                            uilogger.critical("Error in login func-populating  configurations:"+ str(e))
                            uilogger.critical(str(traceback.print_exc()))                                                             
                    else:
                        self.wrong_cred_label.setText(QtCore.QCoreApplication.translate("Login", "Invalid Username or Password!"))        
                        
            except Exception as e:
                print('Exception : ',e)
                uilogger.critical("Error in login func:"+ str(e))
                uilogger.critical(str(traceback.print_exc()))                
        uilogger.critical("LOGIN FUNCTION ENDS")  

class ImageWindow(QtWidgets.QWidget):
    def __init__(self):
        super(ImageWindow, self).__init__()
        self.viewer = PhotoViewer(self)
        # 'Load image' button
        
        self.viewer.photoClicked.connect(self.photoClicked)
        # Arrange layout
        VBlayout = QtWidgets.QVBoxLayout(self)
        VBlayout.addWidget(self.viewer)
        HBlayout = QtWidgets.QHBoxLayout()
        HBlayout.setAlignment(QtCore.Qt.AlignLeft)
        VBlayout.addLayout(HBlayout)
        self.imagepath = ""        

    def show_message(self, message):
        choice = QMessageBox.information(self, 'Message!',message)

    def loadImage(self, imagelink):
        self.close()        
        self.setGeometry(100, 100, 680, 524)
        self.show()
        self.imagepath = imagelink        
        self.viewer.setPhoto(QtGui.QPixmap(imagelink))

    def pixInfo(self):
        self.viewer.toggleDragMode()

    def photoClicked(self, pos):
        if self.viewer.dragMode()  == QtWidgets.QGraphicsView.NoDrag:
            self.editPixInfo.setText('%d, %d' % (pos.x(), pos.y()))

class add_customer_login(QtWidgets.QMainWindow, Ui_add_customer_login):
    def __init__(self, *args, obj=None, **kwargs):
        super(add_customer_login, self).__init__(*args, **kwargs)        
        self.setupUi(self)    
        self.customer_pass_lineEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.setWindowTitle("Add Customer Login Window")
        self.customer_enter_button.clicked.connect(self.customer_login)     

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.customer_login() 
    
            
    def customer_login(self):
        uilogger.debug("LOGIN FUNCTION STARTS")
        name = str(self.customer_login_lineEdit.text())
        password = str(self.customer_pass_lineEdit.text())
        if name == "" and password == "": 
            self.wrong_cred_label.setText(QtCore.QCoreApplication.translate("Login", "Username or Password can not be empty!"))
        elif name == "":
            self.wrong_cred_label.setText(QtCore.QCoreApplication.translate("Login", "Username can not be empty!"))
        elif password == "":
            self.wrong_cred_label.setText(QtCore.QCoreApplication.translate("Login", "Password can not be empty!"))                        
        else:
            try:
                db_fetch = pymysql.connect(host=db_host,    # your host, usually localhost
                                            user=db_user,         # your username
                                            passwd=db_pass,  # your password
                                            db=db_name)
                cur = db_fetch.cursor()
                query = "select username, password, username2, password2 from LOGIN_CRED_TABLE"
                cur.execute(query)
                data_set = cur.fetchall()
                print("LOGIN_CRED_TABLE data_set:",data_set)
                cur.close()
                db_fetch.close()
                for row in range(0,len(data_set)):
                    if name == data_set[row][0] and password == data_set[row][1]:
                        print("correct")
                        add_customer_login_object.hide()
                        main_object.addConfigDumper()
                        self.customer_login_lineEdit.clear()
                        self.customer_pass_lineEdit.clear()
                        self.wrong_cred_label.clear()  

                    elif name == data_set[row][2] and password == data_set[row][3]:
                        print("correct")
                        add_customer_login_object.hide()
                        main_object.save_post_data()
                        self.customer_login_lineEdit.clear()
                        self.customer_pass_lineEdit.clear()
                        self.wrong_cred_label.clear()        

                    else:
                        main_object.show_message("Add Config Login is not valid")    

            except Exception as e:
                print("Exception in Login add customer", e) 

    

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_object = mainwindow()
    login_object = loginwindow()
    #login_object.show()
    imagewindow_object= ImageWindow()
    #data_record_object = DataRecord_Window()
    main_object.show()
    add_customer_login_object = add_customer_login()
    #data_record_object.show()
    app.exec()
