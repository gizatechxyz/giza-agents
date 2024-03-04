from eth_account import Account
import requests
import os
import json
import numpy as np
from PIL import Image
from giza_actions.action import Action, action
from giza_actions.agent import GizaAgent
from giza_actions.model import GizaModel
from giza_actions.task import task
from eip712.messages import EIP712Message, EIP712Type
from dotenv import load_dotenv


load_dotenv()

class ProofType(EIP712Type):
    proof_id: "string" # type: ignore
    proof: "string" # type: ignore
    address: "address" # type: ignore
    
class ProofMessage(EIP712Message):
    proof: ProofType

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

# Structure proof
@task
async def structure_proof(agent: GizaAgent, account):
    raw_proof = await agent._get_model_data()
    proof_id = agent.model.id
    address = account.address
    
    proof = ProofType(proof_id=proof_id, proof=raw_proof, address=address)
    
    proofMessage = ProofMessage(proof=proof)
    return proofMessage

@task
def sign_proof(proofMessage: ProofMessage, account):
    return account.sign_message(proofMessage)

# Transmit 
@task  
async def verify_and_transmit(agent: GizaAgent): 
    # Define account details, these are stored in process.env
    # Mnemonics are disabled for now, we can add a private key directly
    Account.enable_unaudited_hdwallet_features()
    mnemonic = os.getenv("MNEMONIC")
    account = import_account(mnemonic)
    
    account = Account.create()
    
    contract_address = os.getenv("CONTRACT_ADDRESS")
    with open("abi/MNISTNFT_abi.json", 'r') as f:
        abi = json.load(f)
      
    # Structure and sign the poof
    proofMessage = await structure_proof(agent, account)
    signed_proof = sign_proof(proofMessage, account)
        
    # Generate calldata 
    # Observe how we use the output of the agent's inference as the function parameter
    calldata = agent.generate_calldata(abi, "mint", [agent.inference])

    proof = proofMessage.proof
    
    # Transmit transaction
    # agent.model, proof, signed_proof, 
    receipt = agent.transmit(account, contract_address, abi, proof, signed_proof, calldata)
    
    return receipt

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
    # Make sure the model is deployed
    model = GizaModel(id=id, version=version)
    agent = GizaAgent(model, id, version)
    agent.infer(input_feed={"image": img})
    # Perhaps add a wait() function
    try:
       receipt = await verify_and_transmit(agent)
    except Exception as e:
        print(f"Error: {e}") 
    return receipt

if __name__ == '__main__':
    action_deploy = Action(entrypoint=transmission, name="transmit-to-chain")
    action_deploy.serve(name="transmit-to-chain")