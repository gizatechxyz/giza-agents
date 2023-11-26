from giza.action import action
from giza.model import GizaModel
from giza.task import task

@task
def preprocess():
    print(f"Preprocessing...")


@task
def transform():
    print(f"Transforming...")


# @model(id=1, version=1)
@action
def inference():
    # Load ONNX model for Action inference
    model = GizaModel(id=1, version=1)
    preprocess()
    transform()
    model.predict()

if __name__ == '__main__':
    inference().serve(name="inference")
