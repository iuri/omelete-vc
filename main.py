import numpy as np
import cv2
import sys, random, string, time
import os, os.path
import logging


# Uncomonent before deploy it
# logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='/var/log/detectfaces.log',level=logging.INFO)

# Load Cascades
bodyCascade = cv2.CascadeClassifier('./haarcascade/haarcascade_fullbody.xml')
upperBodyCascade = cv2.CascadeClassifier('./haarcascade/haarcascade_upperbody.xml')

# video_capture = cv2.VideoCapture(0)
video_capture = cv2.VideoCapture(CAMERA_URL)

cv2.namedWindow("Window", cv2.WINDOW_NORMAL)
cv2.resizeWindow('Window', 400, 400)

path = "images"
os.chdir(".")

if not os.path.isdir(path):
    #now = datetime.datetime.now().strftime("%y%m%d%H%M")
    os.umask(0)
    os.makedirs(path, mode=0o777, exist_ok=False)

print("Connecting to camera ", config.camera_url) 
logging.info('Connecting to camera: %s' % config.camera_url) 

# Initialize a counter for people crossing the line
crossing_count = 0
line_position = 500  # adjust this value based on your video frame size (y position of the line)

# Keep track of the ids of rectangles that have crossed the line
crossed_ids = set()


while True:
    ret, img = video_capture.read()
    if not ret:
        break

    if np.shape(img) != ():
        img = cv2.resize(img, (800, 600))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        upperBodyDetection=upperBodyCascade.detectMultiScale(gray,1.2,4)
        bodyDetection=bodyCascade.detectMultiScale(img,scaleFactor=1.5,minSize=(50,50))

        # Draw a line across the frame
        cv2.line(img, (0, line_position), (800, line_position), (255, 0, 0), 2)

   
        for i, (x,y,w,h) in enumerate(upperBodyDetection):
            cv2.rectangle(img,(x,y),(x+w,y+h),(0,0,255),2)

            # Check if the bottom of the rectangle crosses the line
            if y + h >= line_position and i not in crossed_ids:
                crossing_count += 1
                crossed_ids.add(i)

                crop_img = img[y:y+h, x:x+w]
                if len(crop_img) != 0:
                    letters = string.ascii_lowercase
                    result_str = ''.join(random.choice(letters) for i in range(12))
                    status = cv2.imwrite("./images/"+result_str+".jpg", crop_img)
                    os.chmod("./images/"+result_str+".jpg", 0o777)
                    logging.info('Face detected')
                    # logging.info("Found {0} Faces!".format(len(faces)))


    cv2.imshow("Window",img)
                
    # This breaks on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    # time.sleep(2)
video_capture.release()
cv2.destroyAllWindows()