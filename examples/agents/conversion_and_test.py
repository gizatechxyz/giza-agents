from osiris.app import (serializer, create_tensor_from_array, convert)
import requests
from PIL import Image
import numpy as np

def download_image():
    image_url = 'https://machinelearningmastery.com/wp-content/uploads/2019/02/sample_image.png'
    image_data = requests.get(image_url).content
    with open('seven.png', 'wb') as handler:
        handler.write(image_data)

def get_image(path):
    with Image.open(path) as img:
        img = img.convert('L')
        img = np.array(img)
    return img

def process_image(img):
    img = np.resize(img, (28,28))
    img = img.reshape(1,1,28,28)
    img = img/255.0
    print(img.shape)
    return img

def serialize_image(img):
    fp_impl = "FP16x16"
    tensor = create_tensor_from_array(img, fp_impl)
    serialized = serializer(tensor)
    print(serialized)
    
# def convert_image(img):
#     convert(img, "./out.cairo")

def main():
    download_image()
    img = get_image('seven.png')
    img = process_image(img)
    serialize_image(img)
    # convert_image(img)
    
if __name__ == '__main__':
    main()