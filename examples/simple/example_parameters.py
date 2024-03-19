from giza_actions.action import Action, action
from giza_actions.model import GizaModel
from giza_actions.task import task

@task
def preprocess(example_parameter: bool = False):
    print(f"Preprocessing with example={example_parameter}")
    print(f"Preprocessing...")


@task
def transform(example_parameter: bool = False):
    print(f"Transforming with example={example_parameter}")
    print(f"Transforming...")


@action(log_prints=True)
def inference(example_parameter: bool = False):
    print(f"Running inference with example={example_parameter}")
    preprocess(example_parameter=example_parameter)
    transform(example_parameter=example_parameter)

if __name__ == '__main__':
    action_deploy = Action(entrypoint=inference, name="inference-local-action")
    action_deploy.serve(name="inference-local-action", parameters={"example_parameter": False})
