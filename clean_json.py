import os
image_path = "/home/server1/Insightzz/Rupali/COAL/coal_data_18_Mar/"
discarded_path = "/home/server1/Insightzz/Rupali/code/discarded/"

img_list = os.listdir(image_path)
img_list.sort()
for f in img_list:
    jpg_count=0
    json_count=0
    if ".jpg" in str(f):
        name_fl = f[:(len(f)-4)]
        jpg_name = name_fl+'.jpg'
        json_name = name_fl+'.json'
        jpg_count=img_list.count(jpg_name)
        json_count=img_list.count(json_name)
        if jpg_count==1 and json_count==1:
            continue
        else:
            file_pth=image_path+f        
            file_opth=discarded_path+f
            os.rename(file_pth,file_opth)        
    elif ".json" in str(f):
        name_fl = f[:(len(f)-5)]
        jpg_name = name_fl+'.jpg'
        json_name = name_fl+'.json'
        jpg_count=img_list.count(jpg_name)
        json_count=img_list.count(json_name)
        if jpg_count==1 and json_count==1:
            continue
        else:
            file_pth=image_path+f        
            file_opth=discarded_path+f
            os.rename(file_pth,file_opth)        
