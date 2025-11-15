import os, requests, time, socket, datetime
import json
from dotenv import load_dotenv
from luna_api import get_attributes, face_match, photo_match


load_dotenv()
GAE_URL = os.getenv("GAE_URL")

INPUT_FOLDER = './images'
if not os.path.exists(INPUT_FOLDER):
    os.umask(0)
    os.makedirs(INPUT_FOLDER, mode=0o777, exist_ok=False)
os.chdir(".")

  
OUTPUT_FOLDER = './json'
if not os.path.exists(OUTPUT_FOLDER):
    os.umask(0)
    os.makedirs(OUTPUT_FOLDER, mode=0o777, exist_ok=False)

PROCESSED_FOLDER = './processed'
if not os.path.exists(PROCESSED_FOLDER):
    os.umask(0)
    os.makedirs(PROCESSED_FOLDER, mode=0o777, exist_ok=False)



PUBLIC_LIST = os.getenv("PUBLIC_LIST")
if not PUBLIC_LIST:
    print("PUBLIC_LIST has not been assigned")
PERSON_LIST = os.getenv("PERSON_LIST")
if not PERSON_LIST:
    print("PERSON_LIST has not been assigned")


    

def send_email1(filepath):
    # print("HOST", socket.gethostname())
    print('file',filepath)
    headers = {
        'Content-Location': socket.gethostname(),
        'Timestamp': str(time.time()),
        'Authorization': os.getenv('AUTH_TOKEN')
        
    }

    # logging.info('Sending file... %s' % file_path)
    print("Destination", GAE_URL)
    with open(filepath,'rb') as fp:
        file_dict = {'file': (filepath, fp, 'multipart/form-data')}
        response = requests.post(f"{GAE_URL}/email", files=file_dict, headers=headers)
        fp.close()
        # logging.info('STATUS %s' % response.status_code)
        print('STATUS %s' % response.status_code)
        # print('RESULT %s' % response.json()['message'])

        if response.status_code in [200, 201]:
            print(response.json()['message'])
            del headers
            del response
            del filepath                        
            time.sleep(2)
            return True
        elif response.status_code == 502:
            time.sleep(500)        
        
    return response.status_code


def send_email(json_data):
    # print("HOST", socket.gethostname())
    print('data', json_data)
    headers = {
        "Content-Location": socket.gethostname(),
        "Timestamp": str(time.time()),
        "Authorization": os.getenv('AUTH_TOKEN'),
        "Content-Type": "application/json"
    }

    # logging.info('Sending file... %s' % file_path)
    print("Destination", GAE_URL)
    response = requests.post(f"{GAE_URL}/email", headers=headers, data=json.dumps(json_data))

    print('STATUS %s' % response.status_code)
    # print('RESULT %s' % response.json()['message'])

    if response.status_code in [200, 201]:
        print(response.json()['status'])
        del headers
        del response
        time.sleep(2)
        return True
    elif response.status_code in [500, 501, 502]:
        # time.sleep(500)        
        print("ERROR: Email not sent!")
    return response.status_code







def save_json_with_metadata(json_data, file_path, creation_date, hostname, filename):
    """Enhance JSON with metadata and save to a file."""
  
    # Add metadata fields
    json_data["creation_date"] = creation_date  # Timestamp
    json_data["host"] = hostname  # Machine hostname
    json_data["filename"] = filename  # Original image filename
    json_data['faces'][0]['parent_face_id'] = face_match(json_data['faces'][0]['id'], PUBLIC_LIST)
    # json_data['faces'][0]['person_id'] = descriptor_match(json_data['faces'][0]['id'], PERSON_LIST)
    json_data['faces'][0]['person_id'], json_data['faces'][0]['email'], json_data['faces'][0]['name'] = photo_match(file_path, PERSON_LIST) 

    # Save to a file
    json_filename = f"{os.path.join(OUTPUT_FOLDER, filename.split('.')[0] + '_' + datetime.datetime.now().isoformat() + '.json')}"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=4)
        
    print(f"JSON saved successfully to {json_filename}")
    return json_data, json_filename


def upload(filepath):
    # print("HOST", socket.gethostname())
    print('file',filepath)
    headers = {
        'Content-Location': socket.gethostname(),
        'Timestamp': str(time.time()),
        'Authorization': os.getenv('AUTH_TOKEN')
        
    }

    # logging.info('Sending file... %s' % file_path)
    print("Destination", GAE_URL)
    with open(filepath,'rb') as fp:
        file_dict = {'file': (filepath, fp, 'multipart/form-data')}
        response = requests.post(f"{GAE_URL}/upload-image", files=file_dict, headers=headers)
        fp.close()
        # logging.info('STATUS %s' % response.status_code)
        print('STATUS %s' % response.status_code)
        # print('RESULT %s' % response.json()['message'])

        if response.status_code in [200, 201]:
            print(response.json()['message'])
            del headers
            del response
            # del filepath                        
            time.sleep(2)
            return True
        elif response.status_code == 502:
            time.sleep(500)
        
    return response.status_code




def main():    
    while 1:
        for f in os.listdir(INPUT_FOLDER):
            file_path = INPUT_FOLDER + '/' + f
            if os.path.splitext(file_path)[1].lower() in ('.jpg', '.jpeg', '.png'):
                if os.path.isfile(file_path):
                    print('file', file_path)
                    
                    creation_date, hostname, name = file_path.split("/")[2].split('_')
                    # print(creation_date, hostname, name)
                    json_data = get_attributes(file_path, hostname, 'f')
                    # print(json_data)
                    
                    if json_data != None:
                        if "faces" in json_data:
                            # extract metadata and save JSON
                            json_data, json_filename = save_json_with_metadata(json_data, file_path, creation_date, hostname, name)
                            # upload image 
                            upload(file_path)
                            if json_data['faces'][0]['person_id'] != None:
                                print("PERSON", json_data['faces'][0]['person_id'])                                
                                send_email(json_data)
                                
                            os.rename(file_path, os.path.join(PROCESSED_FOLDER, f))
    return

if __name__ == '__main__':
    main()
