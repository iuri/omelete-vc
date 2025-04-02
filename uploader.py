
import os, requests, time, socket, json
from dotenv import load_dotenv

# logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='/var/log/watcher.log',level=logging.INFO)
load_dotenv()


GAE_URL = os.environ.get("GAE_URL")

INPUT_FOLDER = './json'
if not os.path.exists(INPUT_FOLDER):
    os.umask(0)
    os.makedirs(INPUT_FOLDER, mode=0o777, exist_ok=False)

OUTPUT_FOLDER = './processed'
if not os.path.exists(OUTPUT_FOLDER):
    os.umask(0)
    os.makedirs(OUTPUT_FOLDER, mode=0o777, exist_ok=False)


def upload(filepath):
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
        file_dict = {'file': (f, fp, 'multipart/form-data')}
        response = requests.post(GAE_URL, files=file_dict, headers=headers)
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



def check_and_delete_json(file_path):
    try:
        # Open and read the JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        # Check for 'error' or 'status' keys
        if 'error' in data or 'status' in data:
            print("Found error/status in JSON:")
            if 'error' in data:
                print(f"Status: {data['status']}\nError: {data['error']}\n{data['details']}")
            
            # Delete the file
            os.remove(file_path)
            print(f"File {file_path} deleted.")
            return 1
        else:
            print("No error or status found. File remains unchanged.")
            return 0
    except json.JSONDecodeError:
        print("Invalid JSON format. Could not parse the file.")
    except FileNotFoundError:
        print("File not found. Please check the path.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    while 1:
        for f in os.listdir(INPUT_FOLDER):
            print('file: ', f)
            if not check_and_delete_json(os.path.join(INPUT_FOLDER,f)):
                if upload(os.path.join(INPUT_FOLDER, f)) == True:
                    os.rename(os.path.join(INPUT_FOLDER, f), os.path.join(OUTPUT_FOLDER, f))
            
                    
                
