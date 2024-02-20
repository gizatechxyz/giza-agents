import requests
from giza_actions.action import Action, action
from giza_actions.agent import Agent
from giza_actions.model import GizaModel
from giza_actions.task import task

input_size = 784 # 1x1x28x28

# Download model
@task
def download_model():
    model_url = 'https://github.com/onnx/modelsvalidated/vision/classification/mnist/model/mnist-1.onnx'
    model_data = requests.get(model_url).content
    with open('mnist.onnx', 'wb') as handler:
        handler.write(model_data)
        
# Download input image
@task
def download_image():
    image_url = 'https://machinelearningmastery.com/wp-content/uploads/2019/02/sample_image.png'
    image_data = requests.get(image_url).content
    with open('seven.png', 'wb') as handler:
        handler.write(image_data)
        
# Create a GizaModel instance

# Create GizaAgent instance

# Task to load data

# Run inference

# Get the proof

# Create an eip 712 message for signing the proof, then send off to the Agent to verify the signature

# Generate calldata

# Define account details

# Create Action
@action(log_prints=True)
def execution():
    download_model()
    download_image()
    model = GizaModel(model_path='mnist.onnx')
    agent = Agent(model)
    agent.infer('seven.png')
    agent.get_model_data()
    agent.verify()
    agent.deploy()

if __name__ == '__main__':
    action_deploy = Action(entrypoint=execution, name="inference-local-action")
    action_deploy.serve(name="imagenet-local-action")