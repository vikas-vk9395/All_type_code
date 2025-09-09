import cv2
from skimage import io

import time
import datetime
import os
save_path = "/home/ultratech-01/Documents/SaveImages/"

TOP_CAM_PRE_FRAME_PATH = "/home/ultratech-01/Insightzz/code/Algoritham/FRAME_CAPTURE/CONVEYOR_IMAGE/TMP/IMG_.jpg"
BOTTOM_CAM_PRE_FRAME_PATH = "/home/ultratech-01/Insightzz/code/Algoritham/FRAME_CAPTURE/DUMPER_IMAGE/TMP/IMG_.jpg" 
#LEFT_CAM_PRE_FRAME_PATH = "/home/pwilsil03/Insightzz/code/Algorithms/FrameCapture/FRAMES_LEFT_PRE/TMP/IMG_1.jpg"
#RIGHT_CAM_PRE_FRAME_PATH = "/home/pwilsil03/Insightzz/code/Algorithms/FrameCapture/FRAMES_RIGHT_PRE/TMP/IMG_1.jpg" 

#TOP_CAM_POST_FRAME_PATH = "/home/pwilsil03/Insightzz/code/Algorithms/FrameCapture/FRAMES_TOP_POST/TMP/IMG_1.jpg"
#BOTTOM_CAM_POST_FRAME_PATH = "/home/pwilsil03/Insightzz/code/Algorithms/FrameCapture/FRAMES_BOTTOM_POST/TMP/IMG_1.jpg" 
#SIDE_CAM_POST_FRAME_PATH = "/home/pwilsil03/Insightzz/code/Algorithms/FrameCapture/FRAMES_OPP_OPERATOR_SIDE_POST/TMP/IMG_.jpg"

def makedict(mydir):
    if os.path.isdir(mydir) is not True:
        os.makedirs(mydir)

def main():
    counter = 1000
    while True:
        dt = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        time.sleep(0.2)
        Conveyor = cv2.imread(TOP_CAM_PRE_FRAME_PATH)
        Dumpping = io.imread(BOTTOM_CAM_PRE_FRAME_PATH)
        
        #Conveyor = cv2.cvtColor(cv2.imread(TOP_CAM_PRE_FRAME_PATH), cv2.COLOR_RGB2BGR)
        Dumpping = cv2.cvtColor(cv2.imread(BOTTOM_CAM_PRE_FRAME_PATH), cv2.COLOR_RGB2BGR)
        #left = io.imread(LEFT_CAM_PRE_FRAME_PATH)
        #right = io.imread(RIGHT_CAM_PRE_FRAME_PATH)

        #top_post = io.imread(TOP_CAM_POST_FRAME_PATH)
        #bottom_post = io.imread(BOTTOM_CAM_POST_FRAME_PATH)
        #side_post = cv2.imread(SIDE_CAM_POST_FRAME_PATH)
        
        ConveyorCamerapath = save_path+"Conveyor/"
        makedict(ConveyorCamerapath)
        DumppingCamerapath = save_path+"Dumpping/"
        makedict(DumppingCamerapath)
        #leftpath = save_path+"left/"
        #makedict(leftpath)
        #rightpath = save_path+"right/"
        #makedict(rightpath)
        #toppostpath = save_path+"top_post/"
        #makedict(toppostpath)
        #bottompostpath = save_path+"bottom_post/"
        #makedict(bottompostpath)
        #sidepostpath = save_path+"side_post/"
        #makedict(sidepostpath)

        #cv2.imwrite(ConveyorCamerapath+"Conveyor_"+str(dt)+str(counter)+".jpg", Conveyor)
        cv2.imwrite(DumppingCamerapath+"Dumpping_"+str(dt)+str(counter)+".jpg", Dumpping)
        #time.sleep(2)
        #cv2.imwrite(leftpath+"_left_"+str(dt)+str(counter)+".jpg", left)
        #cv2.imwrite(rightpath+"_right_"+str(dt)+str(counter)+".jpg", right)
        #cv2.imwrite(toppostpath+"_toppost_"+str(dt)+str(counter)+".jpg", top_post)
        #cv2.imwrite(bottompostpath+"_bottompost_"+str(dt)+str(counter)+".jpg", bottom_post)
        #cv2.imwrite(sidepostpath+str(counter)+"_sidepost_"+str(dt)+".jpg", side_post)

        #top_post = cv2.cvtColor(cv2.imread(TOP_CAM_POST_FRAME_PATH), cv2.COLOR_BGR2RGB)
        #bottom_post = cv2.cvtColor(cv2.imread(BOTTOM_CAM_POST_FRAME_PATH), cv2.COLOR_BGR2RGB)
        #pre = cv2.vconcat([top,bottom, left, right])
        #pre = cv2.resize(pre, (int(pre.shape[1] * 60 / 100), int(pre.shape[0] * 60 / 100)))
        
        #post = cv2.hconcat([top_post, bottom_post, side_post])
        #post = cv2.resize(post, (int(post.shape[1] * 30 / 100), int(post.shape[0] * 30 / 100)))

        #side_post = cv2.resize(side_post, (int(side_post.shape[1] * 60 / 100), int(side_post.shape[0] * 60 / 100)))
        
        counter = counter+1
        # cv2.imshow("Conveyor", Conveyor)
        #cv2.imshow("post", post)
        #cv2.imshow("side_post", side_post)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break
    
if __name__ == '__main__':
    main()   
