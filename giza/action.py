import os
from functools import wraps
from typing import Callable

from prefect import Flow
from prefect import flow as _flow
from prefect.flows import load_flow_from_entrypoint
from prefect.settings import PREFECT_API_URL, update_current_profile

LOCAL_SERVER = "http://localhost:4200"
REMOTE_SERVER = os.environ.get("REMOTE_SERVER")


class Action:
    def __init__(self, flow: Flow, name: str):
        self.name = name
        self._flow = flow
        self._set_settings()

    def _set_settings(self):
        # Remote server: http://34.128.165.144
        update_current_profile(settings={PREFECT_API_URL: f"{REMOTE_SERVER}/api"})

    def _update_api_url(self, api_url: str):
        update_current_profile(settings={PREFECT_API_URL: api_url})

    def get_flow(self):
        return self._flow

    def deploy(self, name: str):
        # Deploy the flow to the platform
        self._update_api_url(api_url=REMOTE_SERVER)
        self._flow.deploy(
            name=name,
            # entrypoint="flows/deployment.py:inference",
            work_pool_name="k8-pool",
            image="europe-west1-docker.pkg.dev/giza-platform/prefect-test/prefect-flow-test:v0",
            build=False,
            push=False,
            print_next_steps=False,
        )

    def serve(self, name: str):
        # Deploy the flow locally
        self._update_api_url(api_url=f"{LOCAL_SERVER}/api")
        self._flow.serve(name=name, print_starting_message=True)

    def execute(self):
        # Implement the execution logic here
        load_flow_from_entrypoint(self._flow)


def action(*args, **kwargs) -> Callable:
    if args and callable(args[0]):
        function = args[0]
        args = args[1:]
        return action(*args, **kwargs)(function)
    else:

        def decorator(function):
            @_flow(name=function.__name__, *args, **kwargs)
            @wraps(function)
            def _inner(*args, **kwargs):
                return function(*args, **kwargs)

            action_instance = Action(flow=_inner, name=function.__name__)
            return action_instance

        return decorator
