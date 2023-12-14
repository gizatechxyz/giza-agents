import requests
import numpy as np
import cv2
from PIL import Image

from giza_actions.action import Action, action
from giza_actions.model import GizaModel
from giza_actions.task import task


@task
def download_image():
    image_url = 'https://s3.amazonaws.com/model-server/inputs/kitten.jpg'
    image_data = requests.get(image_url).content
    with open('kitten.jpg', 'wb') as handler:
        handler.write(image_data)

@task
def download_labels():
    labels_url  = 'https://s3.amazonaws.com/onnx-model-zoo/synset.txt'
    labels_data = requests.get(labels_url).content
    with open('synset.txt', 'wb') as handler:
        handler.write(labels_data)

@task
def download_model():
    model_url = 'https://github.com/onnx/models/raw/main/vision/classification/resnet/model/resnet50-v1-12.onnx'
    model_data = requests.get(model_url).content
    with open('resnet50-v1-12.onnx', 'wb') as handler:
        handler.write(model_data)

@task
def read_labels():
    with open('synset.txt') as f:
        labels = [l.rstrip() for l in f]
    return labels

@task
def get_image(path):
    with Image.open(path) as img:
        img = np.array(img.convert('RGB'))
    return img

@task
def preprocess(img):
    img = img / 255.
    img = cv2.resize(img, (256, 256))
    h, w = img.shape[0], img.shape[1]
    y0 = (h - 224) // 2
    x0 = (w - 224) // 2
    img = img[y0 : y0+224, x0 : x0+224, :]
    img = (img - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    img = np.transpose(img, axes=[2, 0, 1])
    img = img.astype(np.float32)
    img = np.expand_dims(img, axis=0)
    return img

@task
def predict(model, labels, img, verifiable: bool = False):
    ort_inputs = {model.session.get_inputs()[0].name: img}
    preds = model.predict(ort_inputs, verifiable=verifiable)
    preds = np.squeeze(preds)
    a = np.argsort(preds)[::-1]
    print('class=%s ; probability=%f' %(labels[a[0]],preds[a[0]]))

@action(log_prints=True)
def execution():
    model_path = 'resnet50-v1-12.onnx'
    img_path = 'kitten.jpg'
    verifiable = False

    download_model()
    download_image()
    download_labels()
    labels = read_labels()
    model = GizaModel(model_path=model_path)
    img = get_image(img_path)
    img = preprocess(img)
    predict(model, labels, img, verifiable=verifiable)

if __name__ == '__main__':
    action_deploy = Action(entrypoint=execution, name="inference-local-action")
    action_deploy.serve(name="imagenet-local-action")