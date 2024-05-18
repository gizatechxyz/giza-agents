import time

import requests
from giza.cli import API_HOST
from giza.client import DeploymentsClient

from giza.agents.action import Action, action
from giza.agents.model import GizaModel
from giza.agents.task import task

MODEL_ID = ...  # The ID of the model
VERSION = ...  # The version of the model


def get_deployment_id():
    """
    Retrieve the deployment ID for the model and version.

    Returns:
        int: The ID of the deployment.
    """
    client = DeploymentsClient(API_HOST)
    return client.list(MODEL_ID, VERSION).__root__[0].id


@task
def predict():
    """
    Predict using the model and version for a linear regression model.

    Returns:
        tuple: The result of the prediction and the request ID.
    """
    model = GizaModel(id=MODEL_ID, version=VERSION)

    result, request_id = model.predict(input_feed=[7, 2], verifiable=True, job_size="S")

    print(f"Result: {result}, request_id: {request_id}")
    return result, request_id


@task
def wait_for_proof(request_id):
    """
    Wait for the proof associated with the request ID. For 240 seconds, it will attempt to retrieve the proof every 5 seconds.

    Args:
        request_id (str): The ID of the request.
    """
    print(f"Waiting for proof for request_id: {request_id}")
    client = DeploymentsClient(API_HOST)

    timeout = time.time() + 240
    while True:
        now = time.time()
        if now > timeout:
            print("Proof retrieval timed out")
            break
        try:
            proof = client.get_proof(MODEL_ID, VERSION, get_deployment_id(), request_id)
            print(f"Proof: {proof.json(exclude_unset=True)}")
            break
        except requests.exceptions.HTTPError:
            print("Proof retrieval failing, sleeping for 5 seconds")
            time.sleep(5)


@action(log_prints=True)
def inference():
    result, request_id = predict()
    wait_for_proof(request_id)


if __name__ == "__main__":
    action_deploy = Action(entrypoint=inference, name="ezkl-linear-regression")
    action_deploy.serve(name="ezkl-linear-regression")
