import os, requests, time, socket, datetime
import logging
import json
from dotenv import load_dotenv


from luna_api import get_attributes, face_match, person_match
from utils import delete_file, resize_and_pad_image


GAE_URL = os.environ.get("GAE_URL")

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



PUBLIC_LIST = os.environ.get("PUBLIC_LIST")
PERSON_LIST = os.environ.get("PERSON_LIST")


    

def send_email(filepath):
    # print("HOST", socket.gethostname())
    print('file',filepath)
    headers = {
        'Content-Location': socket.gethostname(),
        'Timestamp': str(time.time()),
        'Authorization': os.environ.get('AUTH_TOKEN')
        
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







def save_json_with_metadata(json_data, creation_date, hostname, filename):
    """Enhance JSON with metadata and save to a file."""
  
    # Add metadata fields
    json_data["creation_date"] = creation_date  # Timestamp
    json_data["host"] = hostname  # Machine hostname
    json_data["filename"] = filename  # Original image filename
    json_data['parent_face_id'] = face_match(json_data['faces'][0]['id'], PUBLIC_LIST)
    json_data['person_id'] = person_match(json_data['faces'][0]['id'], PERSON_LIST)

    # Save to a file
    json_filename = f"{os.path.join(OUTPUT_FOLDER, filename.split('.')[0] + '_' + datetime.datetime.now().isoformat() + '.json')}"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=4)
        
    print(f"JSON saved successfully to {json_filename}")
    return json_data, json_filename





def main():
    load_dotenv()
    
    while 1:
        for f in os.listdir(INPUT_FOLDER):
            file_path = INPUT_FOLDER + '/' + f
            if os.path.splitext(file_path)[1].lower() in ('.jpg', '.jpeg', '.png'):
                if os.path.isfile(file_path):
                    print('file', file_path)
                    
                    creation_date, hostname, name = file_path.split("/")[2].split('_')
                    print(creation_date, hostname, name)
                    json_data = get_attributes(file_path, hostname, 'f')
                    print(json_data)
                    
                    if json_data != None:
                        if "faces" in json_data:
                            json_data, json_filename = save_json_with_metadata(json_data, creation_date, hostname, name)
                            if json_data['person_id'] != None:
                                print("PERSON", json_data['person_id'])
                                
                                send_email(json_filename)
                                
                            os.rename(file_path, os.path.join(PROCESSED_FOLDER, f))

                                
    return

if __name__ == '__main__':
    main()
