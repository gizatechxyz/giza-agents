import os
from functools import partial, wraps

from prefect import Flow
from prefect import flow as _flow
from prefect.flows import load_flow_from_entrypoint
from prefect.settings import PREFECT_API_URL, update_current_profile

LOCAL_SERVER = "http://localhost:4200"
REMOTE_SERVER = os.environ.get("REMOTE_SERVER")


class Action:
    def __init__(self, entrypoint: Flow, name: str):
        self.name = name
        self._flow = entrypoint
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
            work_pool_name="k8-pool",
            image="europe-west1-docker.pkg.dev/giza-platform/prefect-test/prefect-flow-test:v0",
            build=False,
            push=False,
            print_next_steps=False,
        )

    def serve(self, name: str):
        # Deploy the flow locally
        self._flow.serve(name=name, print_starting_message=True)

    def execute(self):
        # Implement the execution logic here
        load_flow_from_entrypoint(self._flow)


def action(func=None, **task_init_kwargs):
    if func is None:
        return partial(action, **task_init_kwargs)

    @wraps(func)
    def safe_func(**kwargs):
        return func(**kwargs)

    safe_func.__name__ = func.__name__
    return _flow(safe_func, **task_init_kwargs)
