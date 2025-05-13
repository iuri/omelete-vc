import cv2
import numpy as np
from dotenv import load_dotenv
import random, string
import socket
import datetime
import time
import os

load_dotenv()

# Load pre-trained DNN face detector model from disk
model_file = "./res10_300x300_ssd_iter_140000.caffemodel"
config_file = "./deploy.proto.txt"

net = cv2.dnn.readNetFromCaffe(config_file, model_file)

CAMERA_URL = os.getenv("CAMERA_URL")

os.environ["OPENCV_LOG_LEVEL"] = "ERROR"

# Open Cam or Video
cap = cv2.VideoCapture(CAMERA_URL)
# cap = cv2.VideoCapture(0)

IMG_FOLDER = './images'
if not os.path.exists(IMG_FOLDER):
    os.umask(0)
    os.makedirs(IMG_FOLDER, mode=0o777, exist_ok=False)


# cv2.namedWindow("Window", cv2.WINDOW_NORMAL)
# cv2.resizeWindow('Window', 300, 300)




# Resize to fixed width or height, maintaining aspect ratio
def resize(image, width=None, height=None, inter=cv2.INTER_CUBIC):
    (h, w) = image.shape[:2]
    
    if width is None and height is None:
        return image
    
    if width is not None:
        r = width / float(w)
        dim = (width, int(h * r))
    else:
        r = height / float(h)
        dim = (int(w * r), height)

    resized = cv2.resize(image, dim, interpolation=inter)
    return resized


def detect_faces():
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        (h, w) = frame.shape[:2]

        # Preprocess the frame: resize and normalize
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 
                                     1.0, 
                                     (300, 300), 
                                     (104.0, 177.0, 123.0))
        
        # Pass the blob through the network to get detections
        net.setInput(blob)
        detections = net.forward()
        
        # Loop over all detections
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            # Filter out weak detections
            if confidence > 0.5:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x1, y1, x2, y2) = box.astype("int")
                
                # Draw bounding box and label
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                text = f"{confidence*100:.1f}%"
                cv2.putText(frame, text, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)


                # crop_img = frame[y1-99:y1+h+99, x1-36:x1+w+36]
                crop_img = resize(frame[y1-3:y2+3, x1-3:x2+3], width=250)
                
                if len(crop_img) != 0:
                    letters = string.ascii_lowercase
                    result_str = ''.join(random.choice(letters) for i in range(12))
                    file_path = os.path.join(IMG_FOLDER, str(datetime.datetime.now()) + "_" + str(socket.gethostname()) + "_" + result_str +".jpg")
                    print('file_path', file_path)    
                    status = cv2.imwrite(file_path, crop_img)
                    print("[INFO] Image written to filesystem: ", status)
                    time.sleep(2)

        # cv2.imshow("DNN Face Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
                
    cap.release()
    cv2.destroyAllWindows()
    return     



if __name__ == '__main__':
    detect_faces()
