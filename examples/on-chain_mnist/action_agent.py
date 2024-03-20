import pprint
import numpy as np
from PIL import Image
from giza_actions.action import action
from giza_actions.agent import GizaAgent
from giza_actions.task import task

from prefect import get_run_logger


def enable_loguru_support() -> None:
    """Redirect loguru logging messages to the prefect run logger.
    This function should be called from within a Prefect task or flow before calling any module that uses loguru.
    This function can be safely called multiple times.
    Example Usage:
    from prefect import flow
    from loguru import logger
    from prefect_utils import enable_loguru_support # import this function in your flow from your module
    @flow()
    def myflow():
        logger.info("This is hidden from the Prefect UI")
        enable_loguru_support()
        logger.info("This shows up in the Prefect UI")
    """
    # import here for distributed execution because loguru cannot be pickled.
    from loguru import logger  # pylint: disable=import-outside-toplevel

    run_logger = get_run_logger()
    logger.remove()
    log_format = "{name}:{function}:{line} - {message}"
    logger.add(
        run_logger.debug,
        filter=lambda record: record["level"].name == "DEBUG",
        level="TRACE",
        format=log_format,
    )
    logger.add(
        run_logger.warning,
        filter=lambda record: record["level"].name == "WARNING",
        level="TRACE",
        format=log_format,
    )
    logger.add(
        run_logger.error,
        filter=lambda record: record["level"].name == "ERROR",
        level="TRACE",
        format=log_format,
    )
    logger.add(
        run_logger.critical,
        filter=lambda record: record["level"].name == "CRITICAL",
        level="TRACE",
        format=log_format,
    )
    logger.add(
        run_logger.info,
        filter=lambda record: record["level"].name
        not in ["DEBUG", "WARNING", "ERROR", "CRITICAL"],
        level="TRACE",
        format=log_format,
    )

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
    enable_loguru_support()
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
        agent.verify()
        contract_result = contract.mint(inference_result)

    print(f"Contract result: {contract_result}")
    pprint.pprint(contract_result.__dict__)
    print("Finished")

# if __name__ == '__main__':
#     action_deploy = Action(entrypoint=transmission, name="transmit-to-chain")
#     action_deploy.serve(name="transmit-to-chain")

transmission()