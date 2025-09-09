import os
import shutil
import json

def copyFilesWithClassName(source_folder, destination_folder, class_name):
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if file.endswith(".json"):
                # Read the JSON file
                json_path = os.path.join(root, file)
                with open(json_path, 'r') as json_file:
                    json_data = json.load(json_file)
                
                # Check if the JSON data contains the specified class name
                for shape in json_data['shapes']:
                    if shape['label'] == class_name:
                        # If the class name matches, copy both JSON and image files
                        image_name = file.replace(".json", ".jpg")
                        image_path = os.path.join(root, image_name)
                        if os.path.exists(image_path):
                            # Copy the JSON file to the destination folder
                            shutil.copy2(json_path, destination_folder)

                            # Copy the associated image to the destination folder
                            destination_image_path = os.path.join(destination_folder, image_name)
                            shutil.copy2(image_path, destination_image_path)

source_folder = "/home/viks/Desktop/MAIN_OIL_SUM_IMG/"
destination_folder = "/home/viks/Desktop/"
class_name_to_copy = "curve_7"

copyFilesWithClassName(source_folder, destination_folder, class_name_to_copy)

