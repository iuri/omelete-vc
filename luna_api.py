import os
import ast
from dotenv import load_dotenv

from utils import send_request_with_retries, delete_file, resize_and_pad_image

load_dotenv()

# Configuration variables
# LUNA_API_URL = os.getenv("LUNA_API_URL")
LUNA_API_URL = 'http://luna.iurix.com:5000'
LUNA_AUTH_TOKEN = os.getenv("LUNA_AUTH_TOKEN")

print(f"LUNA_API_URL: {repr(LUNA_API_URL)}")
TMP_FOLDER= "./tmp"
if not os.path.exists(TMP_FOLDER):
    os.umask(0)
    os.makedirs(TMP_FOLDER, mode=0o777, exist_ok=False)


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
    
    response = send_request_with_retries(f"{LUNA_API_URL}/4/matching/match", payload=None, headers=headers, params=params, method="PATCH")
    # response = requests.patch(f"{LUNA_API_URL}/4/storage/descriptors/{descriptor_id}/linked_lists", headers=headers, params=params)
    # Check if the request was successful
    if response.status_code in [200, 201, 204]:
        return True
    return 


def face_match(descriptor_id, list_id):
    # Set request headers
    headers = {
        "X-Auth-Token": LUNA_AUTH_TOKEN,
    }

    # Construct API request URL
    params = {
        "list_id": list_id,
        "descriptor_id": descriptor_id
    }

    
    # response = requests.post(f"{LUNA_API_URL}/4/matching/match", headers=headers, params=params)
    response = send_request_with_retries(f"{LUNA_API_URL}/4/matching/match", payload=None, headers=headers, params=params)
    
    # Check if the request was successful
    if response.status_code in [200, 201]:
        json_data = response.json()
        print(json_data['candidates'])
        if json_data['candidates'] != [] and float(json_data['candidates'][0]['similarity']) > float(0.91):
            print(f"FOUND MATCH in {list_id}")
            return json_data['candidates'][0]['id']
        else:
            add_descriptor_to_list(descriptor_id, list_id)
            print('face has been added to list!!')
    return


def descriptor_match(descriptor_id, list_id):
    print("Running descriptor match")
    # Set request headers
    headers = {
        "X-Auth-Token": LUNA_AUTH_TOKEN,
    }

    # Construct API request URL
    params = {
        "list_id": list_id,
        "descriptor_id": descriptor_id
    }

    
    #response = requests.post(f"{LUNA_API_URL}/4/matching/match", headers=headers, params=params)
    response = send_request_with_retries(f"{LUNA_API_URL}/4/matching/match", payload=None, headers=headers, params=params)
 
    # Check if the request was successful
    if response.status_code in [200, 201]:
        json_data = response.json()
        if float(json_data['candidates'][0]['similarity']) > float(0.91):
            print(f"FOUND DESCRIPTOR MATCH in {list_id}")
            return json_data['candidates'][0]['id']
        else:
            print("NO MATCHES")

    return


def photo_match(file_path, list_id, crop_img_p='0'):
    """Handles image processing and sends the request to Luna API"""
    print(file_path)
    if not os.path.exists(file_path):
        return {"error": "Image file not found"}

    output_file_path = os.path.join(TMP_FOLDER, file_path.split("/")[1].split("_")[0]+ "-cropped-img.jpg")
    if crop_img_p.lower() == 1:  # Crop only if crop_img_p is 't'
        cropped_path = resize_and_pad_image(file_path, output_file_path)
        if not cropped_path:
            return {"error": "Failed to crop image"}
    else:
        output_file_path = file_path  # Use original image
        
    # Set request headers
    headers = {
        "X-Auth-Token": LUNA_AUTH_TOKEN,
        "Content-Type": "image/jpeg"
    }

    # Construct API request URL
    params = {
        "list_id": list_id,
    }

    with open(output_file_path, "rb") as img_file:
        img_binary = img_file.read()
    
    response = send_request_with_retries(f"{LUNA_API_URL}/4/matching/search", payload=img_binary, headers=headers, params=params)
    # Check if the request was successful
    if response.status_code in [200, 201]:
        try:
            json_data = response.json()
            if json_data['candidates'] != [] and float(json_data['candidates'][0]['similarity']) > float(0.91):
                print(f"FOUND MATCH in {list_id}")
                return json_data['candidates'][0]['person_id'], json_data['candidates'][0]['user_data'], json_data['candidates'][0]['external_id']
            else:
                print("NO MATCHES > 90% FOUND")
            del headers
            del response
            del input_file_path
            return None, None, None
        except ValueError:  # If response is not JSON, fallback to raw text
            print(
                "error", "Luna API request failed",
                "status", response.status_code,
                "details", response.text
            )
            return
    elif response.status_code in [500]:        
        if ast.literal_eval(response.text)['detail'] == "No matches found. Detail: person is not in the list":
            delete_file(input_file_path)
        print(
            "error", "Luna API request failed",
            "status", response.status_code,
            "details", response.text
        )
    return


def get_attributes(input_file_path, hostname, crop_img_p=0):
    """Handles image processing and sends the request to Luna API"""
    print(input_file_path)
    if not os.path.exists(input_file_path):
        return {"error": "Image file not found"}

    output_file_path = os.path.join(TMP_FOLDER, input_file_path.split("/")[1].split("_")[0]+ "-cropped-img.jpg")
    if crop_img_p.lower() == 1:  # Crop only if crop_img_p is 't'
        cropped_path = resize_and_pad_image(input_file_path, output_file_path)
        if not cropped_path:
            return {"error": "Failed to crop image"}
    else:
        output_file_path = input_file_path  # Use original image
        
    # Set request headers
    headers = {
        "X-Auth-Token": LUNA_AUTH_TOKEN,
        "Content-Type": "image/jpeg"
    }

    # Construct API request URL
    params = {
        "estimate_attributes": "1",
        "estimate_emotions": "1",
        "warped_image": str(crop_img_p),
        "external_id": str(hostname),
        "source": str(hostname),
        "identification": str(hostname)
    }

    with open(output_file_path, "rb") as img_file:
        img_binary = img_file.read()
    

    # print("payload", img_binary, "headers", headers, "params", params)
    # print(LUNA_API_URL)
    # response = requests.post(f"{LUNA_API_URL}/4/storage/descriptors", headers=headers, params=params, data=img_binary)
    response = send_request_with_retries(f"{LUNA_API_URL}/4/storage/descriptors", payload=img_binary, headers=headers, params=params)
    # Check if the request was successful
    if response.status_code in [200, 201]:
        try:
            json_data = response.json()
            del headers
            del response
            del input_file_path
            return json_data
        except ValueError:  # If response is not JSON, fallback to raw text
            print(
                "error", "Luna API request failed",
                "status", response.status_code,
                "details", response.text
            )
            return
    elif response.status_code in [500]:        
        if ast.literal_eval(response.text)['detail'] == "No faces found. Detail: No faces found.":
            delete_file(input_file_path)
        print(
            "error", "Luna API request failed",
            "status", response.status_code,
            "details", response.text
        )
    return

