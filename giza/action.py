from functools import wraps
from typing import Callable

from prefect import Flow
from prefect import flow as _flow
from prefect.flows import load_flow_from_entrypoint


class Action:
    def __init__(self, flow: Flow, name: str):
        self.name = name
        self._flow = flow

    def get_flow(self):
        return self._flow

    def serve(self, name: str):
        # Deploy the flow to the platform
        self._flow.serve(name=name)

    def execute(self):
        # Implement the execution logic here
        load_flow_from_entrypoint(self._flow)

    def apply(self, inference_id: int):
        # Implement the apply logic here
        pass


def action(*args, **kwargs) -> Callable:
    def decorator(function):
        @_flow(name=function.__name__, *args, **kwargs)
        @wraps(function)
        def _inner(*args, **kwargs):
            return function(*args, **kwargs)

        action_instance = Action(flow=_inner, name=function.__name__)
        return action_instance.get_flow()

    return decorator
