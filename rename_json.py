import os
import json

image_path = "/home/viks/VIKS/CODE/PROJECT_DATA/RAWAN/Labeled/25_Model_Data/"
#print(image_path.split("/")[-2]+"_")
img_list = os.listdir(image_path)
img_list.sort()
for f in img_list:
    print("f is :",f)
    if ".json" in str(f):
        new_name = image_path.split("/")[-2]+"_"+f[:-5]
        #print(new_name)
        with open(image_path + f, 'r') as f1:
            d = json.load(f1)
            print(d['imagePath'])
            d['imagePath'] = d['imagePath'].replace(f[:-5]+".jpg",new_name+".jpg")
        with open(image_path + f, 'w') as f2:
            json.dump(d, f2)
        os.rename(image_path+f[:-5]+".json",image_path+new_name+".json")
        os.rename(image_path+f[:-5]+".jpg",image_path+new_name+".jpg")

