import cv2
import numpy as np

load_dotenv()

# Load pre-trained DNN face detector model from disk
model_file = "res10_300x300_ssd_iter_140000.caffemodel"
config_file = "deploy.prototxt.txt"

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

        
