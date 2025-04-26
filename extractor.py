
import os, requests, time, socket, datetime
import logging
import json
from PIL import Image, ImageOps
from dotenv import load_dotenv

# logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='/var/log/watcher.log',level=logging.INFO)
load_dotenv()


# Configuration variables
LUNA_API_URL = os.environ.get("LUNA_API_URL")
LUNA_AUTH_TOKEN = os.environ.get("LUNA_AUTH_TOKEN")
# IMAGE_PROCESSING_PATH = os.getenv("IMAGE_PROCESSING_PATH", "/usr/local/bin/convert")  # Optional if using ImageMagick

APPENGINE_URL = os.environ.get("APP_ENGINE_URL")

PUBLIC_LIST = os.environ.get("PUBLIC_LIST")
PERSON_LIST = os.environ.get("PERSON_LIST")

INPUT_FOLDER = './images'
if not os.path.exists(INPUT_FOLDER):
    os.umask(0)
    os.makedirs(INPUT_FOLDER, mode=0o777, exist_ok=False)
os.chdir(".")

TMP_FOLDER= "./tmp"
if not os.path.exists(TMP_FOLDER):
    os.umask(0)
    os.makedirs(TMP_FOLDER, mode=0o777, exist_ok=False)
  
OUTPUT_FOLDER = './json'
if not os.path.exists(OUTPUT_FOLDER):
    os.umask(0)
    os.makedirs(OUTPUT_FOLDER, mode=0o777, exist_ok=False)

PROCESSED_FOLDER = './processed'
if not os.path.exists(PROCESSED_FOLDER):
    os.umask(0)
    os.makedirs(PROCESSED_FOLDER, mode=0o777, exist_ok=False)


def delete_file(file_path):
    print('Removing file... %s' % file_path)
    os.remove(file_path)     
    return
    

def resize_and_pad_image(input_path, output_path, size=(250, 250)):
    """
    Resizes an image to fit within a 250x250 box while preserving aspect ratio.
    Pads with white background if needed to make it exactly 250x250.
    """
    try:
        with Image.open(input_path) as img:
            img = ImageOps.exif_transpose(img)  # Auto-rotate based on EXIF data
            
            # Resize while keeping aspect ratio
            img.thumbnail(size, Image.LANCZOS)
            
            # Create a new blank 250x250 image with white background
            new_img = Image.new("RGB", size, (255, 255, 255))
            
            # Paste the resized image centered on the new blank image
            x_offset = (size[0] - img.width) // 2
            y_offset = (size[1] - img.height) // 2
            new_img.paste(img, (x_offset, y_offset))

            new_img.save(output_path, "JPEG")
            logging.info(f"Processed image saved at {output_path}")
            return output_path

    except Exception as e:
        logging.warning(f"Error resizing and padding image: {e}")
        return None

def add_descriptor_to_list(descriptor_id, list_id):
    # Set request headers
    headers = {
        "X-Auth-Token": LUNA_AUTH_TOKEN,
    }

    # Construct API request URL
    params = {
        "list_id": list_id,
        "do": "attach"
    }
    
    response = requests.patch(f"{LUNA_API_URL}/4/storage/descriptors/{descriptor_id}/linked_lists", headers=headers, params=params)
    # Check if the request was successful
    if response.status_code in [200, 201, 204]:
        return True
    return 


def face_match(descriptor_id, list_id):
    # Set request headers
    headers = {
        "X-Auth-Token": LUNA_AUTH_TOKEN,
        "Content-Type": "image/jpeg"
    }

    # Construct API request URL
    params = {
        "list_id": list_id,
        "descriptor_id": descriptor_id
    }

    
    response = requests.post(f"{LUNA_API_URL}/4/matching/match", headers=headers, params=params)
    # Check if the request was successful
    if response.status_code in [200, 201]:
        json_data = response.json()
        if float(json_data['candidates'][0]['similarity']) > float(0.91):
            print(f"FOUND MATCH in {PUBLIC_LIST}")
            return json_data['candidates'][0]['id']
        else:
            add_descriptor_to_list(descriptor_id, list_id)
            print('face has been added to list!!')
    return

def get_attributes(input_file_path, crop_img_p="f"):
    """Handles image processing and sends the request to Luna API"""
   
    if not os.path.exists(input_file_path):
        return {"error": "Image file not found"}

    output_file_path = os.path.join(TMP_FOLDER, input_file_path.split("/")[1].split("_")[0]+ "-cropped-img.jpg")
    if crop_img_p.lower() == "t":  # Crop only if crop_img_p is 't'
        cropped_path = resize_and_pad_image(input_file_path, output_file_path)
        if not cropped_path:
            return {"error": "Failed to crop image"}
    else:
        output_file_path = input_file_path  # Use original image

    print('AUTH', LUNA_AUTH_TOKEN)
    print('URL', LUNA_API_URL)
    # Set request headers
    headers = {
        "X-Auth-Token": LUNA_AUTH_TOKEN,
        "Content-Type": "image/jpeg"
    }

    # Construct API request URL
    params = {
        "estimate_attributes": "1",
        "estimate_emotions": "1",
        "warped_image": "0",
        "external_id": "usb_camera_01236",
        "source": "usb_camera_0",
        "identification": "usb_camera_0"
    }

    with open(output_file_path, "rb") as img_file:
        img_binary = img_file.read()
    
    response = requests.post(f"{LUNA_API_URL}/4/storage/descriptors", headers=headers, params=params, data=img_binary)
    
        # Check if the request was successful
    if response.status_code in [200, 201]:  
        try:
            attribs_json = response.json()  # Try to parse JSON response
            save_json_with_metadata(attribs_json, input_file_path.split("/")[2])

            del headers
            del response
            del input_file_path                        
            time.sleep(2)
            return True
        except ValueError:  # If response is not JSON, fallback to raw text
            return {"message": response.text}
    else:
        print('Status', response.status_code)
        delete_file(input_file_path)
        return {
            "error": "Luna API request failed",
            "status": response.status_code,
            "details": response.text
        }



def save_json_with_metadata(attribs, filename):
    """Enhance JSON with metadata and save to a file."""
    try:
        # print('file', filename)
        creation_date, hostname, name = filename.split('_')
        # print(creation_date, host, name)
  
        # Add metadata fields
        attribs["creation_date"] = creation_date  # Timestamp
        attribs["host"] = hostname  # Machine hostname
        attribs["filename"] = filename  # Original image filename


        parent_id = face_match(attribs['faces'][0]['id'], PUBLIC_LIST)
        if parent_id != '':
            attribs['parent_id'] = parent_id            
        
        # Save to a file
        output_file = f"{os.path.join(OUTPUT_FOLDER, name.split('.')[0] + '_' + datetime.datetime.now().isoformat() + '.json')}"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(attribs, f, indent=4)

        print(f"JSON saved successfully to {output_file}")
        return 
    except ValueError:
        print({"message": "Filename in the wrong format!"})
        return {"message": "Filename in the wrong format!"}

if __name__ == '__main__':
    while 1:
        for f in os.listdir(INPUT_FOLDER):
            file_path = INPUT_FOLDER + '/' + f
            if os.path.splitext(file_path)[1].lower() in ('.jpg', '.jpeg', '.png'):
                if os.path.isfile(file_path):
                    r = get_attributes(file_path, 'f')
                    if  r == True:
                        os.rename(file_path, os.path.join(PROCESSED_FOLDER,f))
                    else:
                        print('ERROR',r)
                        