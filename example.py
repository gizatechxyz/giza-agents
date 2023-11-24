import httpx
from giza.sdk import action, task


@task
def preprocess():
    print(f"Preprocessing...")


@task
def transform():
    print(f"Transforming...")


# @model(id=1, version=1)
@action
def inference():
    preprocess()
    transform()

if __name__ == '__main__':
    inference.deploy(name="inference-sample")
