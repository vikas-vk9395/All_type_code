import cv2
import os
import traceback
import pymysql
import datetime
import time
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog, DatasetCatalog
from detectron2.structures import BoxMode
from detectron2.engine import DefaultTrainer
from detectron2.utils.visualizer import ColorMode
import numpy as np
import logging
import ast
import xml.etree.ElementTree as ET
import json
from PIL import Image
from skimage.io import imread
from PIL import ImageFont, ImageDraw, Image
from fpdf import FPDF
from shapely.geometry import Point, Polygon
from subprocess import Popen, PIPE

os.environ['CUDA_VISIBLE_DEVICES']='0'

DEMO_RUN_FLAG = False

# Load configuration from XML
config_path = "C:/insightzz/CAM_CAP/UI_CODE/APP_CONFIG.xml"
if DEMO_RUN_FLAG:
    config_path =  "/home/viks/VIKS/CODE/PROJECT_ALGORITHAM/NEW_EGAL_PROJECT/CAM_CAP_HLA/17_DEC/APP_CONFIG.xml"

config_parse = ET.parse(config_path)
config_root = config_parse.getroot()
CODE_PATH = config_root[0].text
DB_USER = config_root[1].text
DB_PASS = config_root[2].text
DB_HOST = config_root[3].text
DB_NAME = "hla_cam_cap_db"#config_root[4].text
NUMCLASSES = int(config_root[5].text)
DETECTTHRESH = float(config_root[6].text)
SAVED_FOLDER_PATH = config_root[7].text
MASK_MODEL_PATH = config_root[8].text
CONFIG_YAML_FL_PATH = config_root[9].text
ALL_CLASS_NAMES = "c:/insightzz/CAM_CAP/Model/HLA_IMPROVE.json"
if DEMO_RUN_FLAG is True:
    ALL_CLASS_NAMES = "/home/viks/VIKS/CODE/PROJECT_ALGORITHAM/NEW_EGAL_PROJECT/CAM_CAP_HLA/MODEL_1_JAN_HLA/31DEC.json"
NON_DEFECTIVE_CLASS_NAME = ast.literal_eval(config_root[11].text)
DEPLOYMENT_STATUS = int(config_root[12].text)
CAM_INF_PROCESSNAME = config_root[13].text
BGT_TH_VALUE = int(config_root[14].text)
DOWNLOAD_PATH = "/C:/Desktop/Downloads/" 
if DEMO_RUN_FLAG is False:
    DOWNLOAD_PATH = "/home/shrish/Desktop/Downloads/"

# Set up logger
logger = logging.getLogger("MAHINDRA_CAM_CAP_HLA")
logger.setLevel(logging.DEBUG)
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger_fh = logging.FileHandler("MAHINDRA_CAM_CAP_HLA.log", mode='a')
logger_fh.setFormatter(log_format)
logger.addHandler(logger_fh)



#===================== for pdf ===========================#
from fpdf import FPDF
import os
from PIL import ImageFont, ImageDraw, Image
import datetime
import pymysql

gMailObj = None



def __loadLablMap__():
    #load labelmap
    with open(ALL_CLASS_NAMES,"r") as fl:
        labelMap=json.load(fl)
    return labelMap

labelMap = __loadLablMap__()
label_classes=list(labelMap.values())

class MaskRCNN_Mahindra:
    def __init__(self):
        global CONFIG_YAML_FL_PATH, MASK_MODEL_PATH, DETECTTHRESH, logger
        self.predictor = None
        self.mrcnn_config_fl = CONFIG_YAML_FL_PATH
        self.mrcnn_model_loc = MASK_MODEL_PATH
        self.mrcnn_model_fl = "model_final.pth"
        self.detection_thresh = 0.5#DETECTTHRESH
        self.register_modeldatasets()
        logger.debug("Mask RCNN INIT Completed")
    
    def register_modeldatasets(self):
        global ALL_CLASS_NAMES, NUMCLASSES, DEMO_RUN_FLAG
        tag = "mahindra_test"
        MetadataCatalog.get(tag).set(thing_classes=[label_classes])
        self.railway_metadata = MetadataCatalog.get(tag)
        cfg = get_cfg()
        cfg.merge_from_file(self.mrcnn_config_fl)
        if DEMO_RUN_FLAG:
            cfg.MODEL.DEVICE='cpu'
        cfg.MODEL.ROI_HEADS.NUM_CLASSES = 37
        cfg.OUTPUT_DIR = self.mrcnn_model_loc
        cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, self.mrcnn_model_fl)
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = self.detection_thresh
        self.predictor = DefaultPredictor(cfg)

    def run_inference_new(self,img_path):
        #total_t = int(time.time()*1000)
        try:
            img = cv2.imread(img_path)  # Read the image using OpenCV
            output = self.predictor(img)
            # output = self.predictor(img)
        except Exception as e:
            print(traceback.format_exc())
            logger.debug(f"run_inference_new() : Exception is : {e}, Traceback : {traceback.format_exc()}")
        #print("Only INF Time  = ", int(time.time()*1000) - total_t)
        predictions=output["instances"].to("cpu")
        boxes_surface = predictions.pred_boxes.tensor.to("cpu").numpy()
        pred_class_surface = predictions.pred_classes.to("cpu").numpy()
        #print(pred_class_surface.tolist())
        scores_surface = predictions.scores.to("cpu").numpy()  

        masklist = []
        masks = None  
        if predictions.has("pred_masks"):
            masks = predictions.pred_masks.numpy() 
        #print("Only INF Time  = ", int(time.time()*1000) - total_t)     
        return self.processObjectList(boxes_surface,pred_class_surface, scores_surface,masks)

    def processObjectList(self, boxes_surface,pred_class_surface, scores_surface,masks):   
        global ALL_CLASS_NAMES, DETECTTHRESH, logger
        try:
            OBJECT_LIST = []
            for i,box in enumerate(boxes_surface):
                label_name = label_classes[pred_class_surface[i]]
                if scores_surface[i] > DETECTTHRESH:
                    box = boxes_surface[i]
                    xmin = int(box[0])
                    ymin = int(box[1])
                    xmax = int(box[2])
                    ymax = int(box[3])                
                    item = []
                    item.append(label_name)
                    item.append(xmin)
                    item.append(ymin)
                    item.append(xmax)
                    item.append(ymax)

                    try:
                        masklist = np.column_stack(np.where(masks[i] == True))
                    except:
                        masklist = []  

                    cx,cy = get_centroid(xmin, xmax, ymin, ymax)
                    item.append(scores_surface[i])
                    item.append(cx)
                    item.append(cy)
                    item.append(masklist)
                    OBJECT_LIST.append(item)
            filtered_labellist = filter_classes_within_diesel_roi(OBJECT_LIST)
          #  f.debug("Inference Completed")
        except Exception as e:
            logger.debug(f"except Exception run_inference_new in processObjectList{e}")
            logger.critical(f"processObjectList() Exception is : {e}, Traceback : {traceback.format_exc()}")
        return filtered_labellist
    
    def run_inference_sea(self,img_path):
        #total_t = int(time.time()*1000)
        try:
            img = cv2.imread(img_path)  # Read the image using OpenCV
            output = self.predictor(img)
            # output = self.predictor(img)
        except Exception as e:
            print(e)
            print(traceback.format_exc())
        #print("Only INF Time  = ", int(time.time()*1000) - total_t)
        predictions=output["instances"].to("cpu")
        boxes_surface = predictions.pred_boxes.tensor.to("cpu").numpy()
        pred_class_surface = predictions.pred_classes.to("cpu").numpy()
        #print(pred_class_surface.tolist())
        scores_surface = predictions.scores.to("cpu").numpy()  
      
        masks = None  
        if predictions.has("pred_masks"):
            masks = predictions.pred_masks.numpy() 
        #print("Only INF Time  = ", int(time.time()*1000) - total_t)     
        return self.processObjectList_sea(boxes_surface,pred_class_surface, scores_surface,masks)

    def processObjectList_sea(self, boxes_surface,pred_class_surface, scores_surface,masks):   
        global ALL_CLASS_NAMES, DETECTTHRESH, logger
        try:
            OBJECT_LIST = []
            for i,box in enumerate(boxes_surface):
                label_name = label_classes[pred_class_surface[i]]
                if scores_surface[i] > DETECTTHRESH:
                    box = boxes_surface[i]
                    xmin = int(box[0])
                    ymin = int(box[1])
                    xmax = int(box[2])
                    ymax = int(box[3])                
                    item = []
                    item.append(label_name)
                    item.append(xmin)
                    item.append(ymin)
                    item.append(xmax)
                    item.append(ymax)

                    try:
                        masklist = np.column_stack(np.where(masks[i] == True))
                    except:
                        masklist = []  

                    cx,cy = get_centroid(xmin, xmax, ymin, ymax)
                    item.append(scores_surface[i])
                    item.append(cx)
                    item.append(cy)
                    item.append(masklist)
                    OBJECT_LIST.append(item)
            # filtered_labellist = filter_classes_within_diesel_roi(OBJECT_LIST)
            logger.debug("Inference Completed")
        except Exception as e:
            logger.debug(f"except Exception run_inference_sea in processObjectList{e}")
            logger.debug(f"processObjectList_sea() Exception is : {e}, Traceback : {traceback.format_exc()}")
        return OBJECT_LIST

def get_centroid(xmin, xmax, ymin, ymax):
    cx = int((xmin + xmax) / 2.0)
    cy = int((ymin + ymax) / 2.0)
    return(cx, cy)


# def filter_classes_within_diesel_roi(labellist):
#     try:
#         # Calculate the boundaries based on the coordinates of "diesel_roi"
#         diesel_roi_x_min, diesel_roi_x_max, diesel_roi_y_min, diesel_roi_y_max = None, None, None, None

#         for label_info in labellist:
#             if label_info[3] < 1800:
#                 if label_info[0] == 'number_roi':
#                 # y_min, y_max, x_min, x_max = label_info[1], label_info[2], label_info[3], label_info[4]
#                     y_min, y_max, x_min, x_max = label_info[2], label_info[4], label_info[1], label_info[3]
#                     diesel_roi_x_min = x_min
#                     diesel_roi_x_max = x_max
#                     diesel_roi_y_min = y_min
#                     diesel_roi_y_max = y_max

#         if diesel_roi_x_min is not None:
#             # Create a list to store filtered classes
#             filtered_labellist = []

#             # Iterate through labellist and compare class coordinates with 'diesel_roi'
#             for label_info in labellist:
#                 y_1, y_2, x_1, x_2 = label_info[2], label_info[4], label_info[1], label_info[3]

#                 if label_info[0] == 'number_roi' or label_info[0] == "hla_base_half" or label_info[0] =="cam_cap_missing" or label_info[0] =="hla_top":
#                     filtered_labellist.append(label_info)
#                 elif label_info[0] in ["cam_cap_E", "cam_cap_I", "cam_cap_1", "cam_cap_3", "cam_cap_4", "cam_cap_5", "cam_cap_2",  "NOT_OK_E","NOT_OK_arrow","NOT_OK_2","NOT_OK_I","NOT_OK_3","NOT_OK_4","NOT_OK_5","NOT_OK_1"]:
#                     # Check if the class is inside the 'number_roi'
#                     if diesel_roi_x_max > x_1 and diesel_roi_x_min < x_2 and diesel_roi_y_max > y_1 and diesel_roi_y_min < y_2:
#                         filtered_labellist.append(label_info)
#                 else:
#                     if label_info[3] < 1800:
#                         if label_info[0] == "hla_base":
#                             if label_info[3] > 600:
#                                 filtered_labellist.append(label_info)
#                             else:
#                                 print("Bolt detected as hla_base")
#                         # Include other classes regardless of position
#                         else:
#                             filtered_labellist.append(label_info)

#             return filtered_labellist
#         else:
#             print("No 'number_roi' class found in labellist.")
#             return []
    
#     except Exception as e:
#         print("except Exception filter_classes_within_diesel_roi",e)
#         logger.debug(f"except Exception filter_classes_within_diesel_roi {e}")

def filter_classes_within_diesel_roi(labellist):
    try:
        # Calculate the boundaries based on the coordinates of "diesel_roi"
        diesel_roi_x_min, diesel_roi_x_max, diesel_roi_y_min, diesel_roi_y_max = None, None, None, None

        diesel_roi_x_min_num_roi, diesel_roi_x_max_num_roi, diesel_roi_y_min_num_roi, diesel_roi_y_max_num_roi = None, None, None, None

        for label_info in labellist:
            if label_info[3] < 1800:
                if label_info[0] == 'roi':
                    y_min, y_max, x_min, x_max = label_info[2], label_info[4], label_info[1], label_info[3]
                    diesel_roi_x_min = x_min
                    diesel_roi_x_max = x_max
                    diesel_roi_y_min = y_min
                    diesel_roi_y_max = y_max
                
                if label_info[0] == 'number_roi':
                    y_min, y_max, x_min, x_max = label_info[2], label_info[4], label_info[1], label_info[3]
                    diesel_roi_x_min_num_roi = x_min
                    diesel_roi_x_max_num_roi = x_max
                    diesel_roi_y_min_num_roi = y_min
                    diesel_roi_y_max_num_roi = y_max

        if diesel_roi_x_min is not None:
            # Create a list to store filtered classes
            filtered_labellist = []

            # Iterate through labellist and compare class coordinates with 'diesel_roi'
            for label_info in labellist:
                y_1, y_2, x_1, x_2 = label_info[2], label_info[4], label_info[1], label_info[3]
                if label_info[0] == 'roi':
                    filtered_labellist.append(label_info)

                if label_info[0] in ["cam_cap_E", "cam_cap_I", "cam_cap_1", "cam_cap_3", "cam_cap_4", "cam_cap_5", "cam_cap_2",  "NOT_OK_E","NOT_OK_arrow","NOT_OK_2","NOT_OK_I","NOT_OK_3","NOT_OK_4","NOT_OK_5","NOT_OK_1"]:
                    if diesel_roi_x_max_num_roi > x_1 and diesel_roi_x_min_num_roi < x_2 and diesel_roi_y_max_num_roi > y_1 and diesel_roi_y_min_num_roi < y_2:
                        filtered_labellist.append(label_info)
                    else:
                        print("class not found in roi")

                elif (diesel_roi_x_max > x_1 ) and (diesel_roi_x_min < x_2 ) and (diesel_roi_y_max > y_1 ) and (diesel_roi_y_min < y_2 ):
                    filtered_labellist.append(label_info)

            return filtered_labellist
        else:
            print("No 'number_roi' class found in labellist.")
            return []
    
    except Exception as e:
        print("except Exception filter_classes_within_diesel_roi",e)
        logger.debug(f"except Exception filter_classes_within_diesel_roi {e}")

def getInferenceTrigger():
    #Engine_no, Position,IS_PROCESS,ImageLink = "", "", None,"", ImageLink_2 = ""
    db_fetch = None
    cur = None
    try:
        db_fetch = pymysql.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cur = db_fetch.cursor()
        query = "select * from config_table;"
        cur.execute(query)
        data_set = cur.fetchall()
        for row in range(len(data_set)):
            Engine_no = str(data_set[row][1])
            Position = int(data_set[row][2])
            IS_PROCESS = int(data_set[row][3])
            ImageLink = str(data_set[row][4])
            ImageLink_2 = str(data_set[row][5])
    except Exception as e:
        logger.error(f"Error in getting inference trigger: {e}, Traceback : {traceback.format_exc()}")
    finally:
        if cur is not None:
            cur.close()
        if db_fetch is not None:
            db_fetch.close()

    return Engine_no, Position,IS_PROCESS,ImageLink, ImageLink_2

def update_inference_trigger(IS_PROCESS,STATUS):
    db_update = None
    cur = None
    try:
        db_update = pymysql.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db= DB_NAME)
        cur = db_update.cursor()
        query = "UPDATE config_table SET Is_Process = %s, Status = %s, Image_Link = %s, Image_Link_Cam2 = %s WHERE ID = 1"
        cur.execute(query, (IS_PROCESS,STATUS,"",""))
        db_update.commit()
    except Exception as e:
        print("Update_Program_No() Exception is : "+ str(e))
        logger.critical(f"Update_Program_No() Exception is : {e}, Traceback : {traceback.format_exc()}")
    finally:
        if cur is not None:
            cur.close()
        if db_update is not None:
            db_update.close()

def update_result_trigger(STATUS):
    db_update = None
    cur = None
    try:
        db_update = pymysql.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db= DB_NAME)
        cur = db_update.cursor()
        query = "UPDATE result_tabel SET  Status = %s"
        cur.execute(query, (STATUS))
        db_update.commit()
    except Exception as e:
        print("update_result_trigger() Exception is : "+ str(e))
        logger.debug(f"except Exception update_result_trigger{e}")
        logger.critical(f"update_result_trigger() Exception is : {e}, Traceback : {traceback.format_exc()}")
    finally:
        if cur is not None:
            cur.close()
        if db_update is not None:
            db_update.close()

def insertDataIndotprocessing_table(Engine_no, STATUS, raw_image, processed_image_path, defects, ok_parts):
    IS_PROCESS_INF = 1
    try:
        defects_str = str(defects).replace("'", "").replace(" ", "")
        ok_parts_str = str(ok_parts).replace("'", "").replace(" ", "")
        db_update = pymysql.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cur = db_update.cursor()
        query = "INSERT INTO processing_table (Engine_no, Status, Raw_image, Processed_image,Defects,OK_Lists) VALUES (%s, %s, %s, %s, %s, %s);"
        cur.execute(query, (Engine_no, STATUS, raw_image, processed_image_path, defects_str, ok_parts_str))
        db_update.commit()
        IS_PROCESS_INF = 2
    except Exception as e:
        logger.debug(f"except Exception insertDataIndotprocessing_table {e}")
        logger.error(f"Error in inserting data: {e}, Traceback : {traceback.format_exc()}")

    finally:
        if cur:
            cur.close()
        if db_update:
            db_update.close()

    return IS_PROCESS_INF, STATUS

def getInferenceTrigger_2():
    #Engine_no, Position,IS_PROCESS,ImageLink = "", "", None,"", ImageLink_2 = ""
    db_fetch = None
    cur = None
    try:
        db_fetch = pymysql.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cur = db_fetch.cursor()
        query = "select * from config_table;"
        cur.execute(query)
        data_set = cur.fetchall()
        for row in range(len(data_set)):
            Engine_no = str(data_set[row][1])
            #Position = int(data_set[row][2])
            StatusPreview = str(data_set[row][6])
           
    except Exception as e:
        logger.error(f"Error in getting inference trigger: {e}, Traceback : {traceback.format_exc()}")
    finally:
        if cur is not None:
            cur.close()
        if db_fetch is not None:
            db_fetch.close()

    return Engine_no, StatusPreview


def Arrow_Position_Check(Postion, image, labellist):
    arrow_pinLocation = [890, 697], [892, 780], [975, 782], [972, 695]
    Arrow_Pos_Status = False
    Position_Status = False

    try:
        for smalllabellist in labellist:
            centroid_xMaxyMax = smalllabellist[6]
            current_class = smalllabellist[0]
            xmin, ymin, xmax, ymax = smalllabellist[1:5]

            # ======================== cam_cap_arrow ==================================#
            if current_class == 'cam_cap_arrow':
                centroid_xMaxyMax = smalllabellist[6]
                centroid_yMaxYmin = smalllabellist[7]
                if Postion == 2:
                    if 1040 <= centroid_xMaxyMax <= 1260 and 900 <= centroid_yMaxYmin <= 1090: #FOR E1
                        Arrow_Pos_Status = True
                    else:
                        Arrow_Pos_Status = False
                        color = (0, 0, 255)
                        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 7)
                        label_text = f"{smalllabellist[0]}: {smalllabellist[5]:.2f}"
                        cv2.putText(image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)

                elif Postion == 3:
                    #if 1060 <= centroid_xMaxyMax or centroid_xMaxyMax <= 1175 or 1265 <= centroid_xMaxyMax or centroid_xMaxyMax <= 1110: #FOR E2
                    if 1270 <= centroid_xMaxyMax <= 1460 and 1030 <= centroid_yMaxYmin <= 1180:#FOR E2
                        Arrow_Pos_Status = True
                    else:
                        Arrow_Pos_Status = True#False
                        color = (0, 0, 255)
                        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 7)
                        label_text = f"{smalllabellist[0]}: {smalllabellist[5]:.2f}"
                        cv2.putText(image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)


                elif Postion == 4 :
                    if 860 <= centroid_xMaxyMax <= 1060 and 790 <= centroid_yMaxYmin <= 970: #FOR E3
                        Arrow_Pos_Status = True
                    else:
                        Arrow_Pos_Status = False
                        color = (0, 0, 255)
                        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 7)
                        label_text = f"{smalllabellist[0]}: {smalllabellist[5]:.2f}"
                        cv2.putText(image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)


                elif Postion == 5:
                    if 1015 <= centroid_xMaxyMax <= 1225 and 940 <= centroid_yMaxYmin <= 1110: #FOR E4  x y
                        Arrow_Pos_Status = True
                    else:
                        Arrow_Pos_Status = False
                        color = (0, 0, 255)
                        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 7)
                        label_text = f"{smalllabellist[0]}: {smalllabellist[5]:.2f}"
                        cv2.putText(image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)

                # elif Postion == 6 and 810 <= centroid_xMaxyMax <= 930 and 880 <= centroid_xMaxyMax <= 1065: #FOR i5
                #     Arrow_Pos_Status = True
                
                elif Postion == 7:
                    if 1140 <= centroid_xMaxyMax <= 1350 and 1150 <= centroid_yMaxYmin <= 1340: #FOR I4
                        Arrow_Pos_Status = True
                    else:
                        Arrow_Pos_Status = False
                        color = (0, 0, 255)
                        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 7)
                        label_text = f"{smalllabellist[0]}: {smalllabellist[5]:.2f}"
                        cv2.putText(image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)

                elif Postion == 6:
                    if 980 <= centroid_xMaxyMax <= 1190 and 1020 <= centroid_yMaxYmin <= 1220: #FOR I3
                        Arrow_Pos_Status = True
                    else:
                        Arrow_Pos_Status = False
                        color = (0, 0, 255)
                        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 7)
                        label_text = f"{smalllabellist[0]}: {smalllabellist[5]:.2f}"
                        cv2.putText(image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)

                elif Postion == 9:#
                    if 1215 <= centroid_xMaxyMax <= 1450 and 1150 <= centroid_yMaxYmin <= 1330: #FOR I2
                        Arrow_Pos_Status = True
                    else:
                        Arrow_Pos_Status = False
                        color = (0, 0, 255)
                        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 7)
                        label_text = f"{smalllabellist[0]}: {smalllabellist[5]:.2f}"
                        cv2.putText(image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
                
                elif Postion == 8 :
                    if 1050 <= centroid_xMaxyMax <= 1280 and 990 <= centroid_yMaxYmin <= 1180: #FOR I1
                        Arrow_Pos_Status = True
                    else:
                        Arrow_Pos_Status = False
                        color = (0, 0, 255)
                        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 7)
                        label_text = f"{smalllabellist[0]}: {smalllabellist[5]:.2f}"
                        cv2.putText(image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7) 
                
                elif Postion == 11 :
                    if 1170 <= centroid_xMaxyMax <= 1320 and 1130 <= centroid_yMaxYmin <= 1250: #FOR I1
                        Arrow_Pos_Status = True
                    else:
                        Arrow_Pos_Status = False
                        color = (0, 0, 255)
                        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 7)
                        label_text = f"{smalllabellist[0]}: {smalllabellist[5]:.2f}"
                        cv2.putText(image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7) 

        # ===================== Overall Position Status ===========================#
        Position_Status = Arrow_Pos_Status

    except Exception as e:
        logger.debug(f"except Exception Arrow_Position_Check {e}")
        print(f"Error in Arrow_Position_Check: {e}")

    print("Position_Status:", Position_Status)
    return Position_Status,image

    #return Position_Status

def HLA_classCheck(OBJECT_LIST):
    TOP_HLA_CLASS_NAME_LIST1_STATUS = False
    try:
        if sum(sublist.count('hla_top') for sublist in OBJECT_LIST) == 2:
            print(" HLA_classCheck Status OK ")
            TOP_HLA_CLASS_NAME_LIST1_STATUS = True    
            #print("TOP_HLA 2 IS NOT OK")  

        else:
            print(" HLA_classCheck Status not OK ")
            TOP_HLA_CLASS_NAME_LIST1_STATUS = False

        return TOP_HLA_CLASS_NAME_LIST1_STATUS
    except Exception as e:
        logger.debug(f"except Exception HLA_classCheck {e}")
        print("HLA_classCheck is :",e)


def HLA_PostionCheck_with_nut(Position,OBJECT_LIST,original_image):
    isHLA_PositionCorrect = False
    center_of_hla = []
    center_of_nut = []
    # HLA_POSTION_RIGHT = "NOT OK"
    # HLA_POSTION_LEFT = "NOT OK"
    # HLA_POSTION ="NOT OK"

    HLA_POSTION_RIGHT = "OK"
    HLA_POSTION_LEFT = "OK"
    HLA_POSTION ="OK"
    center_of_hla = False
    center_of_nut = False
    center_of_hla_top=0
    try: 
        #======================================= E1 
        if Position ==2:           #E1
            leftSide_Cord = 0
            RightSide_Cord=0
            hla_label_dict_left = {}
            hla_label_dict_right = {}
            for smalllabellist in OBJECT_LIST:
                xmin, ymin, xmax, ymax = smalllabellist[1:5]
                print(smalllabellist[0])

                if smalllabellist[1]  > 1240:
                    if smalllabellist[0] == 'hla_top':
                        hla_label_dict_left['0'] = [smalllabellist]
                    elif smalllabellist[0] == 'hla_rod_top':
                        hla_label_dict_left['1'] = [smalllabellist]
                else:
                    if smalllabellist[0] == 'hla_top':
                        hla_label_dict_right['0'] = [smalllabellist]
                    elif smalllabellist[0] == 'hla_rod_top':
                        hla_label_dict_right['1'] = [smalllabellist]

            ''' Left Side check '''
            try: 
                thresholdPixel_RightSide_1 = 18#21#23#18#20 #60
                thresholdPixel_RightSide_2 = 27#22#23#26#16
                hla_top_L = hla_label_dict_left.get('0')
                xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

                hla_rod_top_L = hla_label_dict_left.get('1')
                xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]

                logger.debug(f"Left E1, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} AND xminTL IS {xminTL} thresholdPixel_RightSide_1 {thresholdPixel_RightSide_1} and thresholdPixel_RightSide_2 {thresholdPixel_RightSide_2}")
                if xmaxTL > 1850:
                    logger.debug(f"decrese thresholdPixel_RightSide_1 = 15")
                    thresholdPixel_RightSide_1= 25
                
                if xmaxTL < 1616:
                    logger.debug(f"increse thresholdPixel_RightSide_2 = 25")
                    thresholdPixel_RightSide_2= 27
                    
                if  xmaxTL < (xmaxRTL - thresholdPixel_RightSide_1) or xmaxTL > (xmaxRTL + thresholdPixel_RightSide_2): #ok xmaxTL - 1858
                    logger.debug(f"HLA_POSTION_RIGHT = NOT OK")
                    HLA_POSTION_LEFT = "NOT OK"
                    color = (0, 0, 255)
                    #if smalllabellist[0] == 'hla_top':
                    xmin, ymin, xmax, ymax = hla_top_L[0][1:5]

                    cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
                    label_text = ""#f"{smalllabellist[0]}.2f"
                    cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7) 
                else:
                    HLA_POSTION_LEFT = "OK"
                    logger.debug(f"HLA_POSTION_RIGHT = OK")
            except Exception as e:
                logger.debug(f"except Exception E1 Left Side check {e}")
                print("except Exception E1 Left Side check :",e)

            ''' Right Side check '''
            try:
                thresholdPixel_LeftSide_1 = 43#25#29 #65
                thresholdPixel_LeftSide_2 = 52#55
                hla_top_L = hla_label_dict_right.get('0')
                xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

                hla_rod_top_L = hla_label_dict_right.get('1')
                xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]

                RightSide_Cord = xminRTL - xminTL
                print(f"RightSide_Cord is :{RightSide_Cord} ")
                logger.debug(f"E1, Position ==2 RightSide_Cord {RightSide_Cord}")

                logger.debug(f"Right E1, xminTL :{xminTL} AND xminRTL : {xminRTL} thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} and thresholdPixel_LeftSide_2 {thresholdPixel_LeftSide_2}")
                if xminTL < 860:
                    logger.debug(f"Dincrese xmaxTL {xmaxTL} thresholdPixel_LeftSide_2 = 27")
                    thresholdPixel_LeftSide_2= 25
                #if  RightSide_Cord > 30 and RightSide_Cord < 45:
                if  xminTL < (xminRTL - thresholdPixel_LeftSide_1) or xminTL > (xminRTL + thresholdPixel_LeftSide_2): #xminTL ok -1081
                    HLA_POSTION_RIGHT = "NOT OK"
                    logger.debug(f"HLA_POSTION_RIGHT = NOT OK")
                    color = (0, 0, 255)
                    #if smalllabellist[0] == 'hla_top':
                    xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
                    cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
                    label_text = ""#f"{smalllabellist[0]}.2f"
                    cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)

                else:
                    HLA_POSTION_RIGHT = "OK"
                    logger.debug(f"HLA_POSTION_RIGHT = OK")
            except Exception as e:
                logger.debug(f"except Exception E1 Right Side check {e}")
                print("except Exception E1 Right Side check :",e)
        #======================================= E2
        elif Position ==3:                                                 #E2
            hla_label_dict_left = {}
            hla_label_dict_right = {}
            leftSide_Cord = 0
            RightSide_Cord=0
            
            for smalllabellist in OBJECT_LIST:
                xmin, ymin, xmax, ymax = smalllabellist[1:5]
                print(smalllabellist[0])
                if smalllabellist[1]  > 1350:
                    if smalllabellist[0] == 'hla_top':
                        hla_label_dict_left['0'] = [smalllabellist]
                    elif smalllabellist[0] == 'hla_rod_top':
                        hla_label_dict_left['1'] = [smalllabellist]
                else:
                    if smalllabellist[0] == 'hla_top':
                        hla_label_dict_right['0'] = [smalllabellist]
                    elif smalllabellist[0] == 'hla_rod_top':
                        hla_label_dict_right['1'] = [smalllabellist]

            ''' Left Side check '''
            try:
                thresholdPixel_LeftSide_1 = 48
                thresholdPixel_LeftSide_2 = 45
                hla_top_L = hla_label_dict_left.get('0')
                xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]
                
                # if xminTL < 1510:
                #     logger.debug(f"Left E2 xminTL INCRESS +27")
                #     xminTL = xminTL + 27

                hla_rod_top_L = hla_label_dict_left.get('1')
                xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
                leftSide_Cord = xminRTL - xminTL
                print(f"xminTL is :{xminTL} ")
                logger.debug(f"Left E2, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} and thresholdPixel_LeftSide_2 {thresholdPixel_LeftSide_2}")

                ##if  leftSide_Cord > 61 and leftSide_Cord < 79:
                if  xmaxTL < (xmaxRTL - thresholdPixel_LeftSide_1) or xmaxTL > (xmaxRTL + thresholdPixel_LeftSide_2):  #xmin 1528
                    logger.debug(f"HLA_POSTION_LEFT = NOT OK")
                    HLA_POSTION_LEFT = "NOT OK"
                    color = (0, 0, 255)
                    #if smalllabellist[0] == 'hla_top':
                    xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
                    cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
                    label_text = ""#f"{smalllabellist[0]}.2f"
                    cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
                
                else:
                    HLA_POSTION_LEFT = "OK"
                    logger.debug(f"HLA_POSTION_LEFT = OK")
            except Exception as e:
                logger.debug(f"except Exception E2 Left Side check {e}")
                print("except Exception E2 left Left check :",e)   

            ''' Right Side check '''
            try:
                thresholdPixel = 50
                thresholdPixel_RightSide_1 = 95
                thresholdPixel_RightSide_2 = 40
                hla_top_L = hla_label_dict_right.get('0')
                xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]
                hla_rod_top_L = hla_label_dict_right.get('1')
                xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]

                if xmaxTL > 1190:
                    logger.debug(f"if xmaxTL grater 1190 {xmaxTL}dincrese thresholdPixel_RightSide_2 = 5")
                    thresholdPixel_RightSide_2= 4

                logger.debug(f"Right E2, xminTL :{xminTL} AND xminRTL : {xminRTL} thresholdPixel_RightSide_1 {thresholdPixel_RightSide_1} and thresholdPixel_RightSide_2 {thresholdPixel_RightSide_2}")
                if  xminTL < (xminRTL - thresholdPixel_RightSide_1) or xminTL > (xminRTL + thresholdPixel_RightSide_2):
                    HLA_POSTION_RIGHT = "NOT OK"
                    color = (0, 0, 255)
                    #if smalllabellist[0] == 'hla_top':
                    xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
                    logger.debug(f"HLA_POSTION_RIGHT = NOT OK")

                    cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
                    label_text = ""#f"{smalllabellist[0]}.2f"
                    cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
                else:
                    HLA_POSTION_RIGHT = "OK"
                    logger.debug(f"HLA_POSTION_RIGHT = OK") 
            except Exception as e:
                logger.debug(f"except Exception E2 Right Side check {e}")
                print("except Exception E2 Right Right check :",e)   
        #======================================= E3
        if Position ==4:                                        #E3
            hla_label_dict_left = {}
            hla_label_dict_right = {}
            for smalllabellist in OBJECT_LIST:
                xmin, ymin, xmax, ymax = smalllabellist[1:5]
                print(smalllabellist[0])
                if smalllabellist[1]  > 990:
                    if smalllabellist[0] == 'hla_top':
                        hla_label_dict_left['0'] = [smalllabellist]
                    elif smalllabellist[0] == 'hla_rod_top':
                        hla_label_dict_left['1'] = [smalllabellist]
                else:
                    if smalllabellist[0] == 'hla_top':
                        hla_label_dict_right['0'] = [smalllabellist]
                    elif smalllabellist[0] == 'hla_rod_top':
                        hla_label_dict_right['1'] = [smalllabellist]

            ''' Left Side check '''
            try:
                thresholdPixel = 50
                thresholdPixel_LeftSide_1 = 73
                thresholdPixel_LeftSide_2 = 63#70
                hla_top_L = hla_label_dict_left.get('0')
                xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

                hla_rod_top_L = hla_label_dict_left.get('1')
                xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
                logger.debug(f"Left E3, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} xminTL IS {xminTL} thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} and thresholdPixel_LeftSide_2 {thresholdPixel_LeftSide_2}")
                
                if xminTL < 1120:
                    logger.debug(f"if xminTL less 1120 {xminTL}dincrese thresholdPixel_LeftSide_1 = 7")
                    #thresholdPixel_LeftSide_2 = 7
                    thresholdPixel_LeftSide_1 = 7

                if  xmaxTL < (xmaxRTL - thresholdPixel_LeftSide_1) or xmaxTL > (xmaxRTL + thresholdPixel_LeftSide_2): #xmaxTL ok 1413 #xmaxRTL ok-1364
                    HLA_POSTION_LEFT = "NOT OK"
                    color = (0, 0, 255)
                    #if smalllabellist[0] == 'hla_top':
                    xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
                    logger.debug(f"HLA_POSTION_LEFT = NOT OK") 
                    cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
                    label_text = ""#f"{smalllabellist[0]}.2f"
                    cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
                else:
                    HLA_POSTION_LEFT = "OK"
                    logger.debug(f"HLA_POSTION_LEFT = OK") 

            except Exception as e:
                logger.debug(f"except Exception E3 Left Side check {e}")
                print("except Exception E3 Left check :",e)           

            ''' Right Side check '''
            try:
                thresholdPixel = 50
                thresholdPixel_RightSide_1 = 65#73
                thresholdPixel_RightSide_2 = 48#85
                hla_top_L = hla_label_dict_right.get('0')
                xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]
                hla_rod_top_L = hla_label_dict_right.get('1')
                xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
            
                logger.debug(f"Right E3, xminTL :{xminTL} AND xminRTL : {xminRTL} thresholdPixel_RightSide_1 {thresholdPixel_RightSide_1} and thresholdPixel_RightSide_2 {thresholdPixel_RightSide_2}")
                if xminTL < 662:
                    logger.debug(f"thresholdPixel_RightSide_1,if xminTL less 662 {xminTL}dincrese thresholdPixel_RightSide_1 = 20")
                    thresholdPixel_RightSide_1 = 20
                if  xminTL < (xminRTL - thresholdPixel_RightSide_1) or xminTL > (xminRTL + thresholdPixel_RightSide_2):#xminTL ok 607 #xminRTL ok 583
                    HLA_POSTION_RIGHT = "NOT OK"
                    logger.debug(f"HLA_POSTION_RIGHT = NOT OK") 
                    color = (0, 0, 255)
                    #if smalllabellist[0] == 'hla_top':
                    xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
                    cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
                    label_text = ""#f"{smalllabellist[0]}.2f"
                    cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)           
                else:
                    HLA_POSTION_RIGHT = "OK"
                    logger.debug(f"HLA_POSTION_RIGHT = OK") 
            except Exception as e:
                logger.debug(f"except Exception E3 right Side check {e}")
                print("except Exception thresholdPixel_RightSide_1thresholdPixel_RightSide_1 :",e)   
        #======================================= E4
        elif Position ==5:                              #E4
            hla_label_dict_left = {}
            hla_label_dict_right = {}
            for smalllabellist in OBJECT_LIST:
                xmin, ymin, xmax, ymax = smalllabellist[1:5]
                print(smalllabellist[0])
                if smalllabellist[1]  > 1180:
                    if smalllabellist[0] == 'hla_top':
                        hla_label_dict_left['0'] = [smalllabellist]
                    elif smalllabellist[0] == 'hla_rod_top':
                        hla_label_dict_left['1'] = [smalllabellist]
                else:
                    if smalllabellist[0] == 'hla_top':
                        hla_label_dict_right['0'] = [smalllabellist]
                    elif smalllabellist[0] == 'hla_rod_top':
                        hla_label_dict_right['1'] = [smalllabellist]

            ''' Left Side check '''
            try:
                thresholdPixel = 50
                thresholdPixel_LeftSide_1 = 45
                thresholdPixel_LeftSide_2 = 50
                hla_top_L = hla_label_dict_left.get('0')
                xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]
                hla_rod_top_L = hla_label_dict_left.get('1')
                xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
                logger.debug(f"Left E4, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} and xminTL :{xminTL} thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} and thresholdPixel_LeftSide_2 {thresholdPixel_LeftSide_2}")
                
                if xminTL < 1255:
                    thresholdPixel_LeftSide_1 = 5
                    logger.debug(f"Left E4, xminTL :{xminTL} if xminTL less than 1255 that's why thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} ")

                if  xmaxTL < (xmaxRTL - thresholdPixel_LeftSide_1) or xmaxTL > (xmaxRTL + thresholdPixel_LeftSide_2): #xmaxTL ok 1543 #xmaxRTL ok 1516
                    logger.debug(f"HLA_POSTION_LEFT = NOT OK")
                    HLA_POSTION_LEFT = "NOT OK"
                    color = (0, 0, 255)
                    #if smalllabellist[0] == 'hla_top':
                    xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
                    cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
                    label_text = ""#f"{smalllabellist[0]}.2f"
                    cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
                    logger.debug(f"HLA_POSTION_LEFT =NOT OK") 
                else:
                    HLA_POSTION_LEFT = "OK"
                    logger.debug(f"HLA_POSTION_LEFT = OK")
            except Exception as e:
                logger.debug(f"except Exception E4 left Side check {e}")
                print("except Exception E4 left check :",e)   

            ''' Right Side check '''
            try:
                thresholdPixel = 50
                thresholdPixel_RightSide_1 = 70
                thresholdPixel_RightSide_2 = 30#65
                hla_top_L = hla_label_dict_right.get('0')
                xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]
                hla_rod_top_L = hla_label_dict_right.get('1')
                xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
            
                logger.debug(f"Right E4, xminTL :{xminTL} AND xminRTL : {xminRTL} thresholdPixel_RightSide_1 {thresholdPixel_RightSide_1} and thresholdPixel_RightSide_2 {thresholdPixel_RightSide_2}")
                if  xminTL < (xminRTL - thresholdPixel_RightSide_1) or xminTL > (xminRTL + thresholdPixel_RightSide_2): #xminTL ok -718 #xminRTL ok 738
                    HLA_POSTION_RIGHT = "NOT OK"
                    logger.debug(f"HLA_POSTION_RIGHT =NOT OK") 
                    color = (0, 0, 255)
                    #if smalllabellist[0] == 'hla_top':
                    xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
                    cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
                    label_text = ""#f"{smalllabellist[0]}.2f"
                    cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)

                else:
                    HLA_POSTION_RIGHT = "OK"
                    logger.debug(f"HLA_POSTION_RIGHT =OK") 
                
            except Exception as e:
                logger.debug(f"except Exception E4 right Side check {e}")
                print("except Exception E4 right check :",e)  
                
        
        #======================================= I4
        if Position ==7:                                        #I4
            hla_label_dict_left = {}
            hla_label_dict_right = {}
            for smalllabellist in OBJECT_LIST:
                xmin, ymin, xmax, ymax = smalllabellist[1:5]
                print(smalllabellist[0])
                if smalllabellist[1]  > 1340:
                    if smalllabellist[0] == 'hla_top':
                        hla_label_dict_left['0'] = [smalllabellist]
                    elif smalllabellist[0] == 'hla_rod_top':
                        hla_label_dict_left['1'] = [smalllabellist]
                else:
                    if smalllabellist[0] == 'hla_top':
                        hla_label_dict_right['0'] = [smalllabellist]
                    elif smalllabellist[0] == 'hla_rod_top':
                        hla_label_dict_right['1'] = [smalllabellist]

            ''' Left Side check '''
            try:
                thresholdPixel = 50
                thresholdPixel_LeftSide_1 = 45
                thresholdPixel_LeftSide_2 = 50
                hla_top_L = hla_label_dict_left.get('0')
                xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

                hla_rod_top_L = hla_label_dict_left.get('1')
                xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
                logger.debug(f"Left I4, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} and thresholdPixel_LeftSide_2 {thresholdPixel_LeftSide_2}")
                if  xmaxTL < (xmaxRTL - thresholdPixel_LeftSide_1) or xmaxTL > (xmaxRTL + thresholdPixel_LeftSide_2): #xmaxTL ok -1758 ,xmaxRTL -1748
                    HLA_POSTION_LEFT = "NOT OK"
                    color = (0, 0, 255)
                    #if smalllabellist[0] == 'hla_top':
                    xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
                    logger.debug(f"HLA_POSTION_LEFT =NOT OK") 
                    cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
                    label_text = ""#f"{smalllabellist[0]}.2f"
                    cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
                else:
                    HLA_POSTION_LEFT = "OK"
                    logger.debug(f"HLA_POSTION_LEFT =OK")
            
            except Exception as e:
                logger.debug(f"except Exception I4 left Side check {e}")
                print("except Exception I4 left check :",e)  

            ''' Right Side check '''
            try:
                thresholdPixel = 50
                thresholdPixel_RightSide_1 = 80
                thresholdPixel_RightSide_2 = 87
                hla_top_L = hla_label_dict_right.get('0')
                xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

                hla_rod_top_L = hla_label_dict_right.get('1')
                xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
                logger.debug(f"Right I4, xminTL :{xminTL} AND xminRTL : {xminRTL} thresholdPixel_RightSide_1 {thresholdPixel_RightSide_1} and thresholdPixel_RightSide_2 {thresholdPixel_RightSide_2}")
                if  xminTL < (xminRTL - thresholdPixel_RightSide_1) or xminTL > (xminRTL + thresholdPixel_RightSide_2):#xminTL ok -869 and xminRTL ok 864
                    HLA_POSTION_RIGHT = "NOT OK"
                    color = (0, 0, 255)
                    #if smalllabellist[0] == 'hla_top':
                    xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
                    logger.debug(f"HLA_POSTION_RIGHT =NOT OK")
                    cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
                    label_text = ""#f"{smalllabellist[0]}.2f"
                    cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
                    
                else:
                    HLA_POSTION_RIGHT = "OK"
                    logger.debug(f"HLA_POSTION_RIGHT = OK")
            except Exception as e:
                logger.debug(f"except Exception I4 right Side check {e}")
                print("except Exception I4 right check :",e)  
        #======================================= I3
        if Position ==6:  #I3
            hla_label_dict_left = {}
            hla_label_dict_right = {}
            for smalllabellist in OBJECT_LIST:
                xmin, ymin, xmax, ymax = smalllabellist[1:5]
                print(smalllabellist[0])
                if smalllabellist[1]  > 1150:
                    if smalllabellist[0] == 'hla_top':
                        hla_label_dict_left['0'] = [smalllabellist]
                    elif smalllabellist[0] == 'hla_rod_top':
                        hla_label_dict_left['1'] = [smalllabellist]
                else:
                    if smalllabellist[0] == 'hla_top':
                        hla_label_dict_right['0'] = [smalllabellist]
                    elif smalllabellist[0] == 'hla_rod_top':
                        hla_label_dict_right['1'] = [smalllabellist]

            ''' Left Side check '''
            try:
                thresholdPixel = 50
                thresholdPixel_LeftSide_1 = 52#69
                thresholdPixel_LeftSide_2 = 50
                hla_top_L = hla_label_dict_left.get('0')
                xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

                hla_rod_top_L = hla_label_dict_left.get('1')
                xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
                logger.debug(f"Left I3, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} and thresholdPixel_LeftSide_2 {thresholdPixel_LeftSide_2}")
                if  xmaxTL < (xmaxRTL - thresholdPixel_LeftSide_1) or xmaxTL > (xmaxRTL + thresholdPixel_LeftSide_2): #xmaxTL ok 1623, xmaxRTL ok -1604
                    HLA_POSTION_LEFT = "NOT OK"
                    color = (0, 0, 255)
                    #if smalllabellist[0] == 'hla_top':
                    xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
                    cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
                    label_text = ""#f"{smalllabellist[0]}.2f"
                    cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
                    logger.debug(f"HLA_POSTION_LEFT = NOT OK")
                else:
                    HLA_POSTION_LEFT = "OK"
                    logger.debug(f"HLA_POSTION_LEFT = OK")
            except Exception as e:
                logger.debug(f"except Exception I3 left Side check {e}")
                print("except Exception I3 left check :",e)  

            ''' Right Side check '''
            try:
                thresholdPixel = 50
                thresholdPixel_RightSide_1 = 80
                thresholdPixel_RightSide_2 = 91#85#79
                hla_top_L = hla_label_dict_right.get('0')
                xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]
                hla_rod_top_L = hla_label_dict_right.get('1')
                xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
                logger.debug(f"Right I3, xminTL :{xminTL} AND xminRTL : {xminRTL} thresholdPixel_RightSide_1 {thresholdPixel_RightSide_1} and thresholdPixel_RightSide_2 {thresholdPixel_RightSide_2}")
                if  xminTL < (xminRTL - thresholdPixel_RightSide_1) or xminTL > (xminRTL + thresholdPixel_RightSide_2):
                    HLA_POSTION_RIGHT = "NOT OK"
                    logger.debug(f"HLA_POSTION_RIGHT = NOT OK")
                    color = (0, 0, 255)
                    #if smalllabellist[0] == 'hla_top':
                    xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
                    cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
                    label_text = ""#f"{smalllabellist[0]}.2f"
                    cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
                    
                else:
                    logger.debug(f"HLA_POSTION_RIGHT = OK")
                    HLA_POSTION_RIGHT = "OK"
            except Exception as e:
                logger.debug(f"except Exception I3 right Side check {e}")
                print("except Exception I3 right check :",e)
        #======================================= I2
        if Position ==9:   #I2
            hla_label_dict_left = {}
            hla_label_dict_right = {}
            for smalllabellist in OBJECT_LIST:
                xmin, ymin, xmax, ymax = smalllabellist[1:5]
                print(smalllabellist[0])
                if smalllabellist[1]  > 1410:
                    if smalllabellist[0] == 'hla_top':
                        hla_label_dict_left['0'] = [smalllabellist]
                    elif smalllabellist[0] == 'hla_rod_top':
                        hla_label_dict_left['1'] = [smalllabellist]
                else:
                    if smalllabellist[0] == 'hla_top':
                        hla_label_dict_right['0'] = [smalllabellist]
                    elif smalllabellist[0] == 'hla_rod_top':
                        hla_label_dict_right['1'] = [smalllabellist]

            ''' Left Side check '''
            try:
                thresholdPixel = 50
                thresholdPixel_LeftSide_1 = 50
                thresholdPixel_LeftSide_2 = 50
                hla_top_L = hla_label_dict_left.get('0')
                xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

                hla_rod_top_L = hla_label_dict_left.get('1')
                xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
                logger.debug(f"Left I2, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} and thresholdPixel_LeftSide_2 {thresholdPixel_LeftSide_2}")
                if  xmaxTL < (xmaxRTL - thresholdPixel_LeftSide_1) or xmaxTL > (xmaxRTL + thresholdPixel_LeftSide_2):
                    HLA_POSTION_LEFT = "NOT OK"
                    color = (0, 0, 255)
                    #if smalllabellist[0] == 'hla_top':
                    xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
                    logger.debug(f"HLA_POSTION_LEFT = NOT OK")
                    cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
                    label_text = ""#f"{smalllabellist[0]}.2f"
                    cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
                else:
                    logger.debug(f"HLA_POSTION_LEFT = OK")
                    HLA_POSTION_LEFT = "OK"
            except Exception as e:
                logger.debug(f"except Exception I2 left Side check {e}")
                print("except Exception I2 left check :",e)

            ''' Right Side check '''
            try:
                thresholdPixel = 50
                thresholdPixel_RightSide_1 = 80
                thresholdPixel_RightSide_2 = 60
                hla_top_L = hla_label_dict_right.get('0')
                xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

                hla_rod_top_L = hla_label_dict_right.get('1')
                xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
                logger.debug(f"Right I2, xminTL :{xminTL} AND xminRTL : {xminRTL} thresholdPixel_RightSide_1 {thresholdPixel_RightSide_1} and thresholdPixel_RightSide_2 {thresholdPixel_RightSide_2}")
                if  xminTL < (xminRTL - thresholdPixel_RightSide_1) or xminTL > (xminRTL + thresholdPixel_RightSide_2):
                    HLA_POSTION_RIGHT = "NOT OK"
                    color = (0, 0, 255)
                    #if smalllabellist[0] == 'hla_top':
                    xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
                    cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
                    label_text = ""#f"{smalllabellist[0]}.2f"
                    cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)         
                    logger.debug(f"HLA_POSTION_RIGHT =NOT OK")    
                else:
                    HLA_POSTION_RIGHT = "OK"
                    logger.debug(f"HLA_POSTION_RIGHT = OK")  
            except Exception as e:
                logger.debug(f"except Exception I2 right Side check {e}")
                print("except Exception I2 right check :",e)
        #======================================= I1
        if Position ==8:  #I1
            hla_label_dict_left = {}
            hla_label_dict_right = {}
            for smalllabellist in OBJECT_LIST:
                xmin, ymin, xmax, ymax = smalllabellist[1:5]
                print(smalllabellist[0])
                if smalllabellist[1]  > 1215:
                    if smalllabellist[0] == 'hla_top':
                        hla_label_dict_left['0'] = [smalllabellist]
                    elif smalllabellist[0] == 'hla_rod_top':
                        hla_label_dict_left['1'] = [smalllabellist]
                else:
                    if smalllabellist[0] == 'hla_top':
                        hla_label_dict_right['0'] = [smalllabellist]
                    elif smalllabellist[0] == 'hla_rod_top':
                        hla_label_dict_right['1'] = [smalllabellist]

            ''' Left Side check '''
            try:
                thresholdPixel = 50
                thresholdPixel_LeftSide_1 = 52#69
                thresholdPixel_LeftSide_2 = 50
                hla_top_L = hla_label_dict_left.get('0')
                xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

                hla_rod_top_L = hla_label_dict_left.get('1')
                xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
                logger.debug(f"Left I1, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} and thresholdPixel_LeftSide_2 {thresholdPixel_LeftSide_2}")
                if  xmaxTL < (xmaxRTL - thresholdPixel_LeftSide_1) or xmaxTL > (xmaxRTL + thresholdPixel_LeftSide_2):
                    HLA_POSTION_LEFT = "NOT OK"
                    color = (0, 0, 255)
                    #if smalllabellist[0] == 'hla_top':
                    xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
                    logger.debug(f"HLA_POSTION_LEFT = NOT OK") 
                    cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
                    label_text = ""#f"{smalllabellist[0]}.2f"
                    cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
                else:
                    HLA_POSTION_LEFT = "OK"
                    logger.debug(f"HLA_POSTION_LEFT = OK") 
            except Exception as e:
                logger.debug(f"except Exception I1 left Side check {e}")
                print("except Exception I1 left check :",e)

            ''' Right Side check '''
            try:
                thresholdPixel = 50
                thresholdPixel_RightSide_1 = 80
                thresholdPixel_RightSide_2 = 89
                hla_top_L = hla_label_dict_right.get('0')
                xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

                hla_rod_top_L = hla_label_dict_right.get('1')
                xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
                logger.debug(f"Right I1, xminTL :{xminTL} AND xminRTL : {xminRTL} thresholdPixel_RightSide_1 {thresholdPixel_RightSide_1} and thresholdPixel_RightSide_2 {thresholdPixel_RightSide_2}")
                if  xminTL < (xminRTL - thresholdPixel_RightSide_1) or xminTL > (xminRTL + thresholdPixel_RightSide_2):
                    HLA_POSTION_RIGHT = "NOT OK"
                    logger.debug(f"HLA_POSTION_RIGHT = NOT OK") 
                    color = (0, 0, 255)
                    #if smalllabellist[0] == 'hla_top':
                    xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
                    cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
                    label_text = ""#f"{smalllabellist[0]}.2f"
                    cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
                    
                else:
                    HLA_POSTION_RIGHT = "OK"
                    logger.debug(f"HLA_POSTION_RIGHT = OK")
            except Exception as e:
                logger.debug(f"except Exception I1 right Side check {e}")
                print("except Exception I1 right check :",e)
        #=======================================    status
        if HLA_POSTION_LEFT == "OK" and HLA_POSTION_RIGHT == "OK":
            HLA_POSTION = "OK"
             
        else:
            HLA_POSTION ="NOT OK"

        
    except Exception as e:
        logger.debug(f"except Exception HLA_PostionCheck_with_nut {e}")
        print("HLA_classCheck is :",e)
    return HLA_POSTION, original_image


# def HLA_PostionCheck_with_nut(Position,OBJECT_LIST,original_image):
#     isHLA_PositionCorrect = False
#     center_of_hla = []
#     center_of_nut = []
#     # HLA_POSTION_RIGHT = "NOT OK"
#     # HLA_POSTION_LEFT = "NOT OK"
#     # HLA_POSTION ="NOT OK"

#     HLA_POSTION_RIGHT = "OK"
#     HLA_POSTION_LEFT = "OK"
#     HLA_POSTION ="OK"
#     center_of_hla = False
#     center_of_nut = False
#     center_of_hla_top=0
#     try: 
#         #======================================= E1 
#         if Position ==2:           #E1
#             leftSide_Cord = 0
#             RightSide_Cord=0
#             hla_label_dict_left = {}
#             hla_label_dict_right = {}
#             for smalllabellist in OBJECT_LIST:
#                 xmin, ymin, xmax, ymax = smalllabellist[1:5]
#                 print(smalllabellist[0])

#                 if smalllabellist[1]  > 1240:
#                     if smalllabellist[0] == 'hla_top':
#                         hla_label_dict_left['0'] = [smalllabellist]
#                     elif smalllabellist[0] == 'hla_rod_top':
#                         hla_label_dict_left['1'] = [smalllabellist]
#                 else:
#                     if smalllabellist[0] == 'hla_top':
#                         hla_label_dict_right['0'] = [smalllabellist]
#                     elif smalllabellist[0] == 'hla_rod_top':
#                         hla_label_dict_right['1'] = [smalllabellist]

#             ''' Left Side check '''
#             thresholdPixel_RightSide_1 = 67#70 #72  #90
#             thresholdPixel_RightSide_2 = 45
#             hla_top_L = hla_label_dict_left.get('0')
#             xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

#             hla_rod_top_L = hla_label_dict_left.get('1')
#             xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]

#             leftSide_Cord = xminRTL - xminTL
#             print(f"leftSide_Cord is :{leftSide_Cord} ")
#             logger.debug(f"Left E1, xminTL :{xminTL} AND xminRTL : {xminRTL} thresholdPixel_RightSide_1 {thresholdPixel_RightSide_1} and thresholdPixel_RightSide_2 {thresholdPixel_RightSide_2}")
#             if xminTL > 1400:
#                 logger.debug(f"DERC thresholdPixel_RightSide_2 = 5")
#                 thresholdPixel_RightSide_2= 4
#             if  xminTL < (xminRTL - thresholdPixel_RightSide_1) or xminTL > (xminRTL + thresholdPixel_RightSide_2):
#                 logger.debug(f"HLA_POSTION_RIGHT = NOT OK")
#                 HLA_POSTION_LEFT = "NOT OK"
#                 color = (0, 0, 255)
#                 #if smalllabellist[0] == 'hla_top':
#                 xmin, ymin, xmax, ymax = hla_top_L[0][1:5]

#                 cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
#                 label_text = ""#f"{smalllabellist[0]}.2f"
#                 cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7) 
#             else:
#                 HLA_POSTION_LEFT = "OK"
#                 logger.debug(f"HLA_POSTION_RIGHT = OK")


#             ''' Right Side check '''
#             thresholdPixel_LeftSide_1 = 29 #65
#             thresholdPixel_LeftSide_2 = 72 #67#45
#             hla_top_L = hla_label_dict_right.get('0')
#             xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

#             hla_rod_top_L = hla_label_dict_right.get('1')
#             xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]

#             RightSide_Cord = xminRTL - xminTL
#             print(f"RightSide_Cord is :{RightSide_Cord} ")
#             logger.debug(f"E1, Position ==2 RightSide_Cord {RightSide_Cord}")

#             logger.debug(f"Right E1, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} and thresholdPixel_LeftSide_2 {thresholdPixel_LeftSide_2}")
#             #if  RightSide_Cord > 30 and RightSide_Cord < 45:
#             if  xmaxTL < (xmaxRTL - thresholdPixel_LeftSide_1) or xmaxTL > (xmaxRTL + thresholdPixel_LeftSide_2):
#                 HLA_POSTION_RIGHT = "NOT OK"
#                 logger.debug(f"HLA_POSTION_RIGHT = NOT OK")
#                 color = (0, 0, 255)
#                 #if smalllabellist[0] == 'hla_top':
#                 xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
#                 cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
#                 label_text = ""#f"{smalllabellist[0]}.2f"
#                 cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)

#             else:
#                 HLA_POSTION_RIGHT = "OK"
#                 logger.debug(f"HLA_POSTION_RIGHT = OK")
        
#         #======================================= E2
#         elif Position ==3:                                                 #E2
#             hla_label_dict_left = {}
#             hla_label_dict_right = {}
#             leftSide_Cord = 0
#             RightSide_Cord=0
            
#             for smalllabellist in OBJECT_LIST:
#                 xmin, ymin, xmax, ymax = smalllabellist[1:5]
#                 print(smalllabellist[0])
#                 if smalllabellist[1]  > 1350:
#                     if smalllabellist[0] == 'hla_top':
#                         hla_label_dict_left['0'] = [smalllabellist]
#                     elif smalllabellist[0] == 'hla_rod_top':
#                         hla_label_dict_left['1'] = [smalllabellist]
#                 else:
#                     if smalllabellist[0] == 'hla_top':
#                         hla_label_dict_right['0'] = [smalllabellist]
#                     elif smalllabellist[0] == 'hla_rod_top':
#                         hla_label_dict_right['1'] = [smalllabellist]

#             ''' Left Side check '''
#             thresholdPixel_LeftSide_1 = 77#80#100
#             thresholdPixel_LeftSide_2 = 45
#             hla_top_L = hla_label_dict_left.get('0')
#             xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]
            
#             if xminTL < 1510:
#                 logger.debug(f"Left E2 xminTL INCRESS +27")
#                 xminTL = xminTL + 27

#             hla_rod_top_L = hla_label_dict_left.get('1')
#             xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
#             leftSide_Cord = xminRTL - xminTL
#             print(f"xminTL is :{xminTL} ")
#             logger.debug(f"Left E2, xminTL :{xminTL} AND xminRTL : {xminRTL} thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} and thresholdPixel_LeftSide_2 {thresholdPixel_LeftSide_2}")

#             ##if  leftSide_Cord > 61 and leftSide_Cord < 79:
#             if  xminTL < (xminRTL - thresholdPixel_LeftSide_1) or xminTL > (xminRTL + thresholdPixel_LeftSide_2):  #xmin 1528
#                 logger.debug(f"HLA_POSTION_LEFT = NOT OK")
#                 HLA_POSTION_LEFT = "NOT OK"
#                 color = (0, 0, 255)
#                 #if smalllabellist[0] == 'hla_top':
#                 xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
#                 cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
#                 label_text = ""#f"{smalllabellist[0]}.2f"
#                 cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
               
#             else:
#                 HLA_POSTION_LEFT = "OK"
#                 logger.debug(f"HLA_POSTION_LEFT = OK")
               

#             ''' Right Side check '''
#             thresholdPixel = 50
#             thresholdPixel_RightSide_1 = 100
#             thresholdPixel_RightSide_2 = 60#50#45
#             hla_top_L = hla_label_dict_right.get('0')
#             xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]
#             hla_rod_top_L = hla_label_dict_right.get('1')
#             xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
#             RightSide_Cord = xminRTL - xminTL
#             print(f"RightSide_Cord is :{RightSide_Cord} ")
#             #if  RightSide_Cord > 22 and RightSide_Cord < 38:
#             logger.debug(f"Right E2, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} thresholdPixel_RightSide_1 {thresholdPixel_RightSide_1} and thresholdPixel_RightSide_2 {thresholdPixel_RightSide_2}")
#             if  xmaxTL < (xmaxRTL - thresholdPixel_RightSide_1) or xmaxTL > (xmaxRTL + thresholdPixel_RightSide_2):
#                 HLA_POSTION_RIGHT = "NOT OK"
#                 color = (0, 0, 255)
#                 #if smalllabellist[0] == 'hla_top':
#                 xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
#                 logger.debug(f"HLA_POSTION_RIGHT = NOT OK")

#                 cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
#                 label_text = ""#f"{smalllabellist[0]}.2f"
#                 cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
#             else:
#                 HLA_POSTION_RIGHT = "OK"
#                 logger.debug(f"HLA_POSTION_RIGHT = OK") 
        
#         #======================================= E3
#         if Position ==4:                                        #E3
#             hla_label_dict_left = {}
#             hla_label_dict_right = {}
#             for smalllabellist in OBJECT_LIST:
#                 xmin, ymin, xmax, ymax = smalllabellist[1:5]
#                 print(smalllabellist[0])
#                 if smalllabellist[1]  > 990:
#                     if smalllabellist[0] == 'hla_top':
#                         hla_label_dict_left['0'] = [smalllabellist]
#                     elif smalllabellist[0] == 'hla_rod_top':
#                         hla_label_dict_left['1'] = [smalllabellist]
#                 else:
#                     if smalllabellist[0] == 'hla_top':
#                         hla_label_dict_right['0'] = [smalllabellist]
#                     elif smalllabellist[0] == 'hla_rod_top':
#                         hla_label_dict_right['1'] = [smalllabellist]

#             ''' Left Side check '''
#             thresholdPixel = 50
#             thresholdPixel_LeftSide_1 = 73
#             thresholdPixel_LeftSide_2 = 70
#             hla_top_L = hla_label_dict_left.get('0')
#             xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

#             hla_rod_top_L = hla_label_dict_left.get('1')
#             xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
#             logger.debug(f"Left E3, xminTL :{xminTL} AND xminRTL : {xminRTL} thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} and thresholdPixel_LeftSide_2 {thresholdPixel_LeftSide_2}")
#             if  xminTL < (xminRTL - thresholdPixel_LeftSide_1) or xminTL > (xminRTL + thresholdPixel_LeftSide_2): #xminTL ok 1136
#                 HLA_POSTION_LEFT = "NOT OK"
#                 color = (0, 0, 255)
#                 #if smalllabellist[0] == 'hla_top':
#                 xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
#                 logger.debug(f"HLA_POSTION_LEFT = NOT OK") 

#                 cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
#                 label_text = ""#f"{smalllabellist[0]}.2f"
#                 cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
#             else:
#                 HLA_POSTION_LEFT = "OK"
#                 logger.debug(f"HLA_POSTION_LEFT = OK") 

#             ''' Right Side check '''
#             thresholdPixel = 50
#             thresholdPixel_RightSide_1 = 73
#             thresholdPixel_RightSide_2 = 85#72
#             hla_top_L = hla_label_dict_right.get('0')
#             xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]
#             hla_rod_top_L = hla_label_dict_right.get('1')
#             xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
#             if xmaxTL < 800:
#                 thresholdPixel_RightSide_2  = 10
#             logger.debug(f"Right E3, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} thresholdPixel_RightSide_1 {thresholdPixel_RightSide_1} and thresholdPixel_RightSide_2 {thresholdPixel_RightSide_2}")
#             if  xmaxTL < (xmaxRTL - thresholdPixel_RightSide_1) or xmaxTL > (xmaxRTL + thresholdPixel_RightSide_2):#xmaxRTL 815
#                 HLA_POSTION_RIGHT = "NOT OK"
#                 logger.debug(f"HLA_POSTION_RIGHT = NOT OK") 
#                 color = (0, 0, 255)
#                 #if smalllabellist[0] == 'hla_top':
#                 xmin, ymin, xmax, ymax = hla_top_L[0][1:5]

#                 cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
#                 label_text = ""#f"{smalllabellist[0]}.2f"
#                 cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)           
#             else:
#                 HLA_POSTION_RIGHT = "OK"
#                 logger.debug(f"HLA_POSTION_RIGHT = OK") 
        
#         #======================================= E4
#         elif Position ==5:                              #E4
#             hla_label_dict_left = {}
#             hla_label_dict_right = {}
#             for smalllabellist in OBJECT_LIST:
#                 xmin, ymin, xmax, ymax = smalllabellist[1:5]
#                 print(smalllabellist[0])
#                 if smalllabellist[1]  > 1180:
#                     if smalllabellist[0] == 'hla_top':
#                         hla_label_dict_left['0'] = [smalllabellist]
#                     elif smalllabellist[0] == 'hla_rod_top':
#                         hla_label_dict_left['1'] = [smalllabellist]
#                 else:
#                     if smalllabellist[0] == 'hla_top':
#                         hla_label_dict_right['0'] = [smalllabellist]
#                     elif smalllabellist[0] == 'hla_rod_top':
#                         hla_label_dict_right['1'] = [smalllabellist]

#             ''' Left Side check '''
#             thresholdPixel = 50
#             thresholdPixel_LeftSide_1 = 55#69
#             thresholdPixel_LeftSide_2 = 50
#             hla_top_L = hla_label_dict_left.get('0')
#             xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]
#             hla_rod_top_L = hla_label_dict_left.get('1')
#             xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
#             logger.debug(f"Left E4, xminTL :{xminTL} AND xminRTL : {xminRTL} thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} and thresholdPixel_LeftSide_2 {thresholdPixel_LeftSide_2}")

#             if xminTL > 1270:
#                 logger.debug(f"xminTL DINCRESS -50")
#                 xminTL = xminTL - 50

#             if  xminTL < (xminRTL - thresholdPixel_LeftSide_1) or xminTL > (xminRTL + thresholdPixel_LeftSide_2): #xminTL ok 1268
#                 HLA_POSTION_LEFT = "NOT OK"
#                 color = (0, 0, 255)
#                 #if smalllabellist[0] == 'hla_top':
#                 xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
#                 #cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
#                 label_text = ""#f"{smalllabellist[0]}.2f"
#                 cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
#                 logger.debug(f"HLA_POSTION_LEFT =NOT OK") 
#             else:
#                 HLA_POSTION_LEFT = "OK"
#                 logger.debug(f"HLA_POSTION_LEFT = OK")

#             ''' Right Side check '''
#             thresholdPixel = 50
#             thresholdPixel_RightSide_1 = 80
#             thresholdPixel_RightSide_2 = 65#56#69
#             hla_top_L = hla_label_dict_right.get('0')
#             xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]
#             hla_rod_top_L = hla_label_dict_right.get('1')
#             xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
#             if xmaxRTL < 960:
#                 logger.debug(f"xmaxRTL INCRESS +42")
#                 xmaxRTL = xmaxRTL + 42
#             logger.debug(f"Right E4, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} thresholdPixel_RightSide_1 {thresholdPixel_RightSide_1} and thresholdPixel_RightSide_2 {thresholdPixel_RightSide_2}")
#             if  xmaxTL < (xmaxRTL - thresholdPixel_RightSide_1) or xmaxTL > (xmaxRTL + thresholdPixel_RightSide_2): #xmaxTL ok 993  #xmaxRTL ok -928
#                 HLA_POSTION_RIGHT = "NOT OK"
#                 logger.debug(f"HLA_POSTION_RIGHT =NOT OK") 
#                 color = (0, 0, 255)
#                 #if smalllabellist[0] == 'hla_top':
#                 xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
#                 cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
#                 label_text = ""#f"{smalllabellist[0]}.2f"
#                 cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)

#             else:
#                 HLA_POSTION_RIGHT = "OK"
#                 logger.debug(f"HLA_POSTION_RIGHT =OK") 
                
        
#         #======================================= I4
#         if Position ==7:                                        #I4
#             hla_label_dict_left = {}
#             hla_label_dict_right = {}
#             for smalllabellist in OBJECT_LIST:
#                 xmin, ymin, xmax, ymax = smalllabellist[1:5]
#                 print(smalllabellist[0])
#                 if smalllabellist[1]  > 1340:
#                     if smalllabellist[0] == 'hla_top':
#                         hla_label_dict_left['0'] = [smalllabellist]
#                     elif smalllabellist[0] == 'hla_rod_top':
#                         hla_label_dict_left['1'] = [smalllabellist]
#                 else:
#                     if smalllabellist[0] == 'hla_top':
#                         hla_label_dict_right['0'] = [smalllabellist]
#                     elif smalllabellist[0] == 'hla_rod_top':
#                         hla_label_dict_right['1'] = [smalllabellist]

#             ''' Left Side check '''
#             thresholdPixel = 50
#             thresholdPixel_LeftSide_1 = 69
#             thresholdPixel_LeftSide_2 = 50
#             hla_top_L = hla_label_dict_left.get('0')
#             xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

#             hla_rod_top_L = hla_label_dict_left.get('1')
#             xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
#             logger.debug(f"Left I4, xminTL :{xminTL} AND xminRTL : {xminRTL} thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} and thresholdPixel_LeftSide_2 {thresholdPixel_LeftSide_2}")
#             if  xminTL < (xminRTL - thresholdPixel_LeftSide_1) or xminTL > (xminRTL + thresholdPixel_LeftSide_2): #xminTL ok -1503
#                 HLA_POSTION_LEFT = "NOT OK"
#                 color = (0, 0, 255)
#                 #if smalllabellist[0] == 'hla_top':
#                 xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
#                 logger.debug(f"HLA_POSTION_LEFT =NOT OK") 
#                 cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
#                 label_text = ""#f"{smalllabellist[0]}.2f"
#                 cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
#             else:
#                 HLA_POSTION_LEFT = "OK"
#                 logger.debug(f"HLA_POSTION_LEFT =OK")

#             ''' Right Side check '''
#             thresholdPixel = 50
#             thresholdPixel_RightSide_1 = 80
#             thresholdPixel_RightSide_2 = 87
#             hla_top_L = hla_label_dict_right.get('0')
#             xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

#             hla_rod_top_L = hla_label_dict_right.get('1')
#             xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
#             logger.debug(f"Right I4, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} thresholdPixel_RightSide_1 {thresholdPixel_RightSide_1} and thresholdPixel_RightSide_2 {thresholdPixel_RightSide_2}")
#             if  xmaxTL < (xmaxRTL - thresholdPixel_RightSide_1) or xmaxTL > (xmaxRTL + thresholdPixel_RightSide_2): #xmaxTL -1109
#                 HLA_POSTION_RIGHT = "NOT OK"
#                 color = (0, 0, 255)
#                 #if smalllabellist[0] == 'hla_top':
#                 xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
#                 logger.debug(f"HLA_POSTION_RIGHT =NOT OK")
#                 cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
#                 label_text = ""#f"{smalllabellist[0]}.2f"
#                 cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
                
#             else:
#                 HLA_POSTION_RIGHT = "OK"
#                 logger.debug(f"HLA_POSTION_RIGHT = OK")
        
#         #======================================= I3
#         if Position ==6:  #I3
#             hla_label_dict_left = {}
#             hla_label_dict_right = {}
#             for smalllabellist in OBJECT_LIST:
#                 xmin, ymin, xmax, ymax = smalllabellist[1:5]
#                 print(smalllabellist[0])
#                 if smalllabellist[1]  > 1150:
#                     if smalllabellist[0] == 'hla_top':
#                         hla_label_dict_left['0'] = [smalllabellist]
#                     elif smalllabellist[0] == 'hla_rod_top':
#                         hla_label_dict_left['1'] = [smalllabellist]
#                 else:
#                     if smalllabellist[0] == 'hla_top':
#                         hla_label_dict_right['0'] = [smalllabellist]
#                     elif smalllabellist[0] == 'hla_rod_top':
#                         hla_label_dict_right['1'] = [smalllabellist]

#             ''' Left Side check '''
#             thresholdPixel = 50
#             thresholdPixel_LeftSide_1 = 69
#             thresholdPixel_LeftSide_2 = 50
#             hla_top_L = hla_label_dict_left.get('0')
#             xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

#             hla_rod_top_L = hla_label_dict_left.get('1')
#             xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
#             logger.debug(f"Left I3, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} and thresholdPixel_LeftSide_2 {thresholdPixel_LeftSide_2}")

#             if  xminTL < (xminRTL - thresholdPixel_LeftSide_1) or xminTL > (xminRTL + thresholdPixel_LeftSide_2): #xminTL ok-1353
#                 HLA_POSTION_LEFT = "NOT OK"
#                 color = (0, 0, 255)
#                 #if smalllabellist[0] == 'hla_top':
#                 xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
#                 cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
#                 label_text = ""#f"{smalllabellist[0]}.2f"
#                 cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
#                 logger.debug(f"HLA_POSTION_LEFT = NOT OK")
#             else:
#                 HLA_POSTION_LEFT = "OK"
#                 logger.debug(f"HLA_POSTION_LEFT = OK")
                

#             ''' Right Side check '''
#             thresholdPixel = 50
#             thresholdPixel_RightSide_1 = 80
#             thresholdPixel_RightSide_2 = 91#85#79
#             hla_top_L = hla_label_dict_right.get('0')
#             xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]
#             hla_rod_top_L = hla_label_dict_right.get('1')
#             xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
#             logger.debug(f"Right I3, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} thresholdPixel_RightSide_1 {thresholdPixel_RightSide_1} and thresholdPixel_RightSide_2 {thresholdPixel_RightSide_2}")

#             if  xmaxTL < (xmaxRTL - thresholdPixel_RightSide_1) or xmaxTL > (xmaxRTL + thresholdPixel_RightSide_2):#xmaxTL ok -971, xmaxRTL ok -895
#                 HLA_POSTION_RIGHT = "NOT OK"
#                 logger.debug(f"HLA_POSTION_RIGHT = NOT OK")
#                 color = (0, 0, 255)
#                 #if smalllabellist[0] == 'hla_top':
#                 xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
#                 cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
#                 label_text = ""#f"{smalllabellist[0]}.2f"
#                 cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
                
#             else:
#                 logger.debug(f"HLA_POSTION_RIGHT = OK")
#                 HLA_POSTION_RIGHT = "OK"
#         #======================================= I2
#         if Position ==9:   #I2
#             hla_label_dict_left = {}
#             hla_label_dict_right = {}
#             for smalllabellist in OBJECT_LIST:
#                 xmin, ymin, xmax, ymax = smalllabellist[1:5]
#                 print(smalllabellist[0])
#                 if smalllabellist[1]  > 1410:
#                     if smalllabellist[0] == 'hla_top':
#                         hla_label_dict_left['0'] = [smalllabellist]
#                     elif smalllabellist[0] == 'hla_rod_top':
#                         hla_label_dict_left['1'] = [smalllabellist]
#                 else:
#                     if smalllabellist[0] == 'hla_top':
#                         hla_label_dict_right['0'] = [smalllabellist]
#                     elif smalllabellist[0] == 'hla_rod_top':
#                         hla_label_dict_right['1'] = [smalllabellist]

#             ''' Left Side check '''
#             thresholdPixel = 50
#             thresholdPixel_LeftSide_1 = 74#69
#             thresholdPixel_LeftSide_2 = 50
#             hla_top_L = hla_label_dict_left.get('0')
#             xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

#             hla_rod_top_L = hla_label_dict_left.get('1')
#             xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
#             logger.debug(f"Left I2, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} and thresholdPixel_LeftSide_2 {thresholdPixel_LeftSide_2}")
#             if  xminTL < (xminRTL - thresholdPixel_LeftSide_1) or xminTL > (xminRTL + thresholdPixel_LeftSide_2):  #xminTL -1571
#                 HLA_POSTION_LEFT = "NOT OK"
#                 color = (0, 0, 255)
#                 #if smalllabellist[0] == 'hla_top':
#                 xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
#                 logger.debug(f"HLA_POSTION_LEFT = NOT OK")
#                 cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
#                 label_text = ""#f"{smalllabellist[0]}.2f"
#                 cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
#             else:
#                 logger.debug(f"HLA_POSTION_LEFT = OK")
#                 HLA_POSTION_LEFT = "OK"

#             ''' Right Side check '''
#             thresholdPixel = 50
#             thresholdPixel_RightSide_1 = 80
#             thresholdPixel_RightSide_2 = 86
#             hla_top_L = hla_label_dict_right.get('0')
#             xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

#             hla_rod_top_L = hla_label_dict_right.get('1')
#             xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
#             logger.debug(f"Right I2, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} thresholdPixel_RightSide_1 {thresholdPixel_RightSide_1} and thresholdPixel_RightSide_2 {thresholdPixel_RightSide_2}")
#             if  xmaxTL < (xmaxRTL - thresholdPixel_RightSide_1) or xmaxTL > (xmaxRTL + thresholdPixel_RightSide_2):#xmaxTL -1181
#                 HLA_POSTION_RIGHT = "NOT OK"
#                 color = (0, 0, 255)
#                 #if smalllabellist[0] == 'hla_top':
#                 xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
#                 cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
#                 label_text = ""#f"{smalllabellist[0]}.2f"
#                 cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)         
#                 logger.debug(f"HLA_POSTION_RIGHT =NOT OK")    
#             else:
#                 HLA_POSTION_RIGHT = "OK"
#                 logger.debug(f"HLA_POSTION_RIGHT = OK")  

#         #======================================= I1
#         if Position ==8:  #I1
#             hla_label_dict_left = {}
#             hla_label_dict_right = {}
#             for smalllabellist in OBJECT_LIST:
#                 xmin, ymin, xmax, ymax = smalllabellist[1:5]
#                 print(smalllabellist[0])
#                 if smalllabellist[1]  > 1215:
#                     if smalllabellist[0] == 'hla_top':
#                         hla_label_dict_left['0'] = [smalllabellist]
#                     elif smalllabellist[0] == 'hla_rod_top':
#                         hla_label_dict_left['1'] = [smalllabellist]
#                 else:
#                     if smalllabellist[0] == 'hla_top':
#                         hla_label_dict_right['0'] = [smalllabellist]
#                     elif smalllabellist[0] == 'hla_rod_top':
#                         hla_label_dict_right['1'] = [smalllabellist]

#             ''' Left Side check '''
#             thresholdPixel = 50
#             thresholdPixel_LeftSide_1 = 69
#             thresholdPixel_LeftSide_2 = 50
#             hla_top_L = hla_label_dict_left.get('0')
#             xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

#             hla_rod_top_L = hla_label_dict_left.get('1')
#             xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
#             logger.debug(f"Left I1, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} thresholdPixel_LeftSide_1 {thresholdPixel_LeftSide_1} and thresholdPixel_LeftSide_2 {thresholdPixel_LeftSide_2}")
#             if  xminTL < (xminRTL - thresholdPixel_LeftSide_1) or xminTL > (xminRTL + thresholdPixel_LeftSide_2): #xminTL ok-1427
#                 HLA_POSTION_LEFT = "NOT OK"
#                 color = (0, 0, 255)
#                 #if smalllabellist[0] == 'hla_top':
#                 xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
#                 logger.debug(f"HLA_POSTION_LEFT = NOT OK") 
#                 cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
#                 label_text = ""#f"{smalllabellist[0]}.2f"
#                 cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
#             else:
#                 HLA_POSTION_LEFT = "OK"
#                 logger.debug(f"HLA_POSTION_LEFT = OK") 
                

#             ''' Right Side check '''
#             thresholdPixel = 50
#             thresholdPixel_RightSide_1 = 80
#             thresholdPixel_RightSide_2 = 89
#             hla_top_L = hla_label_dict_right.get('0')
#             xminTL, yminTL, xmaxTL, ymaxTL = hla_top_L[0][1:5]

#             hla_rod_top_L = hla_label_dict_right.get('1')
#             xminRTL, yminRTL, xmaxRTL, ymaxRTL = hla_rod_top_L[0][1:5]
#             logger.debug(f"Right I1, xmaxTL :{xmaxTL} AND xmaxRTL : {xmaxRTL} thresholdPixel_RightSide_1 {thresholdPixel_RightSide_1} and thresholdPixel_RightSide_2 {thresholdPixel_RightSide_2}")
#             if  xmaxTL < (xmaxRTL - thresholdPixel_RightSide_1) or xmaxTL > (xmaxRTL + thresholdPixel_RightSide_2):#xmaxTL ok -1046
#                 HLA_POSTION_RIGHT = "NOT OK"
#                 logger.debug(f"HLA_POSTION_RIGHT = NOT OK") 
#                 color = (0, 0, 255)
#                 #if smalllabellist[0] == 'hla_top':
#                 xmin, ymin, xmax, ymax = hla_top_L[0][1:5]
#                 cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 12)
#                 label_text = ""#f"{smalllabellist[0]}.2f"
#                 cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 7)
                
#             else:
#                 HLA_POSTION_RIGHT = "OK"
#                 logger.debug(f"HLA_POSTION_RIGHT = OK")
        
#         #=======================================    status
#         if HLA_POSTION_LEFT == "OK" and HLA_POSTION_RIGHT == "OK":
#             HLA_POSTION = "OK"
             
#         else:
#             HLA_POSTION ="NOT OK"

        
#     except Exception as e:
#         logger.debug(f"except Exception HLA_PostionCheck_with_nut {e}")
#         print("HLA_classCheck is :",e)
#     return HLA_POSTION, original_image
    




def check_for_defect(maskRCNNObj, ImageLink, ImageLink_2, Engine_no, OrgPosition):
    DEFECT_LIST_1 = ["cam_cap_I","cam_cap_2","cam_cap_3","cam_cap_4", "cam_cap_5","cam_cap_missing", "hla_base_half", "hla_base", "nut_missing", "hla_base" ,"NOT_OK_E","NOT_OK_arrow","NOT_OK_2","NOT_OK_I","NOT_OK_3"]
    DEFECT_LIST_2 = ["cam_cap_I","cam_cap_1","cam_cap_3","cam_cap_4", "cam_cap_5","cam_cap_missing", "hla_base_half", "hla_base", "nut_missing", "hla_base" ,"NOT_OK_E","NOT_OK_arrow","NOT_OK_2","NOT_OK_I","NOT_OK_3"]
    DEFECT_LIST_3 = ["cam_cap_I","cam_cap_1","cam_cap_2","cam_cap_4", "cam_cap_5","cam_cap_missing", "hla_base_half", "hla_base", "nut_missing", "hla_base" ,"NOT_OK_E","NOT_OK_arrow","NOT_OK_2","NOT_OK_I","NOT_OK_3"]
    DEFECT_LIST_4 = ["cam_cap_I","cam_cap_1","cam_cap_2","cam_cap_3", "cam_cap_5","cam_cap_missing", "hla_base_half", "hla_base", "nut_missing", "hla_base" ,"NOT_OK_E","NOT_OK_arrow","NOT_OK_2","NOT_OK_I","NOT_OK_3"]
    DEFECT_LIST_5 = ["cam_cap_E","cam_cap_1","cam_cap_2","cam_cap_3", "cam_cap_4","cam_cap_missing", "hla_base_half", "hla_base", "nut_missing", "hla_base" ,"NOT_OK_E","NOT_OK_arrow","NOT_OK_2","NOT_OK_I","NOT_OK_3"]
    
    DEFECT_LIST_6 = ["cam_cap_E","cam_cap_1","cam_cap_2","cam_cap_3", "cam_cap_5","cam_cap_missing", "hla_base_half", "hla_base", "nut_missing", "hla_base" ,"NOT_OK_E","NOT_OK_arrow","NOT_OK_2","NOT_OK_I","NOT_OK_3"]
    DEFECT_LIST_7 = ["cam_cap_E","cam_cap_1","cam_cap_2","cam_cap_4", "cam_cap_5","cam_cap_missing", "hla_base_half", "hla_base", "nut_missing", "hla_base" ,"NOT_OK_E","NOT_OK_arrow","NOT_OK_2","NOT_OK_I","NOT_OK_3"]
    DEFECT_LIST_8 = ["cam_cap_E","cam_cap_1","cam_cap_3","cam_cap_4", "cam_cap_5","cam_cap_missing", "hla_base_half", "hla_base", "nut_missing", "hla_base" ,"NOT_OK_E","NOT_OK_arrow","NOT_OK_2","NOT_OK_I","NOT_OK_3"]
    DEFECT_LIST_9 = ["cam_cap_E","cam_cap_2","cam_cap_3","cam_cap_4", "cam_cap_5","cam_cap_missing", "hla_base_half", "hla_base", "nut_missing", "hla_base" ,"NOT_OK_E","NOT_OK_arrow","NOT_OK_2","NOT_OK_I","NOT_OK_3"]
    
    #========
    #OK_LIST_1 = ["cam_cap_1", "cam_cap_E", "cam_cap_arrow", "hla_top", "nut_present"]
    OK_LIST_1 = ["cam_cap_1", "cam_cap_E", "cam_cap_arrow", "hla_top","hla_rod_top"]

    #OK_LIST_1 = ["cam_cap_E", "cam_cap_arrow", "hla_top"]
    OK_LIST_2 = ["cam_cap_2", "cam_cap_E", "cam_cap_arrow", "hla_top","hla_rod_top"]
    OK_LIST_3 = ["cam_cap_3", "cam_cap_E", "cam_cap_arrow", "hla_top","hla_rod_top"]
    OK_LIST_4 = ["cam_cap_4", "cam_cap_E", "cam_cap_arrow", "hla_top","hla_rod_top"]
    
    OK_LIST_5 = ["cam_cap_5", "cam_cap_I", "cam_cap_arrow"]
    OK_LIST_6 = ["cam_cap_4", "cam_cap_I", "cam_cap_arrow", "hla_top","hla_rod_top"]
    OK_LIST_7 = ["cam_cap_3", "cam_cap_I", "cam_cap_arrow", "hla_top","hla_rod_top"]
    OK_LIST_8 = ["cam_cap_2", "cam_cap_I", "cam_cap_arrow", "hla_top","hla_rod_top"]
    OK_LIST_9 = ["cam_cap_1", "cam_cap_I", "cam_cap_arrow", "hla_top","hla_rod_top"]
    #OK_LIST_9 = ["cam_cap_I", "cam_cap_arrow", "hla_top"]

    #=====VK CHANGE
    CLASS_NAME_OK_LIST_1 = ["cam_cap_1", "cam_cap_E", "cam_cap_arrow", "hla_top", "cam_cap_ok"]
    #CLASS_NAME_OK_LIST_1 = ["cam_cap_E", "cam_cap_arrow", "hla_top", "cam_cap_ok"]
    CLASS_NAME_LIST1_STATUS = False

    CLASS_NAME_OK_LIST_2 = ["cam_cap_2", "cam_cap_E", "cam_cap_arrow", "hla_top", "cam_cap_ok"]
    CLASS_NAME_LIST2_STATUS = False

    CLASS_NAME_OK_LIST_3 = ["cam_cap_3", "cam_cap_E", "cam_cap_arrow", "hla_top", "cam_cap_ok"]
    CLASS_NAME_LIST3_STATUS = False

    CLASS_NAME_OK_LIST_4 = ["cam_cap_4", "cam_cap_E", "cam_cap_arrow", "hla_top", "cam_cap_ok"]
    CLASS_NAME_LIST4_STATUS = False

    CLASS_NAME_OK_LIST_5 = ["cam_cap_5", "cam_cap_I", "cam_cap_arrow","cam_cap_ok"]
    CLASS_NAME_LIST5_STATUS = False

    CLASS_NAME_OK_LIST_6 = ["cam_cap_4", "cam_cap_I", "cam_cap_arrow", "hla_top", "cam_cap_ok"]
    CLASS_NAME_LIST6_STATUS = False

    CLASS_NAME_OK_LIST_7 = ["cam_cap_3", "cam_cap_I", "cam_cap_arrow", "hla_top", "cam_cap_ok"]
    CLASS_NAME_LIST7_STATUS = False

    CLASS_NAME_OK_LIST_8 = ["cam_cap_2", "cam_cap_I", "cam_cap_arrow", "hla_top","cam_cap_ok"]
    CLASS_NAME_LIST8_STATUS = False

    CLASS_NAME_OK_LIST_9 = ["cam_cap_1", "cam_cap_I", "cam_cap_arrow", "hla_top","cam_cap_ok"]
    #CLASS_NAME_OK_LIST_9 = ["cam_cap_I", "cam_cap_arrow", "hla_top","cam_cap_ok"]
    CLASS_NAME_LIST9_STATUS = False

    if OrgPosition == 3:
        Position = 2
    elif OrgPosition == 5:
        Position = 4
    elif OrgPosition == 7:
        Position = 6
    elif OrgPosition == 9:
        Position = 8

    #POSTION1_DEFECT_STATUS = True
    STATUS_POSTION2 = "NOT OK"
    STATUS_POSTION3 = "NOT OK"
    STATUS_POSTION4 = "NOT OK"
    STATUS_POSTION5 = "NOT OK"
    STATUS_POSTION6 = "NOT OK"
    STATUS_POSTION7 = "NOT OK"
    STATUS_POSTION8 = "NOT OK"
    STATUS_POSTION9 = "NOT OK"
    STATUS_POSTION11 = "OK"
    inseryData_SQL = False
    StatusPreview = "NOT OK"

    CLASS_NAME_LIST1_STATUS_POSWISE = True 

    
    try:
        imageList = []
       # time.sleep(1)
        imageList.append(ImageLink_2)
        imageList.append(ImageLink)
        
        #Position = OrgPosition
        if OrgPosition != 11:
            if len(imageList) != 2:
            # continue
                print("image not enf")
        
        clearList = []
        for imageLink in imageList:
            if OrgPosition == 3:
                Position = 2
            elif OrgPosition == 5:
                Position = 4
            elif OrgPosition == 7:
                Position = 6
            elif OrgPosition == 9:
                Position = 8

            elif OrgPosition ==11:
                Position = 11
            if "CAM2" in imageLink:
                if OrgPosition != 11:
                    Position = Position + 1
            

            #=================== CHECK PRIVIEW CYCLE END OR NOT ===================#
                       
            defect_list = []
            ok_list = []
            arrow_Xmax = None  # Initialize arrow_Xmax outside the loop
            OUT_LIST = []
            DEFECT_STATUS = True
            STATUS = "NOT OK"
            inseryData = False

            HLA_PostionCheck =  "NOT OK"
            Arrow_PostionCheck = False
            HLA_Class_Avi_or_not  = False
            checkOnce_Status1 = False
            checkOnce_Status2 = False
            
            try:
                if imageLink == '':
                    print("no image")
                    pass
                if imageLink != '':
                    OBJECT_LIST = maskRCNNObj.run_inference_new(imageLink)
                    original_image = cv2.imread(imageLink)
                    imreal = original_image.copy()
                    logger.debug(f"Engine_no is========== {Engine_no}")  #
                    if OBJECT_LIST == []:
                        TodaysDate = datetime.datetime.now().strftime('%Y_%m_%d')
                        #engine_folder_path = os.path.join(SAVED_FOLDER_PATH,str(TodaysDate), str(Engine_no))   DEFECT_DATA ALGORITHAM MODEL 1920 1080

                        if os.path.exists(os.path.join(SAVED_FOLDER_PATH, TodaysDate)) is False: 
                            os.mkdir(os.path.join(SAVED_FOLDER_PATH, TodaysDate))
                        if os.path.exists(os.path.join(os.path.join(SAVED_FOLDER_PATH, TodaysDate),Engine_no)) is False:
                            os.mkdir(os.path.join(os.path.join(SAVED_FOLDER_PATH, TodaysDate),Engine_no))
                        image_folder_link1 = os.path.join(SAVED_FOLDER_PATH, TodaysDate)
                        engine_folder_path=(image_folder_link1+"/"+Engine_no)+"/"

                        #inseryData = True
                        STATUS = "NOT OK"
                        # if "CAM2" in imageLink:
                        inf_img = f"IMG_{Position}.jpg"
                        #==== FOR 180D ROTATE IMAGE ==========#
                        image_aft_rotate = cv2.rotate(original_image, cv2.ROTATE_180)

                        current_datetime = datetime.datetime.now()
                        formatted_dateime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
                        # Generate image paths including the folder structure
                        realcam1_image_path = os.path.join(engine_folder_path, formatted_dateime+f"_IMG_{Position}_real.jpg")
                        cam4_image_path = os.path.join(engine_folder_path,formatted_dateime+f"_IMG_{Position}.jpg")
                        
                        cv2.imwrite(realcam1_image_path, imreal)
                        cv2.imwrite(cam4_image_path, image_aft_rotate)
                        clearList.append(0)
                        clearList.append(2)

                        IS_PROCESS_INF,STATUS = insertDataIndotprocessing_table(Engine_no, STATUS, imageLink, cam4_image_path,defect_list,ok_list)
                        update_inference_trigger(IS_PROCESS_INF,STATUS)
                        

                    original_image = cv2.imread(imageLink)
                    color = (0, 0, 0)
                    COUNTER_NOT_OK_FLAG = 0
                    COUNTER_OK_FLAG = 0

                    Engine_no_NEW,StatusPreview = getInferenceTrigger_2()

                    # if StatusPreview != "NO": 
                    #     print("preview status not update")
                    #     continue
                    # else:
                    Arrow_PostionCheck, original_image = Arrow_Position_Check(Position,original_image,OBJECT_LIST)
                    HLA_Class_Avi_or_not = HLA_classCheck(OBJECT_LIST)
                    HLA_PostionCheck,original_image = HLA_PostionCheck_with_nut(Position,OBJECT_LIST,original_image)

                    Arrow_PostionCheck = True
                    HLA_Class_Avi_or_not = True

                   # HLA_PostionCheck = "OK"
                    for labels in OBJECT_LIST:
                        xmin, ymin, xmax, ymax = labels[1:5]

                        #============================= Postion 2 ==================================#
                        if Position == 2:
                            #if Position == 2:
                            inseryData = True
                            if checkOnce_Status1 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in CLASS_NAME_OK_LIST_1):
                                    CLASS_NAME_LIST1_STATUS = True    
                                    print("CLASS NAME LIST IS OK")  
                                    checkOnce_Status1 = True         
                                else:
                                    CLASS_NAME_LIST1_STATUS = False    
                                    print("CLASS NAME LIST IS NOT OK")
                                    checkOnce_Status1 = True 

                            elif checkOnce_Status2 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in DEFECT_LIST_1):
                                    CLASS_NAME_LIST1_STATUS_POSWISE = False    
                                    print("CLASS_NAME_LIST1_STATUS_POSWISE IS NOT OK")  
                                    checkOnce_Status2 = True
                            

                            if labels[0] == "cam_cap_I":
                                OUT_LIST.append(labels[0])
                            print("labels[0] is :",labels[0])
                            if labels[0] in DEFECT_LIST_1 and labels[0] not in OK_LIST_1 and len(OUT_LIST) == 0:
                                COUNTER_NOT_OK_FLAG +=1
                                #COUNTER_OK_FLAG +=1
                                color = (0, 0, 255)
                                defect_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)
                                print("CLASS NAME LIST IS NOT OK") 
                                POSTION2_DEFECT_STATUS = False 
            
                            elif labels[0] not in DEFECT_LIST_1 and labels[0] in OK_LIST_1 and len(OUT_LIST) == 0:
                                COUNTER_OK_FLAG +=1
                                color = (0, 255, 0)
                                ok_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)
                                print("CLASS NAME LIST IS OK") 

                        #============================= Postion 3 =================================#
                        elif Position == 3:
                            inseryData = True
                            if checkOnce_Status1 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in CLASS_NAME_OK_LIST_2):
                                    print(" Status OK ")
                                    CLASS_NAME_LIST1_STATUS = True 
                                    checkOnce_Status1 = True  
                                
                                else:
                                    CLASS_NAME_LIST1_STATUS = False    
                                    print("CLASS NAME LIST IS NOT OK")
                                    checkOnce_Status1 = True 
                            elif checkOnce_Status2 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in DEFECT_LIST_2):
                                    CLASS_NAME_LIST1_STATUS_POSWISE = False    
                                    print("CLASS_NAME_LIST1_STATUS_POSWISE IS NOT OK")  
                                    checkOnce_Status2 = True


                            if labels[0] == "cam_cap_I" and labels[0] == "cam_cap_3":
                                #if labels[0] == "cam_cap_1":
                                OUT_LIST.append(labels[0])
            
                            if labels[0] in DEFECT_LIST_2 and labels[0] not in OK_LIST_2 and len(OUT_LIST) == 0:
                                COUNTER_NOT_OK_FLAG +=1
                                color = (0, 0, 255)
                                defect_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)
                                POSTION3_DEFECT_STATUS = False 
            
                            elif labels[0] not in DEFECT_LIST_2 and labels[0] in OK_LIST_2 and len(OUT_LIST) == 0:
                                COUNTER_OK_FLAG +=1
                                color = (0, 255, 0)
                                ok_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)

                        #============================= Postion 4 ==================================#
                        elif Position == 4:
                            inseryData = True
                            if checkOnce_Status1 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in CLASS_NAME_OK_LIST_3):
                                    CLASS_NAME_LIST1_STATUS = True   
                                    checkOnce_Status1 = True 
                                else:
                                    CLASS_NAME_LIST1_STATUS = False 
                                    checkOnce_Status1 = True 

                            if checkOnce_Status2 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in DEFECT_LIST_3):
                                    CLASS_NAME_LIST1_STATUS_POSWISE = False    
                                    print("CLASS NAME LIST IS NOT OK") 
                                    checkOnce_Status2 = True 
                            
                            if labels[0] == "cam_cap_I":
                                OUT_LIST.append(labels[0])
                                # labels[0] = "cam_cap_1"
                            if labels[0] in DEFECT_LIST_3 and labels[0] not in OK_LIST_3 and len(OUT_LIST) == 0:
                                COUNTER_NOT_OK_FLAG +=1
                                color = (0, 0, 255)
                                defect_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)
                                POSTION4_DEFECT_STATUS = False 
            
                            elif labels[0] not in DEFECT_LIST_3 and labels[0] in OK_LIST_3 and len(OUT_LIST) == 0:
                                COUNTER_OK_FLAG +=1
                                color = (0, 255, 0)
                                ok_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)

                        #============================= Postion 5 ==================================#
                        elif Position == 5:
                            inseryData = True
                            if checkOnce_Status1 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in CLASS_NAME_OK_LIST_4):
                                    CLASS_NAME_LIST1_STATUS = True  
                                    print("Status OK")
                                    checkOnce_Status1 = True 

                                else:
                                    CLASS_NAME_LIST1_STATUS = False
                                    print("Status NOT OK")
                                    checkOnce_Status1 = True 
                            if checkOnce_Status2 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in DEFECT_LIST_4):
                                    CLASS_NAME_LIST1_STATUS_POSWISE = False    
                                    print("CLASS NAME LIST IS NOT OK")
                                    checkOnce_Status2 = True 

                            if labels[0] == "cam_cap_I":
                                OUT_LIST.append(labels[0])
                            if labels[0] in DEFECT_LIST_4 and labels[0] not in OK_LIST_4 and len(OUT_LIST) ==0:
                                COUNTER_NOT_OK_FLAG +=1
                                color = (0, 0, 255)
                                defect_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)
                                POSTION5_DEFECT_STATUS = False 
            
                            elif labels[0] not in DEFECT_LIST_4 and labels[0] in OK_LIST_4 and len(OUT_LIST) ==0:
                                COUNTER_OK_FLAG +=1
                                color = (0, 255, 0)
                                ok_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)

                        #============================= Postion 11 ==================================#
                        elif Position == 11:
                            inseryData = True
                            if checkOnce_Status1 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in CLASS_NAME_OK_LIST_5):
                                    print(" Status OK ")
                                    CLASS_NAME_LIST1_STATUS = True  
                                    checkOnce_Status1 = True 

                                else:
                                    CLASS_NAME_LIST1_STATUS = False
                                    print("Status NOT OK")
                                    checkOnce_Status1 = True 
                            if checkOnce_Status2 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in DEFECT_LIST_5):
                                    CLASS_NAME_LIST1_STATUS_POSWISE = False    
                                    print("CLASS NAME LIST IS NOT OK")
                                    checkOnce_Status2 = True 

                            
                            if labels[0] in DEFECT_LIST_5 and labels[0] not in OK_LIST_5:
                                COUNTER_NOT_OK_FLAG +=1
                                #COUNTER_NOT_OK_FLAG = 0
                                color = (0, 0, 255)
                                defect_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)
                                POSTION11_DEFECT_STATUS = False 

                            elif labels[0] not in DEFECT_LIST_5 and labels[0] in OK_LIST_5:
                                COUNTER_OK_FLAG +=1
                                #COUNTER_OK_FLAG =5
                                color = (0, 255, 0)
                                ok_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)
                            
                        #============================= Postion 7 ==================================#
                        elif Position == 7:
                            inseryData = True
                            if checkOnce_Status1 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in CLASS_NAME_OK_LIST_6):
                                    print(" Status OK ")
                                    CLASS_NAME_LIST1_STATUS = True 
                                    checkOnce_Status1 = True  
                                else:
                                    CLASS_NAME_LIST1_STATUS = False
                                    print("Status NOT OK")
                                    checkOnce_Status1 = True 

                            if checkOnce_Status2 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in DEFECT_LIST_6):
                                    CLASS_NAME_LIST1_STATUS_POSWISE = False    
                                    print("CLASS NAME LIST IS NOT OK")
                                    checkOnce_Status2 = True

                            
                            if labels[0] in DEFECT_LIST_6 and labels[0] not in OK_LIST_6:
                                COUNTER_NOT_OK_FLAG +=1
                                color = (0, 0, 255)
                                defect_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)
                                POSTION7_DEFECT_STATUS = False 

                            elif labels[0] not in DEFECT_LIST_6 and labels[0] in OK_LIST_6:
                                COUNTER_OK_FLAG +=1
                                color = (0, 255, 0)
                                ok_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)

                        #============================= Postion 6 ==================================#
                        elif Position == 6:
                            inseryData = True
                            if checkOnce_Status1 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in CLASS_NAME_OK_LIST_7):
                                    print(" Status OK ")
                                    CLASS_NAME_LIST1_STATUS = True 
                                    checkOnce_Status1 = True   

                                else:
                                    CLASS_NAME_LIST1_STATUS = False
                                    print("Status NOT OK")
                                    checkOnce_Status1 = True  
                            if checkOnce_Status2 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in DEFECT_LIST_7):
                                    CLASS_NAME_LIST1_STATUS_POSWISE = False    
                                    print("CLASS NAME LIST IS NOT OK")
                                    checkOnce_Status2 = True  

                    
                            if labels[0] in DEFECT_LIST_7 and labels[0] not in OK_LIST_7:
                                COUNTER_NOT_OK_FLAG +=1
                                color = (0, 0, 255)
                                defect_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)
                                POSTION6_DEFECT_STATUS = False 

                            elif labels[0] not in DEFECT_LIST_7 and labels[0] in OK_LIST_7:
                                COUNTER_OK_FLAG +=1
                                color = (0, 255, 0)
                                ok_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)

                        #============================= Postion 9 ==================================#
                        elif Position == 9:
                            inseryData = True
                            if checkOnce_Status1 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in CLASS_NAME_OK_LIST_8):
                                    print(" Status OK ")
                                    CLASS_NAME_LIST1_STATUS = True  
                                    checkOnce_Status1 = True 

                                else:
                                    CLASS_NAME_LIST1_STATUS = False
                                    print("Status NOT OK")
                                    checkOnce_Status1 = True 
                            if checkOnce_Status2 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in DEFECT_LIST_8):
                                    CLASS_NAME_LIST1_STATUS_POSWISE = False    
                                    print("CLASS NAME LIST IS NOT OK")
                                    checkOnce_Status2 = True 

                            
                            if labels[0] in DEFECT_LIST_8 and labels[0] not in OK_LIST_8:
                                COUNTER_NOT_OK_FLAG +=1
                                color = (0, 0, 255)
                                defect_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)
                                POSTION9_DEFECT_STATUS = False 

                            elif labels[0] not in DEFECT_LIST_8 and labels[0] in OK_LIST_8:
                                COUNTER_OK_FLAG +=1
                                color = (0, 255, 0)
                                ok_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)

                        #============================= Postion 8 ==================================#
                        elif Position == 8:
                            inseryData = True
                            if checkOnce_Status1 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in CLASS_NAME_OK_LIST_9):
                                    print(" Status OK ")
                                    CLASS_NAME_LIST1_STATUS = True   
                                    checkOnce_Status1 = True 

                                else:
                                    CLASS_NAME_LIST1_STATUS = False
                                    print("Status NOT OK")
                                    checkOnce_Status1 = True 
                            
                            if checkOnce_Status2 == False:
                                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in DEFECT_LIST_9):
                                    CLASS_NAME_LIST1_STATUS_POSWISE = False    
                                    print("CLASS NAME LIST IS NOT OK") 
                                    checkOnce_Status2 = True                    
                        
                            if labels[0] in DEFECT_LIST_9 and labels[0] not in OK_LIST_9:
                                COUNTER_NOT_OK_FLAG +=1
                                color = (0, 0, 255)
                                defect_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)
                                POSTION8_DEFECT_STATUS = False 

                            elif labels[0] not in DEFECT_LIST_9 and labels[0] in OK_LIST_9:
                                COUNTER_OK_FLAG +=1
                                color = (0, 255, 0)
                                ok_list.append(labels[0])
                                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                                label_text = f"{labels[0]}: {labels[5]:.3f}"
                                cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)

                    if inseryData == True:
                        SAVED_FOLDER_PATH_NOTOK = "C:/insightzz/CAM_CAP/DefectData_not_ok/"
                        TodaysDate = datetime.datetime.now().strftime('%Y_%m_%d')
                        #engine_folder_path = os.path.join(SAVED_FOLDER_PATH,str(TodaysDate), str(Engine_no))
                        if os.path.exists(os.path.join(SAVED_FOLDER_PATH, TodaysDate)) is False: 
                            os.mkdir(os.path.join(SAVED_FOLDER_PATH, TodaysDate))
                        if os.path.exists(os.path.join(os.path.join(SAVED_FOLDER_PATH, TodaysDate),Engine_no)) is False:
                            os.mkdir(os.path.join(os.path.join(SAVED_FOLDER_PATH, TodaysDate),Engine_no))
                        image_folder_link1 = os.path.join(SAVED_FOLDER_PATH, TodaysDate)
                        engine_folder_path=(image_folder_link1+"/"+Engine_no)+"/"

                        # if os.path.exists(os.path.join(SAVED_FOLDER_PATH_NOTOK, TodaysDate)) is False: 
                        #     os.mkdir(os.path.join(SAVED_FOLDER_PATH_NOTOK, TodaysDate))
                        # if os.path.exists(os.path.join(os.path.join(SAVED_FOLDER_PATH_NOTOK, TodaysDate),Engine_no)) is False:
                        #     os.mkdir(os.path.join(os.path.join(SAVED_FOLDER_PATH_NOTOK, TodaysDate),Engine_no))
                        # image_folder_link1_notok = os.path.join(SAVED_FOLDER_PATH_NOTOK, TodaysDate)
                        # engine_folder_path_notok=(image_folder_link1_notok+"/"+Engine_no)+"/"



                         #==== FOR 180D ROTATE IMAGE ==========#
                        image_aft_rotate = cv2.rotate(original_image, cv2.ROTATE_180)
                        current_datetime = datetime.datetime.now()
                        formatted_dateime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
                        # Generate image paths including the folder structure
                        realcam1_image_path = os.path.join(engine_folder_path, formatted_dateime+f"_IMG_{Position}_real.jpg")
                        cam4_image_path = os.path.join(engine_folder_path,formatted_dateime+f"_IMG_{Position}.jpg")
                        cv2.imwrite(realcam1_image_path, imreal)
                        cv2.imwrite(cam4_image_path, image_aft_rotate)
                       
                        if OrgPosition != 11:
                            if COUNTER_OK_FLAG >= 4 and COUNTER_NOT_OK_FLAG == 0 and CLASS_NAME_LIST1_STATUS == True and Arrow_PostionCheck == True and CLASS_NAME_LIST1_STATUS_POSWISE == True and HLA_Class_Avi_or_not == True and HLA_PostionCheck == "OK" :# here counter_ok_flag is set to 5 if model is improved or logic is added
                                STATUS_POSTION2 = "OK"
                                clearList.append(1)

                            else:
                                STATUS_POSTION2 = "NOT OK"
                                IS_PROCESS_INF =2
                                clearList.append(0)
                                clearList.append(2)

                        else:
                            if COUNTER_OK_FLAG >= 3 and COUNTER_NOT_OK_FLAG == 0 and CLASS_NAME_LIST1_STATUS == True and Arrow_PostionCheck == True and CLASS_NAME_LIST1_STATUS_POSWISE == True :# here counter_ok_flag is set to 5 if model is improved or logic is added
                                STATUS_POSTION2 = "OK"
                                clearList.append(1)

                            else:
                                STATUS_POSTION2 = "NOT OK"
                                IS_PROCESS_INF =2
                                clearList.append(0)
                                clearList.append(2)

                                                                
                        IS_PROCESS_INF,STATUS_POSTION2 = insertDataIndotprocessing_table(Engine_no, STATUS_POSTION2, imageLink, cam4_image_path, defect_list, ok_list)
                        start_pdf(STATUS_POSTION2, Engine_no,engine_folder_path)
                        inseryData_SQL == True

            except Exception as e:
                logger.debug(f"except Exception imag inf for {Position} and error {e}")
                print("except Exception INF IMAGE",e)
                      
        try:
            if OrgPosition != 11:
                if len(clearList) >= 2:
                    if all(x == 1 for x in clearList):
                        STATUS_POSTION2 = "OK"
                        IS_PROCESS_INF =2
                        update_inference_trigger(IS_PROCESS_INF,STATUS_POSTION2)  
                        clearList.clear()
                    else:
                        STATUS_POSTION2 = "NOT OK"
                        IS_PROCESS_INF =2
                        update_inference_trigger(IS_PROCESS_INF,STATUS_POSTION2) 
                        clearList.clear()
            else:
                if all(x == 1 for x in clearList):
                    STATUS_POSTION2 = "OK"
                    IS_PROCESS_INF =2
                    update_inference_trigger(IS_PROCESS_INF,STATUS_POSTION2)  
                    clearList.clear()
                else:
                    STATUS_POSTION2 = "NOT OK"
                    IS_PROCESS_INF =2
                    update_inference_trigger(IS_PROCESS_INF,STATUS_POSTION2) 
                    clearList.clear()


        except Exception as e:
            logger.debug(f"except Exception OrgPosition != 11 for {Position} and error {e}")
            print("update_inference_trigger",e)
    except Exception as e:
        print(e)
        logger.debug(f"except Exception check_for_defect for {Position} and error {e}")
        logger.debug(f"Error in check_for_defect(): {e}")

    return STATUS, defect_list, ok_list

def drawPolygonPoints(image,data_list):
    # Set the polygon points
    points = np.array(data_list, np.int32)
    # Reshape the points array to match the required format for cv2.polylines()
    points = points.reshape((-1, 1, 2))
    # Set the color and thickness of the polygon outline
    color = (0, 255, 0)  # BGR color format (red)
    thickness = 5
    # Draw the polygon on the image
    cv2.polylines(image, [points], isClosed=True, color=color, thickness=thickness)

def getMinMaxValues(values):
    minX = float('inf')
    minY = float('inf')
    maxX = float('-inf')
    maxY = float('-inf')
    
    for point in values:
        x, y = point
        if x < minX:
            minX = x
        if y < minY:
            minY = y
        if x > maxX:
            maxX = x
        if y > maxY:
            maxY = y
    return minX,minY,maxX,maxY


#============================== pdf =========================#
def start_pdf(final_status, engine_number, dirname):
    #engine_number = "VK1234567890"#Part_number#getEngineNumberDetails()
    print(engine_number)
    TodaysDate = datetime.datetime.now().strftime('%Y_%m_%d')
    #dirName = "/home/viks/VIKS/CODE/PROJECT_ALGORITHAM/NEW_EGAL_PROJECT/pdfgenerate/DEFECT_IMAGES/2023_08_25/"
    dirName =dirname+"/"#f"/home/deepak/Desktop/TOX/OP_40/INF_IMAGES"

    #image_folder_link1 = os.path.join(dirName, TodaysDate)
    #image_folder_link=(dirName+"/"+engine_number)+"/"
    #print(image_folder_link)
    #Status = engine_number
    INF_IMAGE_PATH_LIST=os.listdir(dirName)
    INF_IMAGE_PATH_LIST.sort()
    image_file_list = []
    for image_file in INF_IMAGE_PATH_LIST:
        if image_file.lower().endswith(('.jpg','.jpeg')):
            INF_FOLDER_PATH=dirName+image_file
            image_file_list.append(INF_FOLDER_PATH)
            # Replace double slashes with a single slash in each element of the list
            image_file_list = [path.replace("//", "/") for path in image_file_list]
    
    DateTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    SavedirName = dirName
    createPDF(image_file_list,final_status, engine_number, DateTime, SavedirName)
    print("createPDF Completed++++++++++++++++++++++")   



def reduceImageQuality(image_file_list):
    for image in image_file_list:
        image_file = Image.open(image)
        image_file.save(image, quality=25)

def createPDF(image_file_list,final_status, engine_number,DateTime,SavedirName):
    global gMailObj
    pdf = FPDF()
    reduceImageQuality(image_file_list)
    pdf.add_page("L")
    pdf.rect(5.0,4.0,285.0,200.0)
    pdf.set_font('Arial', 'B', 30)
    pdf.cell(270,10,"DRISHTI PORTAL",0,1,'C')
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(270,15,"HLA CAM CAP REPORT",0,1,'C')

    pdf.image("C:/insightzz/CAM_CAP/UI_CODE/LOGO/Mahindra-Mahindra-New-Logo.png", x=10, y=5, w=50, h=30, type='png')
    #pdf.image("c:/INSIGHTZZ/PISTON_DROPING_UI_MAIN/LOGO/download.jpg", x=220, y=5, w=60, h=30, type='jpg')

    pdf.rect(5.0,38.0,285.0,166.0)
    pdf.cell(270,30,"Engine Number : "+engine_number,0,1)
    pdf.set_font('Arial', 'B', 15)
    pdf.cell(270,10,"Date & Time of Inspection : "+DateTime,0,1)
    pdf.cell(270,10,"Engine Status : "+final_status,0,1)
    pdf.set_font("Times", size=13)   
    image_file_list1=[]
    image__file_list2=[]
    counter=0
    counter2=0
    for image in image_file_list:
        image_file_list1.append(image)
       
    if len(image_file_list1) >0:
        for image in image_file_list1:
            pdf.add_page("L")
            pdf.rect(5.0,4.0,285.0,200.0)
            fixed_height = 170
            pdf.set_font('Arial', 'B', 20)
            pdf.cell(250,10,"IMAGE NAME : "+os.path.basename(image),0,1,'C')
            img = Image.open(image)
            height_percent = (fixed_height / float(img.size[1]))
            width_size = int((float(img.size[0]) * float(height_percent)))
            pdf.image(image,20,20,width_size,fixed_height)
            counter=counter+1
            print(counter)
            if counter==20:
                break
    
    pdf.output(SavedirName+"/"+engine_number+".pdf", "F")   



def run(maskRCNNObj):
    try:
        while True:

            POSITION_WISE_DETECTION_POSITION = {}
            POSITION_WISE_DETECTION_POSITION["1"] = [[529,651],[526,1239],[900,1251],[921,657]]
            POSITION_WISE_DETECTION_POSITION["2"] = [[1670,656],[1666,1289],[2143,1310],[2150,664]]
            cam1_DefectStatus = False
            POLYGON_MAP = {}
            # POLYGON_MAP["1"]= [[546,1192],[547,1166],[561,1145],[582,1135],[615,1132],[650,1137],[672,1149],[697,1164],[714,1169],[739,1171],[758,1167],[781,1160],[792,1150],[800,1134],[804,1116],[806,1085],[804,1061],[797,1044],[776,1030],[752,1021],[725,1019],[698,1017],[672,1007],[656,991],[647,971],[647,951],[652,922],[653,885],[650,862],[644,827],[642,809],[642,775],[645,750],[648,732],[661,720],[680,715],[703,715],[718,723],[729,735],[734,758],[731,768],[729,788],[727,826],[727,875],[731,900],[734,917],[746,936],[767,947],[778,952],[801,958],[831,961],[860,969],[872,977],[877,986],[877,1024],[873,1055],[869,1085],[869,1110],[869,1145],[872,1195],[866,1221],[856,1234],[838,1239],[806,1241],[770,1234],[745,1227],[714,1225],[682,1224],[652,1229],[615,1239],[585,1238],[565,1230],[553,1212]]
            # POLYGON_MAP["2"]= [[1973,779],[1961,793],[1955,810],[1953,832],[1953,851],[1954,884],[1954,918],[1951,944],[1950,953],[1943,967],[1935,973],[1911,977],[1885,980],[1861,982],[1831,986],[1808,994],[1794,1006],[1792,1049],[1791,1127],[1792,1185],[1797,1231],[1805,1252],[1819,1261],[1835,1265],[1852,1265],[1882,1261],[1913,1260],[1944,1260],[1981,1265],[2016,1275],[2041,1280],[2061,1280],[2077,1271],[2085,1255],[2089,1229],[2087,1205],[2079,1192],[2065,1184],[2045,1179],[2029,1182],[2017,1188],[1997,1197],[1966,1202],[1951,1202],[1929,1200],[1911,1197],[1889,1190],[1875,1178],[1865,1153],[1860,1129],[1862,1105],[1869,1086],[1882,1066],[1902,1059],[1928,1057],[1959,1060],[1978,1066],[1993,1064],[2011,1056],[2023,1041],[2031,1021],[2030,992],[2026,963],[2030,934],[2036,901],[2041,872],[2047,832],[2045,801],[2027,780],[2008,772],[1984,776]]
            
           #10 feb POLYGON_MAP["1"]= [[617,1128],[600,1127],[577,1132],[561,1140],[552,1152],[547,1170],[547,1189],[551,1205],[557,1219],[564,1230],[580,1237],[600,1238],[616,1237],[635,1233],[655,1226],[674,1223],[696,1220],[716,1220],[745,1222],[768,1228],[783,1232],[798,1237],[814,1238],[833,1238],[854,1234],[865,1222],[871,1209],[874,1192],[873,1158],[873,1126],[874,1091],[876,1065],[880,1038],[882,1024],[882,1002],[881,983],[875,972],[859,963],[844,959],[827,956],[801,951],[788,947],[773,942],[762,938],[750,931],[740,921],[734,912],[731,898],[729,877],[729,855],[731,823],[731,798],[733,778],[735,763],[735,743],[729,727],[717,716],[701,710],[679,709],[664,713],[653,721],[644,735],[641,751],[639,781],[639,806],[642,836],[647,856],[648,878],[649,907],[646,935],[643,955],[646,972],[652,990],[666,1001],[679,1011],[700,1017],[721,1018],[746,1018],[763,1022],[779,1026],[793,1037],[800,1049],[804,1065],[806,1088],[805,1110],[799,1135],[792,1147],[781,1155],[760,1164],[739,1167],[721,1167],[701,1161],[687,1156],[673,1147],[656,1137],[633,1130]]
           #10 feb POLYGON_MAP["2"]= [[2000,769],[1984,773],[1970,780],[1961,794],[1957,805],[1956,834],[1956,876],[1956,902],[1954,931],[1950,952],[1946,961],[1940,967],[1930,970],[1907,974],[1887,977],[1868,978],[1841,980],[1822,984],[1805,991],[1795,1001],[1793,1013],[1793,1062],[1792,1108],[1793,1161],[1793,1191],[1798,1226],[1804,1246],[1812,1256],[1828,1261],[1846,1261],[1874,1259],[1898,1254],[1928,1251],[1966,1253],[1991,1259],[2016,1268],[2040,1274],[2062,1276],[2077,1272],[2086,1262],[2093,1245],[2096,1225],[2094,1205],[2084,1191],[2075,1182],[2063,1177],[2046,1175],[2030,1176],[2014,1183],[2001,1189],[1979,1195],[1966,1197],[1944,1198],[1924,1197],[1903,1191],[1888,1184],[1874,1170],[1868,1156],[1864,1137],[1864,1120],[1866,1097],[1871,1077],[1877,1064],[1892,1055],[1914,1052],[1926,1054],[1942,1059],[1962,1061],[1976,1064],[1996,1061],[2013,1053],[2026,1037],[2032,1016],[2032,996],[2031,978],[2029,961],[2032,938],[2036,910],[2042,876],[2048,844],[2050,816],[2048,799],[2037,785],[2027,774],[2011,769]]
           #12feb POLYGON_MAP["1"]= [[645,734],[638,766],[639,811],[648,843],[655,868],[654,902],[654,944],[652,969],[654,992],[667,1008],[678,1016],[693,1021],[713,1024],[736,1025],[756,1026],[771,1028],[789,1038],[803,1053],[808,1068],[811,1088],[810,1114],[807,1143],[798,1156],[784,1166],[755,1168],[730,1167],[713,1164],[690,1157],[667,1146],[643,1141],[608,1136],[582,1138],[561,1149],[550,1164],[548,1190],[553,1215],[564,1230],[580,1240],[600,1243],[626,1242],[652,1239],[675,1234],[700,1233],[742,1234],[780,1237],[803,1242],[836,1244],[860,1240],[872,1229],[880,1207],[880,1139],[885,1058],[886,1023],[885,994],[884,975],[871,969],[851,968],[824,967],[798,961],[778,949],[759,938],[746,922],[742,906],[741,879],[745,832],[747,775],[742,748],[735,723],[715,709],[691,704],[665,708],[652,722]]
           #12feb POLYGON_MAP["2"]= [[2002,769],[1988,771],[1976,778],[1968,785],[1960,798],[1956,809],[1954,826],[1954,844],[1961,862],[1966,877],[1971,892],[1971,919],[1968,951],[1958,978],[1945,986],[1924,993],[1904,994],[1879,990],[1859,987],[1842,988],[1825,987],[1808,994],[1800,1006],[1800,1049],[1799,1139],[1800,1203],[1801,1232],[1807,1254],[1821,1266],[1834,1271],[1852,1271],[1882,1271],[1910,1267],[1938,1267],[1980,1268],[2003,1271],[2021,1277],[2036,1281],[2060,1283],[2078,1280],[2091,1271],[2099,1254],[2104,1232],[2101,1205],[2085,1191],[2071,1186],[2052,1187],[2030,1197],[2010,1206],[1987,1210],[1966,1212],[1937,1208],[1915,1202],[1898,1195],[1879,1183],[1872,1168],[1870,1147],[1871,1123],[1874,1098],[1878,1080],[1889,1069],[1904,1062],[1922,1060],[1940,1064],[1967,1068],[1995,1066],[2019,1057],[2033,1040],[2039,1015],[2038,986],[2037,969],[2037,952],[2042,921],[2046,891],[2055,848],[2056,819],[2052,794],[2041,779],[2023,771]]
           #13march POLYGON_MAP["1"]= [[676,729],[666,734],[657,746],[653,760],[650,774],[652,802],[655,832],[656,851],[657,869],[659,892],[660,907],[658,925],[657,947],[657,963],[660,978],[662,988],[671,1001],[681,1011],[693,1018],[706,1021],[722,1022],[743,1022],[759,1023],[772,1027],[788,1033],[796,1041],[802,1052],[807,1068],[810,1085],[810,1101],[808,1116],[804,1130],[802,1141],[797,1150],[795,1156],[786,1161],[774,1165],[760,1165],[750,1165],[740,1164],[726,1162],[706,1160],[694,1157],[681,1152],[669,1145],[655,1139],[640,1135],[622,1131],[606,1133],[595,1135],[586,1139],[578,1143],[570,1149],[563,1161],[560,1172],[559,1182],[559,1193],[560,1201],[564,1211],[570,1220],[577,1228],[584,1233],[596,1239],[609,1240],[624,1239],[637,1238],[648,1234],[656,1228],[666,1223],[678,1221],[690,1219],[703,1220],[718,1220],[735,1224],[756,1230],[767,1233],[787,1236],[810,1237],[835,1234],[851,1230],[864,1223],[875,1211],[878,1197],[877,1176],[876,1160],[877,1143],[878,1125],[880,1101],[880,1087],[881,1070],[881,1055],[882,1029],[882,1010],[881,992],[878,981],[871,973],[864,967],[857,965],[845,962],[832,959],[815,955],[802,951],[793,948],[780,944],[769,939],[761,933],[751,925],[745,919],[741,913],[739,904],[737,893],[737,882],[738,868],[739,853],[740,834],[741,821],[742,808],[742,797],[743,784],[741,767],[739,754],[735,737],[725,728],[706,723],[685,724]]
           #13march POLYGON_MAP["2"]= [[1964,797],[1964,814],[1965,836],[1966,864],[1967,888],[1967,913],[1965,939],[1965,953],[1959,966],[1954,971],[1943,975],[1927,978],[1910,978],[1891,979],[1879,978],[1866,977],[1845,980],[1831,985],[1817,992],[1808,1001],[1804,1009],[1803,1028],[1803,1065],[1804,1094],[1804,1126],[1804,1153],[1802,1194],[1802,1207],[1803,1223],[1809,1240],[1818,1253],[1829,1260],[1840,1265],[1853,1266],[1871,1265],[1884,1263],[1907,1260],[1925,1258],[1946,1258],[1969,1258],[1986,1258],[2008,1264],[2025,1269],[2040,1272],[2059,1274],[2073,1274],[2082,1269],[2091,1260],[2097,1248],[2100,1233],[2100,1216],[2097,1200],[2089,1188],[2082,1181],[2071,1178],[2052,1177],[2028,1183],[2015,1187],[2004,1188],[1988,1190],[1965,1191],[1948,1193],[1932,1192],[1919,1191],[1905,1190],[1895,1187],[1882,1180],[1872,1171],[1864,1160],[1860,1149],[1859,1135],[1861,1120],[1865,1106],[1870,1092],[1876,1077],[1883,1065],[1892,1057],[1901,1054],[1914,1053],[1927,1054],[1940,1057],[1953,1060],[1969,1061],[1985,1061],[1997,1057],[2009,1051],[2018,1045],[2026,1035],[2031,1024],[2035,1011],[2036,1000],[2037,986],[2036,970],[2035,953],[2036,938],[2036,927],[2038,915],[2039,902],[2041,891],[2044,876],[2047,865],[2050,855],[2053,841],[2054,825],[2055,811],[2053,796],[2047,782],[2041,775],[2026,771],[2012,769],[1997,770],[1982,774],[1971,785]]
           #16march POLYGON_MAP["1"]= [[587,1140],[573,1146],[561,1155],[554,1167],[552,1178],[553,1194],[554,1206],[558,1216],[562,1223],[570,1230],[578,1235],[587,1240],[595,1242],[604,1243],[615,1243],[625,1243],[636,1243],[646,1240],[656,1234],[667,1230],[674,1227],[682,1225],[693,1224],[704,1224],[716,1225],[728,1226],[735,1227],[743,1228],[751,1230],[758,1232],[766,1233],[774,1235],[780,1236],[790,1236],[800,1237],[809,1238],[819,1238],[827,1237],[839,1235],[849,1232],[857,1229],[866,1223],[871,1215],[872,1203],[869,1188],[868,1172],[868,1156],[869,1145],[870,1131],[871,1114],[873,1101],[874,1088],[876,1073],[878,1061],[882,1046],[882,1031],[883,1019],[882,1004],[878,992],[877,987],[874,981],[868,974],[859,970],[845,966],[832,964],[820,964],[807,962],[793,958],[782,954],[770,951],[759,947],[751,941],[743,936],[737,932],[731,922],[729,911],[730,899],[731,886],[730,876],[734,860],[735,847],[737,828],[738,814],[740,796],[739,781],[739,766],[739,753],[737,739],[731,730],[720,724],[703,721],[693,721],[680,722],[666,727],[656,737],[650,751],[647,770],[649,787],[650,798],[652,811],[654,824],[656,839],[657,858],[658,871],[658,879],[659,891],[660,905],[658,918],[657,930],[655,940],[654,953],[655,966],[657,979],[661,993],[669,1005],[678,1011],[686,1018],[700,1022],[712,1024],[728,1024],[739,1024],[752,1025],[768,1029],[784,1033],[793,1041],[801,1053],[806,1064],[807,1079],[807,1094],[807,1104],[807,1117],[803,1129],[797,1143],[794,1154],[785,1164],[765,1168],[755,1169],[734,1171],[719,1171],[709,1171],[692,1169],[678,1164],[671,1158],[662,1152],[651,1145],[641,1141],[629,1138],[619,1136],[609,1137],[595,1138]]
           #16march POLYGON_MAP["2"]= [[1837,1267],[1828,1263],[1820,1259],[1811,1249],[1805,1239],[1801,1230],[1799,1220],[1799,1210],[1800,1198],[1800,1190],[1800,1182],[1801,1176],[1801,1167],[1801,1158],[1802,1151],[1802,1142],[1802,1134],[1803,1125],[1803,1116],[1803,1106],[1802,1096],[1802,1087],[1801,1074],[1801,1068],[1801,1054],[1801,1040],[1800,1028],[1801,1017],[1805,1005],[1809,999],[1817,991],[1824,989],[1836,985],[1852,986],[1865,989],[1879,990],[1897,989],[1920,985],[1934,981],[1944,973],[1951,966],[1954,952],[1955,941],[1956,928],[1958,915],[1958,902],[1958,891],[1958,879],[1956,872],[1955,865],[1953,850],[1951,834],[1952,819],[1955,807],[1960,796],[1967,787],[1980,783],[1997,781],[2016,784],[2030,791],[2037,806],[2042,822],[2043,835],[2043,849],[2039,862],[2037,873],[2032,890],[2029,903],[2025,913],[2021,926],[2019,941],[2017,950],[2016,964],[2016,979],[2020,992],[2024,1010],[2025,1019],[2025,1030],[2022,1041],[2015,1050],[2006,1056],[1993,1062],[1981,1065],[1965,1065],[1955,1064],[1942,1061],[1926,1058],[1907,1058],[1895,1062],[1888,1066],[1882,1070],[1877,1077],[1872,1085],[1870,1092],[1868,1100],[1866,1108],[1861,1120],[1860,1132],[1860,1140],[1858,1146],[1859,1157],[1862,1169],[1866,1178],[1873,1185],[1882,1188],[1896,1192],[1905,1195],[1914,1197],[1929,1200],[1936,1201],[1947,1202],[1962,1204],[1977,1205],[1992,1202],[2008,1200],[2021,1197],[2034,1194],[2052,1191],[2069,1194],[2077,1198],[2086,1206],[2091,1216],[2094,1232],[2092,1245],[2088,1256],[2082,1266],[2071,1272],[2055,1274],[2036,1274],[2021,1271],[2007,1267],[1999,1266],[1988,1264],[1976,1263],[1963,1262],[1949,1260],[1934,1259],[1924,1258],[1914,1258],[1905,1259],[1897,1259],[1888,1260],[1877,1262],[1867,1264],[1861,1265],[1852,1266],[1845,1266]]
           #19march POLYGON_MAP["1"]= [[583,1136],[569,1142],[558,1149],[550,1160],[546,1171],[545,1188],[547,1202],[549,1215],[555,1223],[561,1230],[570,1236],[581,1243],[592,1246],[604,1247],[616,1246],[625,1243],[634,1240],[644,1236],[654,1231],[665,1226],[672,1224],[680,1222],[691,1221],[702,1221],[714,1221],[726,1222],[733,1223],[741,1224],[750,1226],[760,1228],[770,1231],[781,1233],[791,1236],[801,1239],[812,1240],[822,1240],[834,1238],[845,1235],[858,1231],[868,1223],[874,1212],[876,1199],[876,1187],[874,1172],[873,1162],[870,1146],[872,1135],[874,1122],[873,1110],[877,1098],[878,1090],[882,1081],[883,1070],[884,1056],[886,1042],[886,1029],[886,1015],[884,999],[880,986],[873,974],[863,969],[848,963],[829,960],[811,958],[800,955],[787,952],[774,947],[761,942],[752,935],[745,929],[741,922],[737,912],[736,904],[736,895],[736,883],[737,870],[737,857],[739,844],[741,828],[742,814],[744,800],[744,785],[744,769],[743,757],[743,746],[741,735],[734,727],[724,720],[710,715],[693,714],[673,716],[660,722],[652,732],[647,744],[644,760],[643,777],[643,789],[644,805],[646,817],[648,829],[649,839],[650,850],[651,862],[652,872],[652,883],[653,894],[654,907],[652,919],[651,931],[649,946],[650,963],[651,975],[654,988],[660,999],[667,1009],[679,1017],[690,1022],[704,1025],[719,1026],[735,1026],[746,1026],[761,1028],[773,1030],[785,1035],[793,1043],[801,1055],[804,1068],[805,1082],[805,1095],[805,1107],[803,1115],[800,1125],[796,1138],[791,1150],[781,1160],[769,1164],[754,1165],[739,1164],[720,1163],[708,1161],[695,1157],[684,1151],[675,1148],[666,1143],[653,1138],[642,1134],[628,1132],[616,1131],[604,1132],[593,1134]]
           #19march POLYGON_MAP["2"]= [[1832,1263],[1822,1258],[1812,1251],[1806,1241],[1801,1232],[1799,1223],[1797,1213],[1796,1201],[1797,1192],[1798,1184],[1798,1176],[1798,1170],[1798,1161],[1799,1152],[1799,1145],[1800,1136],[1800,1128],[1800,1119],[1801,1110],[1801,1100],[1800,1090],[1800,1081],[1798,1068],[1799,1062],[1798,1048],[1798,1034],[1798,1022],[1799,1011],[1804,1000],[1808,994],[1815,989],[1824,985],[1836,981],[1849,982],[1865,984],[1881,985],[1902,983],[1919,981],[1935,976],[1946,968],[1952,958],[1955,944],[1956,930],[1957,918],[1958,905],[1958,893],[1958,882],[1957,871],[1956,863],[1954,855],[1954,844],[1950,829],[1952,811],[1955,800],[1961,790],[1969,780],[1978,777],[1995,775],[2014,778],[2028,783],[2039,798],[2044,815],[2046,831],[2047,846],[2045,856],[2043,871],[2041,884],[2038,898],[2034,911],[2030,924],[2028,935],[2026,949],[2025,961],[2024,973],[2025,989],[2024,1007],[2024,1016],[2023,1024],[2020,1035],[2013,1044],[2006,1051],[1994,1058],[1981,1062],[1966,1061],[1952,1061],[1938,1057],[1922,1055],[1909,1054],[1897,1056],[1887,1059],[1881,1064],[1875,1072],[1871,1080],[1869,1088],[1866,1096],[1864,1104],[1863,1115],[1862,1125],[1862,1135],[1862,1141],[1863,1155],[1867,1166],[1871,1174],[1875,1179],[1880,1182],[1893,1188],[1904,1192],[1917,1195],[1928,1196],[1938,1197],[1950,1198],[1960,1198],[1974,1198],[1990,1196],[2007,1193],[2018,1190],[2034,1185],[2051,1183],[2064,1184],[2077,1187],[2087,1191],[2095,1198],[2099,1209],[2102,1222],[2102,1236],[2099,1252],[2094,1265],[2086,1274],[2069,1278],[2053,1279],[2035,1277],[2017,1271],[2000,1263],[1986,1258],[1972,1256],[1961,1256],[1950,1255],[1941,1254],[1932,1254],[1923,1254],[1912,1255],[1902,1256],[1892,1258],[1881,1259],[1868,1261],[1859,1263],[1846,1265]]
            
           #21march POLYGON_MAP["1"]= [[647,761],[645,774],[645,785],[645,798],[646,810],[647,821],[647,835],[649,850],[651,867],[652,883],[654,897],[655,912],[654,927],[652,940],[651,953],[652,965],[655,978],[656,988],[660,998],[667,1009],[677,1017],[693,1024],[708,1027],[726,1026],[746,1027],[763,1028],[780,1033],[794,1042],[801,1054],[804,1068],[805,1086],[804,1108],[802,1124],[799,1135],[793,1143],[786,1153],[780,1158],[773,1162],[765,1164],[760,1166],[752,1167],[746,1167],[740,1168],[733,1168],[726,1168],[722,1168],[717,1167],[711,1167],[706,1166],[701,1165],[697,1164],[691,1162],[685,1160],[679,1158],[675,1155],[671,1152],[666,1148],[663,1146],[658,1144],[652,1141],[645,1138],[639,1135],[632,1134],[626,1133],[619,1132],[612,1132],[606,1133],[601,1133],[594,1134],[588,1134],[581,1136],[574,1139],[566,1143],[559,1149],[553,1154],[549,1160],[545,1169],[543,1176],[543,1184],[543,1192],[544,1201],[545,1209],[548,1219],[552,1226],[557,1232],[562,1238],[568,1242],[575,1247],[582,1249],[592,1250],[602,1251],[609,1250],[617,1248],[624,1246],[629,1244],[634,1241],[638,1238],[643,1236],[647,1234],[651,1231],[655,1230],[663,1229],[669,1229],[679,1229],[686,1229],[700,1228],[713,1229],[726,1229],[740,1231],[749,1233],[756,1234],[760,1236],[770,1238],[779,1240],[787,1241],[794,1243],[799,1243],[805,1242],[812,1241],[821,1241],[828,1240],[836,1240],[845,1238],[853,1234],[860,1232],[867,1226],[872,1219],[875,1212],[875,1204],[874,1197],[873,1189],[872,1176],[871,1160],[872,1141],[874,1119],[877,1095],[880,1074],[884,1053],[886,1031],[886,1013],[885,1000],[882,991],[877,980],[869,969],[863,966],[856,964],[850,962],[843,960],[838,960],[830,959],[824,958],[817,958],[806,955],[796,953],[788,951],[782,948],[773,945],[766,943],[763,940],[759,938],[755,935],[750,933],[745,930],[742,926],[738,923],[736,917],[734,910],[734,904],[733,898],[732,892],[732,882],[732,870],[734,856],[735,848],[736,838],[736,829],[738,820],[739,811],[740,803],[740,796],[741,790],[741,781],[740,772],[741,763],[740,757],[739,748],[738,741],[734,734],[729,729],[722,726],[714,723],[704,722],[692,721],[683,721],[670,724],[662,729],[656,736],[651,748]]
           #21march POLYGON_MAP["2"]= [[1823,1265],[1816,1260],[1810,1253],[1807,1248],[1805,1241],[1805,1235],[1804,1227],[1804,1215],[1804,1203],[1804,1194],[1804,1183],[1805,1174],[1806,1166],[1805,1155],[1806,1143],[1806,1133],[1805,1123],[1805,1108],[1803,1098],[1801,1086],[1800,1077],[1797,1070],[1796,1063],[1796,1056],[1796,1050],[1795,1042],[1795,1034],[1796,1028],[1796,1020],[1799,1010],[1804,1005],[1810,1000],[1817,995],[1825,992],[1834,989],[1842,988],[1849,987],[1857,989],[1864,990],[1874,991],[1882,991],[1892,990],[1902,989],[1912,988],[1921,987],[1928,985],[1935,983],[1942,979],[1947,972],[1951,966],[1954,958],[1955,951],[1956,943],[1957,936],[1958,928],[1960,919],[1960,911],[1960,902],[1960,894],[1960,887],[1959,881],[1958,875],[1957,866],[1956,859],[1956,852],[1955,848],[1954,841],[1954,834],[1954,826],[1955,818],[1956,809],[1960,800],[1963,795],[1969,790],[1974,787],[1980,785],[1987,784],[1992,783],[2000,782],[2007,783],[2013,784],[2020,785],[2024,788],[2029,791],[2032,794],[2035,799],[2037,802],[2038,806],[2040,812],[2042,816],[2044,820],[2044,824],[2044,829],[2045,833],[2045,839],[2045,844],[2045,849],[2044,855],[2042,861],[2041,866],[2039,872],[2038,877],[2036,884],[2035,889],[2034,895],[2033,901],[2032,907],[2031,912],[2030,918],[2029,924],[2028,928],[2028,933],[2027,939],[2027,943],[2027,949],[2026,953],[2026,959],[2026,965],[2025,971],[2025,977],[2025,984],[2025,991],[2025,996],[2025,1003],[2026,1009],[2026,1014],[2026,1019],[2027,1027],[2027,1033],[2025,1040],[2021,1047],[2016,1053],[2009,1058],[2001,1062],[1993,1066],[1982,1068],[1975,1068],[1969,1068],[1962,1067],[1955,1067],[1951,1065],[1947,1063],[1943,1062],[1937,1061],[1931,1060],[1923,1060],[1918,1060],[1911,1059],[1903,1059],[1898,1059],[1889,1060],[1881,1063],[1876,1068],[1872,1072],[1870,1079],[1869,1083],[1868,1089],[1867,1093],[1866,1097],[1866,1103],[1865,1108],[1864,1115],[1863,1121],[1863,1127],[1863,1133],[1863,1140],[1863,1146],[1864,1152],[1864,1158],[1865,1164],[1867,1169],[1869,1176],[1873,1180],[1877,1183],[1882,1186],[1888,1188],[1894,1189],[1901,1191],[1908,1192],[1915,1194],[1922,1195],[1931,1197],[1939,1198],[1946,1199],[1953,1200],[1960,1200],[1968,1201],[1977,1201],[1985,1201],[1993,1200],[2001,1198],[2007,1197],[2015,1195],[2022,1194],[2031,1191],[2038,1190],[2046,1190],[2053,1189],[2061,1189],[2068,1190],[2075,1193],[2082,1197],[2086,1200],[2091,1205],[2094,1211],[2096,1217],[2097,1224],[2098,1231],[2097,1238],[2096,1245],[2095,1250],[2093,1255],[2090,1262],[2086,1268],[2081,1272],[2077,1274],[2070,1277],[2060,1279],[2051,1278],[2043,1279],[2035,1278],[2027,1276],[2020,1275],[2015,1273],[2008,1269],[2003,1267],[2000,1265],[1991,1264],[1985,1262],[1977,1261],[1971,1261],[1963,1259],[1956,1259],[1949,1258],[1941,1256],[1931,1256],[1923,1256],[1910,1257],[1898,1259],[1886,1259],[1871,1262],[1860,1264],[1850,1267],[1834,1267]]
           #25march POLYGON_MAP["1"]= [[650,756],[651,768],[651,781],[652,795],[653,808],[653,821],[653,835],[653,850],[653,867],[652,883],[654,900],[654,918],[654,935],[653,949],[654,965],[656,980],[660,999],[670,1012],[685,1021],[700,1026],[717,1027],[732,1027],[748,1027],[768,1029],[781,1033],[793,1038],[803,1049],[810,1062],[814,1075],[815,1088],[815,1098],[815,1108],[814,1118],[813,1127],[810,1138],[805,1147],[798,1154],[789,1161],[780,1163],[771,1166],[762,1167],[754,1168],[745,1167],[736,1167],[729,1166],[723,1166],[718,1164],[710,1162],[705,1160],[698,1159],[691,1156],[686,1154],[681,1151],[677,1149],[672,1147],[666,1144],[661,1142],[657,1140],[652,1137],[648,1135],[642,1134],[635,1132],[629,1131],[624,1129],[617,1129],[610,1130],[604,1131],[599,1131],[592,1132],[586,1132],[579,1134],[572,1137],[564,1141],[557,1147],[551,1152],[547,1158],[543,1167],[541,1174],[541,1182],[541,1190],[542,1199],[543,1207],[546,1217],[550,1224],[555,1230],[560,1236],[566,1240],[573,1245],[580,1247],[590,1248],[600,1249],[607,1248],[615,1246],[622,1244],[628,1242],[633,1240],[638,1238],[642,1235],[648,1233],[652,1231],[656,1229],[661,1228],[667,1227],[675,1226],[685,1225],[697,1225],[710,1225],[723,1225],[735,1227],[744,1228],[750,1229],[757,1230],[765,1231],[775,1232],[784,1234],[791,1235],[797,1237],[802,1239],[810,1241],[818,1241],[825,1241],[831,1241],[838,1241],[848,1239],[855,1237],[863,1233],[869,1229],[875,1220],[880,1211],[880,1201],[878,1186],[878,1166],[879,1150],[880,1131],[881,1113],[883,1093],[886,1074],[889,1051],[890,1026],[891,1010],[890,996],[886,986],[880,977],[873,973],[864,970],[857,970],[849,967],[844,966],[836,964],[829,963],[822,961],[812,960],[803,957],[795,955],[789,954],[782,952],[775,949],[772,947],[768,945],[765,943],[763,941],[761,939],[758,936],[755,933],[753,931],[748,924],[745,919],[742,910],[741,902],[742,892],[742,879],[742,869],[743,861],[744,852],[744,841],[745,830],[746,821],[746,813],[747,805],[747,794],[748,785],[748,776],[748,766],[747,756],[745,748],[744,741],[741,733],[737,726],[730,722],[720,720],[710,718],[699,717],[689,718],[679,719],[670,722],[664,727],[656,734],[653,743]]
           #25march POLYGON_MAP["2"]= [[1831,1266],[1824,1261],[1818,1254],[1816,1250],[1813,1242],[1813,1236],[1812,1228],[1812,1216],[1812,1205],[1812,1195],[1812,1184],[1813,1175],[1814,1167],[1813,1156],[1814,1144],[1814,1134],[1814,1124],[1813,1109],[1812,1099],[1809,1087],[1808,1078],[1807,1070],[1806,1063],[1806,1055],[1806,1048],[1806,1042],[1807,1034],[1808,1026],[1808,1020],[1810,1014],[1813,1007],[1818,1001],[1825,996],[1833,993],[1842,990],[1850,989],[1857,988],[1867,990],[1875,991],[1884,991],[1891,991],[1900,991],[1910,990],[1920,989],[1929,988],[1937,986],[1943,984],[1950,980],[1956,973],[1959,967],[1962,959],[1963,952],[1964,944],[1966,937],[1967,929],[1968,920],[1968,912],[1968,903],[1968,896],[1968,888],[1968,882],[1969,874],[1969,865],[1968,859],[1966,852],[1964,846],[1964,841],[1963,833],[1962,827],[1963,819],[1965,810],[1968,801],[1972,796],[1977,791],[1982,788],[1989,786],[1995,785],[2000,784],[2008,783],[2015,784],[2022,785],[2028,786],[2034,788],[2039,791],[2042,795],[2045,799],[2047,803],[2049,808],[2052,813],[2053,818],[2055,822],[2056,826],[2056,831],[2056,836],[2055,841],[2056,846],[2055,852],[2053,857],[2052,863],[2051,868],[2050,874],[2048,879],[2047,885],[2045,891],[2044,896],[2042,902],[2040,908],[2039,913],[2038,920],[2037,925],[2037,929],[2036,934],[2036,938],[2036,943],[2036,948],[2036,954],[2035,960],[2034,966],[2035,972],[2035,978],[2035,984],[2035,990],[2035,995],[2036,1001],[2036,1008],[2036,1014],[2035,1020],[2035,1028],[2035,1034],[2033,1041],[2029,1048],[2024,1054],[2018,1059],[2009,1064],[2001,1067],[1991,1069],[1983,1069],[1977,1069],[1970,1068],[1964,1068],[1959,1066],[1955,1064],[1951,1063],[1945,1062],[1939,1061],[1932,1061],[1926,1061],[1921,1061],[1913,1060],[1905,1061],[1897,1062],[1889,1065],[1884,1069],[1881,1074],[1878,1080],[1877,1084],[1876,1090],[1875,1094],[1874,1098],[1874,1104],[1873,1109],[1872,1116],[1871,1122],[1871,1128],[1871,1134],[1871,1141],[1871,1147],[1872,1153],[1873,1159],[1874,1165],[1875,1170],[1877,1177],[1881,1181],[1885,1184],[1890,1187],[1896,1189],[1902,1190],[1909,1192],[1916,1193],[1924,1195],[1931,1196],[1939,1198],[1947,1199],[1954,1200],[1962,1201],[1968,1201],[1976,1202],[1985,1202],[1993,1202],[2001,1201],[2010,1199],[2015,1198],[2023,1196],[2030,1195],[2039,1192],[2046,1191],[2054,1191],[2062,1190],[2069,1190],[2076,1191],[2083,1194],[2090,1198],[2094,1201],[2099,1206],[2102,1212],[2104,1218],[2105,1225],[2106,1232],[2105,1239],[2104,1246],[2103,1251],[2102,1256],[2099,1263],[2095,1269],[2089,1273],[2085,1275],[2078,1278],[2069,1280],[2059,1280],[2051,1280],[2043,1279],[2036,1277],[2029,1276],[2023,1274],[2017,1270],[2011,1268],[2006,1266],[1999,1265],[1993,1264],[1986,1263],[1980,1263],[1973,1262],[1965,1261],[1958,1261],[1950,1260],[1942,1259],[1931,1259],[1918,1260],[1906,1260],[1893,1262],[1881,1265],[1869,1267],[1858,1268],[1842,1268]]
            
            POLYGON_MAP["1"]= [[591,1126],[580,1131],[572,1136],[563,1144],[555,1152],[548,1161],[544,1171],[543,1185],[543,1200],[545,1210],[549,1223],[559,1234],[572,1243],[589,1250],[604,1253],[623,1252],[637,1252],[651,1248],[665,1242],[678,1237],[689,1232],[698,1229],[709,1226],[720,1224],[730,1226],[743,1227],[752,1228],[761,1230],[770,1231],[777,1233],[785,1233],[796,1235],[805,1238],[815,1241],[827,1242],[837,1242],[846,1242],[858,1240],[868,1235],[877,1229],[883,1222],[886,1214],[888,1200],[888,1185],[889,1170],[889,1155],[890,1140],[890,1126],[890,1112],[893,1097],[895,1087],[897,1076],[898,1064],[900,1050],[901,1036],[901,1023],[901,1009],[900,993],[895,980],[888,968],[878,963],[863,957],[844,954],[826,952],[815,950],[802,946],[789,942],[777,936],[770,929],[765,922],[760,915],[757,906],[756,899],[755,889],[756,876],[758,862],[759,849],[760,834],[761,819],[762,805],[762,790],[763,777],[762,764],[762,752],[760,740],[756,730],[749,721],[739,715],[725,709],[707,707],[687,708],[671,713],[661,721],[653,733],[651,748],[652,764],[652,780],[653,796],[653,810],[654,824],[655,835],[656,846],[657,857],[657,869],[659,880],[659,892],[660,904],[661,916],[661,929],[660,944],[661,963],[663,975],[665,986],[669,996],[674,1006],[686,1016],[702,1025],[720,1027],[735,1027],[751,1026],[762,1026],[775,1029],[786,1032],[797,1038],[804,1048],[812,1060],[813,1070],[816,1083],[816,1093],[816,1103],[816,1111],[815,1119],[811,1132],[806,1145],[796,1155],[784,1158],[769,1159],[754,1159],[735,1157],[723,1155],[710,1151],[699,1145],[690,1142],[681,1137],[668,1132],[657,1128],[641,1122],[627,1121],[615,1121],[602,1123]]
            POLYGON_MAP["2"]= [[1837,1266],[1826,1261],[1817,1253],[1814,1244],[1812,1235],[1811,1225],[1809,1214],[1809,1206],[1808,1196],[1808,1188],[1809,1181],[1810,1174],[1810,1165],[1810,1155],[1811,1147],[1810,1138],[1810,1130],[1810,1121],[1810,1111],[1808,1100],[1808,1092],[1806,1081],[1805,1067],[1804,1058],[1804,1046],[1803,1034],[1804,1020],[1807,1008],[1812,1000],[1819,994],[1827,988],[1837,985],[1852,984],[1866,983],[1882,984],[1902,983],[1918,981],[1934,980],[1950,974],[1962,966],[1968,956],[1970,942],[1972,928],[1973,916],[1973,903],[1974,891],[1974,880],[1972,869],[1971,861],[1970,852],[1969,842],[1969,825],[1970,811],[1973,799],[1977,788],[1986,777],[1999,772],[2016,770],[2035,771],[2050,776],[2060,785],[2067,795],[2071,812],[2071,825],[2072,839],[2070,852],[2068,863],[2066,875],[2064,883],[2061,896],[2058,907],[2054,919],[2050,930],[2048,944],[2049,957],[2050,970],[2049,982],[2049,998],[2049,1012],[2046,1022],[2044,1035],[2037,1048],[2025,1060],[2006,1069],[1986,1070],[1967,1068],[1952,1064],[1937,1062],[1917,1061],[1905,1063],[1896,1066],[1890,1071],[1884,1079],[1882,1087],[1880,1095],[1879,1105],[1879,1116],[1877,1124],[1878,1133],[1878,1140],[1879,1153],[1882,1163],[1887,1172],[1891,1177],[1895,1180],[1908,1186],[1919,1191],[1933,1193],[1944,1194],[1954,1195],[1965,1196],[1976,1196],[1991,1196],[2005,1195],[2022,1191],[2033,1188],[2049,1183],[2068,1182],[2090,1184],[2104,1192],[2114,1207],[2117,1224],[2117,1243],[2112,1260],[2106,1273],[2095,1279],[2078,1283],[2060,1285],[2048,1282],[2039,1279],[2030,1275],[2021,1271],[2011,1264],[2001,1261],[1988,1260],[1978,1259],[1968,1257],[1957,1256],[1948,1255],[1937,1256],[1927,1256],[1917,1257],[1904,1260],[1890,1263],[1877,1265],[1863,1267],[1850,1268]]
            

            LABEL_LIST_MAP = {}
            ERROR_LIST_MAP = {}
            
            Engine_no, Position,IS_PROCESS,ImageLink, ImageLink_2 = getInferenceTrigger()
            # Engine_no = "VK YJP4L741378"
            # IS_PROCESS = 1
            # Position = 1
            # ImageLink = "c:/Users/Admin/Documents/IMAGE_SAVE/IMG/IMG_1.jpg"
            # ImageLink_2 = "/home/viks/VIKS/CODE/PROJECT_ALGORITHAM/NEW_EGAL_PROJECT/CAM_CAP_HLA/3_JAN/IMG/CAM2_3.jpg"
        
            class_names_to_check_img3 = ["ok_sealant_2",  "ok_sealant_1"]
            STATUS_FINAL = "NOT OK"
            class_check_cam1 = False
            
            
            if Position== 1 and IS_PROCESS == 1:
                original_image = cv2.imread(ImageLink)
                STATUS = "NOT OK"
                class_names_to_check_img3 = ["ok_sealant_2",  "ok_sealant_1"]
                STATUS_FINAL = "NOT OK"
                SEALNT_1_STATUS = "NOT OK"
                SEALNT_2_STATUS = "NOT OK"
                original_image_real = cv2.imread(ImageLink)
                
                OBJECT_LIST = maskRCNNObj.run_inference_sea(ImageLink)
                cam1_DefectStatus = False
                if OBJECT_LIST == []:
                    #inseryData = True
                    STATUS = "NOT OK"
                    inf_img = f"IMG_{Position}.jpg"
                    TodaysDate = datetime.datetime.now().strftime('%Y_%m_%d')
                    engine_folder_path = os.path.join(SAVED_FOLDER_PATH,str(TodaysDate), str(Engine_no))
                    os.makedirs(engine_folder_path, exist_ok=True)
                    processed_image_path = os.path.join(engine_folder_path, inf_img)
                    # processed_image_path.replace()
                    processed_image_path=processed_image_path.replace("\\",'/')
                    cv2.imwrite(processed_image_path, original_image)

                    current_datetime = datetime.datetime.now()
                    formatted_dateime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
                    # # Generate image paths including the folder structure
                    cam4_image_path = os.path.join(engine_folder_path,formatted_dateime+f"_IMG_{Position}.jpg")
                    cv2.imwrite(cam4_image_path, original_image)


                    IS_PROCESS_INF,STATUS_FINAL = insertDataIndotprocessing_table(Engine_no, STATUS_FINAL, ImageLink, cam4_image_path,"","")
                   # if IS_PROCESS_INF == 2 :
                    update_inference_trigger(IS_PROCESS_INF,STATUS_FINAL)
                    class_check_cam1 = False


                #print(OBJECT_LIST)
                for index, (key, value) in enumerate(POSITION_WISE_DETECTION_POSITION.items()):
                    ''' Create a polygon object '''
                    polygon = Polygon(value)
                    for item in OBJECT_LIST:
                        labelname = item[0]
                        if "hole" in labelname or "base" in labelname:
                            continue
                        cx = item[6]
                        cy = item[7]
                        ''' Point outside '''
                        point = Point(cx, cy)
                        # Check if the point lies inside the polygon
                        if polygon.contains(point):
                            LABEL_LIST_MAP[key] = item
                        else:
                            continue

                #===========================================================================================#        
                for index, (key, value) in enumerate(POLYGON_MAP.items()):
                    exsitingPoints = []
                    minX,minY,maxX,maxY = getMinMaxValues(value)
                    if key in LABEL_LIST_MAP.keys():
                        drawPolygonPoints(original_image,value)
                        labelItems = LABEL_LIST_MAP.get(key)
                        # minY = labelItems[1]
                        # maxY = labelItems[2]
                        polygon = Polygon(value)
                        mask_points = labelItems[8]
                        for points in mask_points:
                            px = points[1]
                            py = points[0]
                            
                            if py > minY and py < maxY:
                                
                                ''' Point outside '''
                                point = Point(px, py)
                                # Check if the point lies inside the polygon
                                if polygon.contains(point):
                                    LABEL_LIST_MAP[key] = item
                                    #cam1_DefectStatus = False
                                else:
                                    if key in ERROR_LIST_MAP.keys():
                                        exsitingPoints = ERROR_LIST_MAP.get(key)
                                        exsitingPoints.append([px,py])
                                        ERROR_LIST_MAP[key] = exsitingPoints
                                    else:
                                        ERROR_LIST_MAP[key] = [[px,px]]
                                    cv2.circle(original_image, (px, py), radius=1, color=(0,0,255), thickness=7)
                                    cam1_DefectStatus = True
                            else:
                                pass

                #  original_image = cv2.imread(ImageLink)
                color = (0, 0, 0)
                NOT_OK_FLAG= False
                if all(any(class_name in sublist for sublist in OBJECT_LIST) for class_name in class_names_to_check_img3):
                    print(" OK")
                    class_check_cam1 = True
                else:
                    print("NOT OK")
                    class_check_cam1 = False


                for item in OBJECT_LIST:
                    xmin, ymin, xmax, ymax = item[1:5]
                    if item[0] == "selant_not_ok_1" or item[0] == "selant_not_ok_2" or item[0] == "dry_sealant_1" or item[0] == "dry_sealant_2" or item[0] == "NOT_OK_sealant_1" or item[0] == "NOT_OK_sealant_2" or item[0] == "sealant_2_cut" or item[0] == "sealant_1_cut" or item[0] == "cut_sealant_1" or item[0] == "cut_sealant_2" :
                        NOT_OK_FLAG= True
                        STATUS = "NOT OK"
                        color = (0, 0, 255)
                        cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 6)
                        label_text = f"{item[0]}: {item[5]:.3f}"
                        cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)


                    else:
                        NOT_OK_FLAG = False
                        STATUS = "OK"
                        color = (0, 255, 0)
                    if NOT_OK_FLAG == True or class_check_cam1 == False or cam1_DefectStatus == True:
                        color = (0, 0, 255)
                        STATUS_FINAL = "NOT OK"

                    elif NOT_OK_FLAG == False and class_check_cam1 == True and cam1_DefectStatus == False:
                        color = (0, 255, 0)
                        STATUS_FINAL = "OK"

                    # cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, 3)
                    # label_text = f"{item[0]}: {item[5]:.2f}"
                    # cv2.putText(original_image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)
                current_datetime = datetime.datetime.now()
                formatted_dateime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")

                inf_img = f"IMG_Real_{Position}.jpg"
                TodaysDate = datetime.datetime.now().strftime('%Y_%m_%d')
                engine_folder_path = os.path.join(SAVED_FOLDER_PATH,str(TodaysDate), str(Engine_no))
                os.makedirs(engine_folder_path, exist_ok=True)
                processed_image_path = os.path.join(engine_folder_path, inf_img)
                # processed_image_path.replace()
                processed_image_path=processed_image_path.replace("\\",'/')
                cv2.imwrite(processed_image_path, original_image_real)

               
                # # Generate image paths including the folder structure
                cam4_image_path = os.path.join(engine_folder_path,formatted_dateime+f"_IMG_{Position}.jpg")
                cv2.imwrite(cam4_image_path, original_image)
                #cv2.imwrite(cam4_image_path, original_image_real)


                IS_PROCESS_INF,STATUS_FINAL = insertDataIndotprocessing_table(Engine_no, STATUS_FINAL, ImageLink, cam4_image_path,"","")
                start_pdf(STATUS_FINAL, Engine_no,engine_folder_path)
                if IS_PROCESS_INF == 2 :
                    update_inference_trigger(IS_PROCESS_INF,STATUS_FINAL)
                    
            elif Position in [2,3,4,5,6,7,8,9,10,11] and IS_PROCESS == 1:
                Engine_no, Position,IS_PROCESS,ImageLink, ImageLink_2 = getInferenceTrigger()             
                #Position_11 = Position[0]
                if Position in [11]:
                    STATUS, defect_list, ok_list = check_for_defect(maskRCNNObj,ImageLink,ImageLink_2,Engine_no,Position)

                elif ImageLink == '' or ImageLink_2 == '':
                    print("ImageLink is========== :",ImageLink)
                    print("ImageLink_2 is======== :",ImageLink_2)
                   # pass
                else:
                    print("ImageLink is========== :",ImageLink)
                    print("ImageLink_2 is======== :",ImageLink_2)
                    if ImageLink != '' and ImageLink_2 != '':             
                        STATUS, defect_list, ok_list = check_for_defect(maskRCNNObj,ImageLink,ImageLink_2,Engine_no,Position)
                        print("ALGO Postion is",Position)
            else:
               
                print("ALGO Postion is",Position)
                time.sleep(0.1)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        logger.debug(f"Error in run(): {e}")

if __name__ == "__main__":
    maskRCNNObj = MaskRCNN_Mahindra()
    run(maskRCNNObj)

