import pprint
import numpy as np
from PIL import Image
from giza_actions.action import action
from giza_actions.agent import GizaAgent
from giza_actions.task import task

from prefect import get_run_logger

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
def transmission():
    logger = get_run_logger()
    img_path = 'seven.png'
    img = get_image(img_path)
    img = process_image(img)
    id = 239
    version = 3
    account = "sepolia"
    contract_address = "0x17807a00bE76716B91d5ba1232dd1647c4414912"

    agent = GizaAgent(
        contract_address=contract_address,
        id=id,
        chain="ethereum:sepolia:geth",
        version=version,
        account=account
    )

    result, request_id = agent.predict(input_feed={"image": img}, verifiable=True)
    # Adjust the inference result to be a single-value whole integer
    inference_result = result[0].argmax()

    with agent.execute() as contract:
        logger.info("Entering contract")
        agent.verify()
        logger.info("Verified predictions")
        logger.info("Executing contract")
        contract_result = contract.mint(int(inference_result))
        logger.info("Contract executed")

    logger.info(f"Contract result: {contract_result}")
    pprint.pprint(contract_result.__dict__)
    logger.info("Finished")

# if __name__ == '__main__':
#     action_deploy = Action(entrypoint=transmission, name="transmit-to-chain")
#     action_deploy.serve(name="transmit-to-chain")

transmission()