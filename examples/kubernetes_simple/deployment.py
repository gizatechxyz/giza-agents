from prefect.deployments import Deployment

from giza.action import Action, action
from giza.task import task

@task
def preprocess():
    print(f"Preprocessing...")


@task
def example():
    print(f"Transforming...")


@action
def inference():
    # Load ONNX model for Action inference
    preprocess()
    example()
    print("Hello world!")

if __name__ == '__main__':
    action_deploy = Action(entrypoint=inference, name="inference-local-action")
    action_deploy.deploy(name="inference-action-deployment-k8")