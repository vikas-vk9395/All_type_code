import cv2

# Load the image
file_dir = "/home/viks/Documents/INFERENCE/12_HLA/TESTED/4_cy/POS_1.jpg"
image = cv2.imread(file_dir)

# Rotate the image 90 degrees counterclockwise
rotated_image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

# Save or display the rotated image
rotated_file = "/home/viks/Documents/INFERENCE/12_HLA/TESTED/4_cy/IMG_rotated_90.jpg"
cv2.imwrite(rotated_file, rotated_image)

# Show the rotated image (optional)
cv2.imshow("Rotated Image", rotated_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
