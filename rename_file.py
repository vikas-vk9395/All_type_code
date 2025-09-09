import os
import datetime
import glob

img_dir = "test_img"
Current_Date =  datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f')
jpg_fls=glob.glob(os.path.join(img_dir,"*.jpg"))
for jpg_fl in jpg_fls:
    print("XML file:",jpg_fl.split("/")[1].split(".")[0])
    fname = jpg_fl.split("/")[1].split(".")[0]
    os.rename(jpg_fl,img_dir+"/"+fname+'_' + str(Current_Date) + '.jpg')
