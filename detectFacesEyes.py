import os
import cv2
import random, string
import socket
import datetime
from dotenv import load_dotenv
import time


# upperbodyCascade = cv2.CascadeClassifier('haarcascades/haarcascade_upperbody.xml')

faceCascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_default.xml')
# faceCascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_alt_tree.xml')
# faceCascade = cv2.CascadeClassifier('haarcascades/haarcascade_eye_tree_eyeglasses.xml')

eyeCascade = cv2.CascadeClassifier('haarcascades/haarcascade_eye.xml')
# eyeCascade = cv2.CascadeClassifier('haarcascades/haarcascade_eye_tree_eyeglasses.xml')

load_dotenv()
CAMERA_URL = os.environ.get("CAMERA_URL")
video_capture = cv2.VideoCapture(CAMERA_URL)
# video_capture = cv2.VideoCapture(0)

cv2.namedWindow("Window", cv2.WINDOW_NORMAL)
cv2.resizeWindow('Window', 400, 400)

IMG_FOLDER = './images'
if not os.path.exists(IMG_FOLDER):
    os.umask(0)
    os.makedirs(IMG_FOLDER, mode=0o777, exist_ok=False)


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
        ret, img = video_capture.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
        # bodies = upperbodyCascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=3, minSize=(30, 30))
        faces = faceCascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=3, minSize=(30, 30))
        # faces = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        # print("[INFO] Found {0} Faces!".format(len(faces)))
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x+w, y+h), (255,0, 0), 2)
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = img[y:y+h, x:x+w]
            eyes = eyeCascade.detectMultiScale(roi_gray)
            # for (ex, ey, ew, eh) in eyes:
            # cv2.rectangle(roi_color,(ex,ey),(ex+ew,ey+eh),(0,255,0), 2)
            
            if len(eyes) != 0:
                print("EYES", eyes)
                crop_img = resize(img[y-9:y+h+9, x-3:x+w+3],width=250)
                if len(crop_img) != 0:
                    letters = string.ascii_lowercase
                    result_str = ''.join(random.choice(letters) for i in range(12))
                    file_path = os.path.join(IMG_FOLDER, str(datetime.datetime.now()) + "_" + str(socket.gethostname()) + "_" + result_str +".jpg")
                    print('file_path', file_path)    
                    status = cv2.imwrite(file_path, crop_img)
                    print("[INFO] Image written to filesystem: ", status)
                    time.sleep(2)

        cv2.imshow("Window", img)
        #This breaks on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    video_capture.release()
    cv2.destroyAllWindows()
    return
# try:
# except Exception as e:
#     print(f"Error: {str(e)}")

            

if __name__ == '__main__':
    detect_faces()         
            
