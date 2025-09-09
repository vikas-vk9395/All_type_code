# import os
# import datetime

# folder_path = "/home/viks/VIKS/CODE/IMG/"

# dir_list = os.listdir(folder_path)
# dir_list.sort()
# for directory in dir_list:
#     img_list = os.listdir(folder_path+directory)
#     img_list.sort()
#     for img in img_list:
#         if ".jpg" in img:
#             current_filename = folder_path+directory+"/"+img
#             print(current_filename)
#             name = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')
#             new_file_name = folder_path+directory+"/"+img.split(".")[0]+"_"+name+".jpg"
#             print(new_file_name)
#             os.rename(current_filename, new_file_name)
#         else:
#             print(img)

import os
import datetime

def get_all_subdirectories(directory):
    subdirs = []
    for root, dirs, files in os.walk(directory):
        for d in dirs:
            subdirs.append(os.path.join(root, d))
    return subdirs

def rename_jpg_files_in_directory(directory):
    img_list = os.listdir(directory)
    img_list.sort()
    for img in img_list:
        if img.lower().endswith(".jpg"):
            current_filename = os.path.join(directory, img)
            print(f"Current filename: {current_filename}")
            name = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')
            new_file_name = os.path.join(directory, f"{img.split('.')[0]}_{name}.jpg")
            print(f"New filename: {new_file_name}")
            os.rename(current_filename, new_file_name)
        else:
            print(f"Not a .jpg file: {img}")

# Specify the root folder path
folder_path = "/home/viks/VIKS/CODE/PROJECT_ALGORITHAM/ROKAM/22_june_UpSleev_ND/"

# Get a list of all subdirectories
all_subdirs = get_all_subdirectories(folder_path)
all_subdirs.sort()

# Get the last three subdirectories
last_three_subdirs = all_subdirs[+4:]

# Rename .jpg files in each of the last three subdirectories
for subdir in last_three_subdirs:
    rename_jpg_files_in_directory(subdir)
