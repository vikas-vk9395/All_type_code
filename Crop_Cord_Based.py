import os
import cv2
import datetime


# Define the paths
file_dir = '/home/vikram/Insightzz/eclipse-j2ee-workspace/TestingProject/ImageCropping/Sealent/Input/'
output_dir = '/home/vikram/Insightzz/eclipse-j2ee-workspace/TestingProject/ImageCropping/Sealent/Output/'

w = 192
h = 256

w1 = 128
h1 = 128

IMAGE_CROP_COORDINATES = [
    [80,60,w,h],[106,172,w,h],[126,515,w,h],[143,690,w,h],
    [558,67,w,h],[490,200,w,h],[481,425,w,h],[530,530,w,h],[568,700,w,h],
    [287,181,w1,h1],[275,307,w1,h1],[284,432,w1,h1],[318,560,w1,h1]
    ]

# Directories for cropped images
# SealentDir = os.path.join(output_dir, "SealentDir")
# os.makedirs(SealentDir, exist_ok=True)


def cropImageAndSave(img, xmin, xmax, ymin, ymax):
    """Crop the image based on bounding box coordinates."""
    # print(f"Cropping image with coordinates: xmin={xmin}, xmax={xmax}, ymin={ymin}, ymax={ymax}")
    cropped = img[ymin:ymax, xmin:xmax]
    # print(f"Cropped image shape: {cropped.shape}")
    return cropped

def mainFunction():
    try:
        for file_name in os.listdir(file_dir):
            if file_name.endswith('.jpg'):
                imagePath = os.path.join(file_dir, file_name)
                image = cv2.imread(imagePath)
                
                for item in IMAGE_CROP_COORDINATES:
                    xmin, ymin, width, height = item
                    xmax = xmin + width
                    ymax = ymin + height
                    
                    cropImg = cropImageAndSave(image, xmin, xmax, ymin, ymax)
                    
                    CROP_IMG_FILENAME = os.path.join(output_dir, f"CROP_IMAGE_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')}") + ".jpg"
                    cv2.imwrite(CROP_IMG_FILENAME, cropImg)
                
                
                
    except Exception as e:
        print(f"Exception is : {e}")

if __name__=="__main__":
    mainFunction()
    print("Done")