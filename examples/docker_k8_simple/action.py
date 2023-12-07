from giza.action import action
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