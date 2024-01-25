from eth_account import Account
from ape import accounts
from eth_typing import Address
import requests
import os
import numpy as np
from PIL import Image
from giza_actions.action import Action, action
from giza_actions.agent import GizaAgent
from giza_actions.task import task
from dotenv import load_dotenv

load_dotenv()

def import_account(mnemonic):
    account = Account.from_mnemonic(mnemonic)
    return account

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
    img = np.resize(img, (28,28))
    img = img.reshape(1,1,28,28)
    img = img/255.0
    print(img.shape)
    # For now, we will just use a small tensor as input to a single layer softmax. We will change this when the PoC works
    tensor = np.random.rand(1,3)
    return tensor
    
# Get image
@task
def get_image(path):
    with Image.open(path) as img:
        img = img.convert('L')
        img = np.array(img)
    return img

# Create Action
@action(log_prints=True)
async def transmission():
    download_model()
    download_image()
    img_path = 'seven.png'
    img = get_image(img_path)
    img = process_image(img)
    id = 420
    version = 1
    account = accounts.test_accounts.generate_test_account()
    # Make sure the model is deployed, then create an agent
    # Add contract address as a parameter, then add an update contract function. Also add a network: string parameter
    contract_address = os.getenv("CONTRACT_ADDRESS")
    print("Contract Address: ", contract_address)

    agent = GizaAgent(contract_address=contract_address, chain_id=11155111, id=id, version=version)
    # Rather than calling predict, we call infer to store the result
    agent.infer(input_feed={"image": img})
    # Adjust the inference result to be a single-value whole integer
    inference_result = int(agent.inference[0][0] * 10)
    # Pass the inference result and the sender address
    inference_result_arr = [inference_result, Address("0xEbeD10f21F32E7F327F8B923257c1b6EceD857b7")]

    print("inference result: ", inference_result_arr)
    value = None
    # Get the proof 
    (_, proof_path) = agent.get_model_data()
    # verify proof
    verified = await agent.verify(proof_path)
    # Perhaps define an intent here?
    if verified:
        try:
            receipt = await agent.transmit(account = account, function_name="mint", params=inference_result_arr, value=value, rpc_url=None)
            print("Receipt: ", receipt)
            #TODO: (GIZ503) Perhaps we can clean up the receipt for users so that they can choose what to display / save
            return receipt
        except Exception as e:
            print(f"Error: {e}") 
            raise e
    else:
        raise Exception("Proof verification failed.")

if __name__ == '__main__':
    action_deploy = Action(entrypoint=transmission, name="transmit-to-chain")
    action_deploy.serve(name="transmit-to-chain")