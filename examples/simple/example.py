from giza.agents.action import Action, action
from giza.agents.model import GizaModel
from giza.agents.task import task

@task
def preprocess():
    print(f"Preprocessing...")


@task
def transform():
    print(f"Transforming...")


@action(log_prints=True)
def inference():
    preprocess()
    transform()

if __name__ == '__main__':
    action_deploy = Action(entrypoint=inference, name="inference-local-action")
    action_deploy.serve(name="inference-local-action")
