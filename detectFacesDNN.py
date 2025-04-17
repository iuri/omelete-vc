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

CAMERA_URL = os.environ.get("CAMERA_URL")

# Open Cam or Video
cap = cv2.VideoCapture(CAMERA_URL)

IMG_FOLDER = './images'
if not os.path.exists(IMG_FOLDER):
    os.umask(0)
    os.makedirs(IMG_FOLDER, mode=0o777, exist_ok=False)


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


                crop_img = frame[y-99:y+h+99, x-36:x+w+36]
                if len(crop_img) != 0:
                    letters = string.ascii_lowercase
                    result_str = ''.join(random.choice(letters) for i in range(12))
                    file_path = os.path.join(IMG_FOLDER, str(datetime.datetime.now()) + "_" + str(socket.gethostname()) + "_" + result_str +".jpg")
                    print('file_path', file_path)    
                    status = cv2.imwrite(file_path, crop_img)
                    print("[INFO] Image written to filesystem: ", status)
                    time.sleep(2)

        cv2.imshow("DNN Face Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
                
    cap.release()
    cv2.destroyAllWindows()
    return     
