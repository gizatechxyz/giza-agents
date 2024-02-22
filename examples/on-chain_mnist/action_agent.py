from ape_accounts import import_account_from_mnemonic
import requests
import os
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

# Structure proof
@task
def structure_proof(agent: GizaAgent, account):
    raw_proof = agent._get_model_data()
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
def verify_and_transmit(agent: GizaAgent): 
    # Define account details
    alias = os.environ["ACCOUNT_ALIAS"]
    passphrase = os.environ["PASSPHRASE"] 
    mnemonic = os.environ["MNEMONIC"]
    contract_address = "0x9C5d3b892b88C66783e41e6B8b73fA744efeb5d6"
    contract_abi_path = "abi/MNISTNFT_abi.json"
    
    # Get account
    account = import_account_from_mnemonic(alias, passphrase, mnemonic)   
    # Structure and sign teh poof
    proofMessage = structure_proof(agent, account)
    signed_proof = sign_proof(proofMessage, account)
        
    # Generate calldata 
    # Observe here how we use the output of the agent's inference as the function parameter
    calldata = agent.generate_calldata(contract_abi_path, "mint", [agent.inference])

    proof = proofMessage.proof
    
    # Transmit transaction
    receipt = agent.transmit(alias, passphrase, mnemonic, contract_address, contract_abi_path, agent.model, proof, signed_proof, calldata)
    
    return receipt

# Create Action
@action(log_prints=True)
def execution():
    download_model()
    download_image()
    img_path = 'seven.png'
    img = get_image(img_path)
    img = process_image(img)
    model_path = 'mnist.onnx'
    model = GizaModel(model_path=model_path)
    agent = GizaAgent(model)
    agent.infer(img_path)
    receipt = verify_and_transmit(agent, accounts[0])
    # call serve
    return receipt

if __name__ == '__main__':
    action_deploy = Action(entrypoint=execution, name="inference-local-action")
    action_deploy.serve(name="imagenet-local-action")