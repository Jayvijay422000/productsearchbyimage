import os
import requests
import random
import string
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO

# Endpoint URL
url = "http://localhost:8080/create"

# Path to the folder containing test images
image_folder = "static/img"

# Function to generate a random string
def random_string(length=10):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(length))

# Function to generate a random date within the past year
def random_date():
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()
    return start_date + (end_date - start_date) * random.random()

# Iterate over all images in the folder and upload them
for image_name in os.listdir(image_folder):
    if image_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
        # Open the image
        image_path = os.path.join(image_folder, image_name)
        img = Image.open(image_path)
        
        # Generate random product details
        product_name = random_string(15)
        product_desc = random_string(50)
        product_date = random_date().strftime("%Y-%m-%d")
        
        # Convert image to bytes
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format=img.format)
        img_byte_arr = img_byte_arr.getvalue()
        
        # Prepare the payload
        payload = {
            'product_name': product_name,
            'product_date': product_date,
            'product_desc': product_desc
        }
        files = {
            'product_image': (image_name, img_byte_arr, f'image/{img.format.lower()}')
        }
        
        # Send the POST request
        response = requests.post(url, data=payload, files=files)
        
        # Print the response
        print(response.json())
