import json
import os

def changeJsonLabelName():
    image_path = "/home/viks/VIKS/CODE/PROJECT_DATA/RAWAN/27_Mar/Remening/"
    
    img_list = os.listdir(image_path)
    img_list.sort()
    for f in img_list:
        #print(f)
        if ".json" in str(f):
            with open(image_path + f, 'r') as f1:
                d = json.load(f1)
                for i,j in enumerate(d['shapes']):
                    if len(d['shapes'][i]['label']) == 0:
                        os.remove(image_path + f)
                        continue
                    #d['shapes'][i]['label'] = d['shapes'][i]['label'].replace("guage_s", "gauge_s")
                    d['shapes'][i]['label'] = d['shapes'][i]['label'].replace("false_stone", "stone")
                    #d['shapes'][i]['label'] = d['shapes'][i]['label'].replace("egr_temperature_sensor", "temperature_sensor")
                    print(i)
                    #d['shapes'][i]['label'] = d['shapes'][i]['label'].replace("others", "gauge_s")
                    #print(d['shapes'][i]['label'])
            with open(image_path + f, 'w') as f2:
                json.dump(d, f2)
changeJsonLabelName()
