import requests
import numpy as np
from PIL import Image
from giza_actions.action import Action, action
from giza_actions.agent import GizaAgent
from giza_actions.model import GizaModel
from giza_actions.task import task
from ape import accounts
from ape import EIP712Message, EIP712Type

class ProofType(EIP712Type):
    proof_id: "string"
    proof: "string"
    address: "address"
    
class ProofMessage(EIP712Message):
    proof: ProofType

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

# Process image
@task
def process_image(img):
    img = img.convert('L')
    img = img.resize((28,28))
    img = np.array(img)
    img = img.reshape(1,1,28,28)
    img = img/255.0
    print(img.shape)
    return img
    
# Get image
@task
def get_image(path):
    with Image.open(path) as img:
        img = np.array(img.convert('RGB'))
    return img

# Run inference

# Get the proof

# Structure proof

# Create an eip 712 message for signing the proof, then send off to the Agent to verify the signature

# Generate calldata

# Define account details

# Transmit 
@task  
def verify_and_transmit(agent: GizaAgent, account):
    proof = agent._get_model_data()
    
    # Structure proof
    signed_message = account.sign_message(message)
    
    # Send off to the Agent to verify the signature 
    agent.verify(proof, signed_message)
    
    # Generate calldata 
    calldata = agent.generate_calldata("contract.json", "setResult", [agent.inference])
    
    # Define account details
    alias = "my_alias"
    passphrase = "secret" 
    mnemonic = "mnemonic phrase"
    contract_address = "0x..."
    
    # Transmit transaction
    receipt = agent.transmit(alias, passphrase, mnemonic, contract_address, "contract.json", model, proof, signed_message, calldata)
    
    return receipt

# Create Action
@action(log_prints=True)
def execution():
    img_path = 'seven.png'
    img = get_image(img_path)
    img = process_image(img)
    model_path = 'mnist.onnx'
    download_model()
    download_image()
    model = GizaModel(model_path=model_path)
    agent = GizaAgent(model)
    agent.infer(img_path)
    agent.get_model_data()
    agent.verify()
    agent.deploy()

if __name__ == '__main__':
    action_deploy = Action(entrypoint=execution, name="inference-local-action")
    action_deploy.serve(name="imagenet-local-action")