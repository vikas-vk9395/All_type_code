import os
import datetime

folder_path = "/media/viks/VIKS/OLD_LINE_PISTON_ARROW_LABELING_DATA_17_JAN/2024_01_17/"

dir_list = os.listdir(folder_path)
dir_list.sort()
for directory in dir_list:
    img_list = os.listdir(folder_path+directory)
    img_list.sort()
    for img in img_list:
        if ".jpg" in img:
            current_filename = folder_path+directory+"/"+img
            print(current_filename)
            name = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')
            new_file_name = folder_path+directory+"/"+img.split(".")[0]+"_"+name+".jpg"
            print(new_file_name)
            os.rename(current_filename, new_file_name)
        else:
            print(img)
