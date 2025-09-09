import os
import json

image_path = "/home/server1/Insightzz/Rupali/COAL/coal_data_18_Mar/"


img_list = os.listdir(image_path)
img_list.sort()
class_list = []
class_dict = {} 
for f in img_list:
    
    if ".json" in str(f):
        with open(image_path + f, 'r') as f1:
            d = json.load(f1)
            for i,j in enumerate(d['shapes']):
                class_list.append(d['shapes'][i]['label'])

for item in class_list: 
    if (item in class_dict): 
        class_dict[item] += 1
    else: 
        class_dict[item] = 1        
label_dict={}
for n,i in enumerate(class_dict):
    print(str(n)+" "+str(i)+" : "+str(class_dict[i]))
    label_dict[str(n)] = str(i)

print(label_dict)
