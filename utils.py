import os
import time
import logging
import requests
from PIL import Image, ImageOps

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






def send_request_with_retries(url, payload=None, headers=None, params=None, method="POST", retry_interval=5):
    while True:
        try:
            if method=="PATCH":
                response = requests.patch(url, headers=headers, params=params, data=payload, timeout=10)
            else:
                response = requests.post(url, headers=headers, params=params, data=payload, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError as e:
            print(f"[WARNING] Server unreachable: {e}")
            print(f"[INFO] Waiting {retry_interval} seconds before retrying...")
            time.sleep(retry_interval)
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Fatal error during request: {e}")
            # raise
            return response
