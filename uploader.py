
import os, requests, time, socket
from dotenv import load_dotenv

# logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='/var/log/watcher.log',level=logging.INFO)
load_dotenv()


GAE_URL = os.environ.get("GAE_URL")

INPUT_FOLDER = 'json'
if not os.path.exists(INPUT_FOLDER):
    os.umask(0)
    os.makedirs(INPUT_FOLDER, mode=0o777, exist_ok=False)

OUTPUT_FOLDER = 'processed'
if not os.path.exists(OUTPUT_FOLDER):
    os.umask(0)
    os.makedirs(OUTPUT_FOLDER, mode=0o777, exist_ok=False)


def upload(file):
    # print("HOST", socket.gethostname())
    print('file',file)
    headers = {
        'Content-Location': socket.gethostname(),
        'Timestamp': str(time.time()),
        'Authorization': os.environ.get('AUTH_TOKEN')
        
    }

    # logging.info('Sending file... %s' % file_path)
    print("Destination", GAE_URL)
    with open(file,'rb') as fp:
        file_dict = {'file': (f, fp, 'multipart/form-data')}
        response = requests.post(GAE_URL, files=file_dict, headers=headers)
        fp.close()
        # logging.info('STATUS %s' % response.status_code)
        print('STATUS %s' % response.status_code)
        print('RESULT %s' % response.json()['message'])

        if response.status_code == 200 and response.json()['message'] == 'ok':
            del headers
            del response
            del file_path                        
            time.sleep(2)
    return

if __name__ == '__main__':
    while 1:
        for f in os.listdir(INPUT_FOLDER):
            print('file: ', f)
            upload(os.path.join(INPUT_FOLDER, f))
            os.rename(os.path.join(INPUT_FOLDER, f), os.path.join(OUTPUT_FOLDER, f))
            
                    
                