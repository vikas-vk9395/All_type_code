import cv2
import os
import numpy as np
import logging
import time
import datetime
import glob
import json

os.environ['CUDA_VISIBLE_DEVICES']='0'
detection_graph  = None
sess = None

#for maskrcnn
# import some common detectron2 utilities
from detectron2.utils.logger import setup_logger
setup_logger()
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog, DatasetCatalog
from detectron2.structures import BoxMode
from detectron2.engine import DefaultTrainer
from detectron2.utils.visualizer import ColorMode

img_dir="/home/insightzz-03/insightzz/HARSHAD/inference_crop_V3/testdata/ZS_Data/"
dest_dir = "/home/insightzz-03/insightzz/HARSHAD/inference_crop_V3/tested/"
# img_dir="/home/pratik/insightzz/project/NESTLE_GOA/frame_capture/data/test/"
# dest_dir = "/home/pratik/insightzz/project/NESTLE_GOA/frame_capture/data/tested/"

#MASKRCNN PATHS 
mask_model_path = "/home/insightzz-03/insightzz/mahesh/igatmahindra_engineinspection/All_Models_5dec/ZS_Model/ZS_28NOV_MODEL/"
CONFIG_PATH = "/home/insightzz-03/insightzz/PROJECTS/configs/COCO-InstanceSegmentation/mask_rcnn_R_101_FPN_3x.yaml"
json_path = "/home/insightzz-03/insightzz/mahesh/igatmahindra_engineinspection/All_Models_5dec/ZS_Model/ZS_28NOV.json"

def __loadLablMap__():
    #load labelmap
    with open(json_path,"r") as fl:
        labelMap=json.load(fl)
    return labelMap

labelMap = __loadLablMap__()
label_classes=list(labelMap.values())

class maskRCNN_Railway:
    def __init__(self):
        global mask_model_path

        self.predictor=None
        self.mrcnn_config_fl=CONFIG_PATH
        self.mrcnn_model_loc= mask_model_path
        self.mrcnn_model_fl="model_final.pth"
        self.detection_thresh=0.5
        self.register_modeldatasets()

    def register_modeldatasets(self):
        d="test"
        MetadataCatalog.get("brake_" + d).set(thing_classes=label_classes)

        self.railway_metadata = MetadataCatalog.get("brake_test")
        #Start config for inf
        cfg = get_cfg()
        cfg.merge_from_file(self.mrcnn_config_fl)
        #cfg.merge_from_list(["MODEL.DEVICE","cpu"]) #cpu
        cfg.MODEL.ROI_HEADS.NUM_CLASSES =98 # only has one class (ballon)
        cfg.OUTPUT_DIR=self.mrcnn_model_loc
        cfg.MODEL.WEIGHTS =os.path.join(cfg.OUTPUT_DIR,self.mrcnn_model_fl)
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = self.detection_thresh
        self.predictor = DefaultPredictor(cfg)

    def run_inference(self,img):
        output = self.predictor(img)
        predictions=output["instances"].to("cpu")
        classes = predictions.pred_classes.numpy()

        #for counting number of items
        class_list = []
        for i in classes:
            class_list.append(self.railway_metadata.get("thing_classes")[i])
        class_dict = {} 
        for item in class_list: 
            if (item in class_dict): 
                class_dict[item] += 1
            else: 
                class_dict[item] = 1        
        
        boxes_surface = output["instances"].pred_boxes.tensor.to("cpu").numpy()
        pred_class_surface = output["instances"].pred_classes.to("cpu").numpy()
        scores_surface = output["instances"].scores.to("cpu").numpy()
        mask_surface = output['instances'].pred_masks.to("cpu").numpy()
        labellist = []
        for i,box in enumerate(boxes_surface):
            if scores_surface[i] > 0.5:
                score = scores_surface[i]
                box = boxes_surface[i]
                ymin = int(box[1])
                xmin = int(box[0])
                ymax = int(box[3])
                xmax = int(box[2])
                class_name = self.railway_metadata.get("thing_classes")[pred_class_surface[i]]
                
                labellistsmall = []
                labellistsmall.append(score)
                labellistsmall.append(ymin)
                labellistsmall.append(ymax)
                labellistsmall.append(xmin)
                labellistsmall.append(xmax) 
                labellistsmall.append(class_name)
                labellist.append(labellistsmall)
                #if class_name == "gauge_b" or class_name == "gauge_s":
                    #cv2.putText(img, class_name, (xmin,ymin-15), cv2.FONT_HERSHEY_SIMPLEX, 
                                      # 1, (255, 0, 0), 1, cv2.LINE_AA) 
                    #cv2.rectangle(img, (xmin,ymin), (xmax,ymax), (0,0,255),2)
                if class_name == "oil_inlet_washer_top_area":
                    crop_dest_path = "/home/insightzz-03/insightzz/HARSHAD/inference_crop_V3/oil_inlet_washer_top_area/"
                    #xmax=xmax+10
                    #roi_top
                    #ymin = 600 #1734
                    #xmin = 0 #1125
                    #ymax = 1000#1900
                    #xmax = 290 #1400
                    crop_img =img[ymin:ymax, xmin:xmax]  
                    curr_file_name ="oil_inlet_washer_top_area_"+ datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")+".jpg"
                    cv2.imwrite(crop_dest_path+curr_file_name, crop_img)
                #if class_name == "ocfm_benzo_area":
                    #crop_dest_path = "/home/insightzz-03/insightzz/HARSHAD/inference_crop_V3/benzo_washer/"
                    #crop_img =img[ymin:ymax, xmin:xmax]  
                    #curr_file_name ="OCFM_benzo_"+ datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")+".jpg"
                    #cv2.imwrite(crop_dest_path+curr_file_name, crop_img)
        #print(labellist)
        
        # boxes=predictions.pred_boxes.tensor.numpy()[0]
        # masks=None
        # mask_img=np.full((img.shape[0],img.shape[1]),0,np.uint8)
        # if predictions.has("pred_masks"):
        #         masks = np.asarray(predictions.pred_masks)
                
        # mdata=(masks[0]*mask_img)
        # out_img=img.copy()
        # visualizer = Visualizer(out_img[:, :, ::-1], metadata=self.railway_metadata, scale=1, instance_mode=ColorMode.IMAGE)
        # out_img = visualizer.draw_instance_predictions(output["instances"].to("cpu"))
        # print(type(out_img.get_image()[:, :, ::-1]))
        # print(type(img))
        # #return out_img.get_image()[:, :, ::-1], class_dict
        # img = np.array(out_img.get_image()[:, :, ::-1])
        return img, labellist

def draw_rectangle(img_rd, class_name, ymin, ymax, xmin, xmax, color, score):
    class_name = class_name+" "+str(score)[:4] 
    fontsize_x = cv2.getTextSize(class_name, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 1)[0][0]
    fontsize_y = cv2.getTextSize(class_name, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 1)[0][1]

    #for label rectangle
    cv2.rectangle(img_rd, (xmin,ymin), (xmax,ymax), (int(color[0]),int(color[1]),int(color[2])),2)   

    #for defect text
    cv2.rectangle(img_rd, (xmin,ymin), ((xmin+fontsize_x),int(ymin-25)), (int(color[0]),int(color[1]), int(color[2])),-1)
    cv2.putText(img_rd, class_name,(xmin,int(ymin)) ,cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0,0,0), 2, cv2.FILLED)

    return img_rd


def main(img_dir):
    global model_name, label_map, num_classes
    mask_obj = maskRCNN_Railway()    

    dir_list = os.listdir(img_dir)
    dir_list.sort()
    for directory in dir_list:
        img_list = os.listdir(img_dir+directory)
        img_list.sort()
        for img in img_list:
            print(img_dir+directory+"/"+img)
            im = cv2.imread(img_dir+directory+"/"+img)
            imreal = im.copy()
            try:
                im, labellist = mask_obj.run_inference(im)                
            except Exception as e:
                print(e)

            dest_path = dest_dir+directory
            if os.path.isdir(dest_path) is not True:
                os.makedirs(dest_path)
            # im = cv2.hconcat([im, imreal])
            # cv2.imwrite(dest_path+"/"+img, im)
            #im1 = cv2.resize(im, (int(im.shape[1] * 20 / 100), int(im.shape[0] * 20 / 100)))
            #cv2.imshow("imgrd", im1)
            #if cv2.waitKey(1) & 0xFF == ord('q'):
            #    break


if __name__ == '__main__':
    main(img_dir)
