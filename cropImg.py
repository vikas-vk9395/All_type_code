import cv2
import os

# Input image path
link = '/home/viks/Documents/CAM1_DEFECT.jpg'
# Output image path
PIC_NAME_PATH = '/home/viks/Documents/CAM1_DEFECT_CROPPED.jpg'

# Check if the image exists
if os.path.exists(link):
    # Load the image
    image = cv2.imread(link)

    if image is None:
        print("Failed to load image. Please check the file format or path.")
    else:
        # Get image dimensions
        height, width, _ = image.shape

        # Define cropping parameters
        xmin = 350
        xmax = 1950 if width > 1950 else width
        ymin = 270
        ymax = 1220 if height > 1220 else height

        # Ensure valid cropping range
        if xmin < 0 or ymin < 0 or xmax > width or ymax > height:
            print("Cropping dimensions are out of bounds.")
        else:
            # Perform cropping
            cropped_image = image[ymin:ymax, xmin:xmax]

            # Save the cropped image
            cv2.imwrite(PIC_NAME_PATH, cropped_image)
            print(f"Cropped image saved at: {PIC_NAME_PATH}")

            # # Display the cropped image for verification (optional)
            # cv2.imshow('Cropped Image', cropped_image)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()
else:
    print(f"Image not found: {link}")
