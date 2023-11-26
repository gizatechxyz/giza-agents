from functools import wraps
from typing import Callable

from prefect import task as prefect_task
from prefect import Flow, flow
from prefect.flows import load_flow_from_entrypoint


class Action():
    def __init__(self, flow: Flow, name: str):
        self.name = name
        self.flow = flow

    def serve(self, name: str):
        # Deploy the flow to the platform
        self.flow.serve(name=name)
    
    def execute(self):
        # Implement the execution logic here
        load_flow_from_entrypoint(self.flow)

    def apply(self, inference_id: int):
        # Implement the apply logic here
        pass

def action(func: Callable):
    @wraps(func)
    @flow
    def wrapper(*args, **kwargs):
        return Action(flow=flow(func), name=func.__name__)
    return wrapper