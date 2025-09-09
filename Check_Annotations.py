import os
import shutil

# Define the folder containing your images
source_folder = '/path/to/source/folder'

# Define the destination folder where you want to move the images
destination_folder = '/path/to/destination/folder'

# Create the destination folder if it does not exist
if not os.path.exists(destination_folder):
    os.makedirs(destination_folder)

# List all files in the source folder
files = os.listdir(source_folder)

# Iterate over each file
for file in files:
    # Check if the file has no usable annotations
    # For example, you might check if there is a corresponding annotation file
    annotation_file = os.path.join(source_folder, file.replace('.jpg', '.json'))  # Assuming JSON annotations
    if not os.path.exists(annotation_file):
        # If the annotation file does not exist, move the image file to the destination folder
        source_file_path = os.path.join(source_folder, file)
        destination_file_path = os.path.join(destination_folder, file)
        shutil.move(source_file_path, destination_file_path)
        print(f"Moved {file} to {destination_folder}.")

print("Image movement process completed.")
