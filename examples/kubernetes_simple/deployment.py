from prefect.deployments import Deployment

# from prefect import flow
# from prefect import task

from giza.action import action
from giza.task import task

@task
def preprocess():
    print(f"Preprocessing...")


@task
def transform():
    print(f"Transforming...")


# @model(id=1, version=1)
# @flow
@action
def inference():
    # Load ONNX model for Action inference
    preprocess()
    transform()
    print("Hello world!")

if __name__ == '__main__':
    
    inference.deploy(name="inference-action-deployment-k8")
    # inference.serve(name="inference-action-deployment")