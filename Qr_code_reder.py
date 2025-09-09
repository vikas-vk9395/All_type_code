import cv2
import pytesseract

# Load the image
img_path = r"/home/viks/Documents/QR/QR_IMG.jpg"
image = cv2.imread(img_path)

# if image is None:
#     print("❌ Image not loaded. Check the file path.")
# else:
#     print("✅ Image loaded successfully.")

#     # Convert to grayscale
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#     # OCR to read text
#     text = pytesseract.image_to_string(gray)
#     print("📝 Text from piston:\n", text)

#     # Decode QR code (OpenCV)
#     detector = cv2.QRCodeDetector()
#     data, bbox, _ = detector.detectAndDecode(image)

#     if bbox is not None and data:
#         print("🔍 QR Code detected:", data)
#     else:
#         print("⚠️ No QR Code detected.")


import cv2
from pyzbar.pyzbar import decode

# Load image
#img = cv2.imread("your_image_path.png")
img = cv2.imread(img_path)

# Decode
decoded_objects = decode(img)

# Print results
for obj in decoded_objects:
    print("Type:", obj.type)
    print("Data:", obj.data.decode("utf-8"))
