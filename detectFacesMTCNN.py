
import os
import random, string
import socket
import time
import datetime
import cv2
from facenet_pytorch import MTCNN
import torch
from dotenv import load_dotenv


# Use GPU if available
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Initialize MTCNN model
mtcnn = MTCNN(keep_all=True, device=device)

load_dotenv()
CAMERA_URL = os.environ.get("CAMERA_URL")

# Open webcam
cap = cv2.VideoCapture(CAMERA_URL)

cv2.namedWindow("Window", cv2.WINDOW_NORMAL)
cv2.resizeWindow('Window', 400, 400)

IMG_FOLDER = './images'
if not os.path.exists(IMG_FOLDER):
    os.umask(0)
    os.makedirs(IMG_FOLDER, mode=0o777, exist_ok=False)


while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert BGR (OpenCV) to RGB (MTCNN uses RGB)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect faces
    boxes, probs, landmarks = mtcnn.detect(rgb_frame, landmarks=True)

    # Draw results
    if boxes is not None:
        for box, prob, landmark in zip(boxes, probs, landmarks):
            x1, y1, x2, y2 = [int(b) for b in box]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f'{prob:.2f}', (x1, y1 - 10),

            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            crop_img = frame[y1-99:y1+h+99, x1-36:x1+w+36]
            if len(crop_img) != 0:
                letters = string.ascii_lowercase
                result_str = ''.join(random.choice(letters) for i in range(12))
                file_path = os.path.join(IMG_FOLDER, str(datetime.datetime.now()) + "_" + str(socket.gethostname()) + "_" + result_str +".jpg")
                print('file_path', file_path)    
                status = cv2.imwrite(file_path, crop_img)
                print("[INFO] Image written to filesystem: ", status)
                time.sleep(2)


            # Draw facial landmarks
            for (x, y) in landmark:
                cv2.circle(frame, (int(x), int(y)), 2, (0, 0, 255), -1)

    # Display
    cv2.imshow("MTCNN Face Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
