import json

with open("/home/insightzz-01/Insightzz/Vikram/CoalIndiaLimited/20220926_labeled_coalindia/all_data_1/") as data_file:
    data = json.load(data_file)

for element in data:
    if "no_plate" in element:
        del element["no_plate"]

with open("/home/insightzz-01/Insightzz/Vikram/CoalIndiaLimited/20220926_labeled_coalindia/output/", 'w') as data_file:
    data = json.dump(data, data_file)
