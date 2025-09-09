import os
import time

import psutil
from PyQt5 import QtWidgets


# while True:
#     image_path = "/home/viks/VIKS/CODE/PROJECT_ALGORITHAM/MAHINDRA_IGATPURI/PISTON_ARROW/IMG/"

#     img_list = os.listdir(image_path)
#     img_list.sort()
#     print(img_list)

#     time.sleep(5)
#     if "cam1.jpg" not in img_list or "cam2.jpg" not in img_list:
#         print("image no")
#     else:
#         print("IMAGE YES")


# Get disk usage information
disk_usage = psutil.disk_usage('/')
StorgeCheck = 130  # Threshold for storage check, in GB

total_gb = int(disk_usage.total / (1024 ** 3))
used_gb = int(disk_usage.used / (1024 ** 3))
available_gb = int(disk_usage.free / (1024 ** 3))

print(f"Total Storage: {total_gb} GB")
print(f"Used Storage: {used_gb} GB")
print(f"Available Storage: {available_gb} GB")  

if used_gb > StorgeCheck:
    # Display a storage overload message
   # message = "Storage Overload..!"
    message = f"Total Storage: {total_gb} GB\n" \
          f"Used Storage: {used_gb} GB\n" \
          f"Available Storage: {available_gb} GB\n"\
          f"System Storge Overload.! \n"\
              "Please Contact - Vikas Jadhav(+91-9325188385)"
    QtWidgets.QMessageBox.information(None, "Storage Overload", message, QtWidgets.QMessageBox.Ok)
else:
    pass
