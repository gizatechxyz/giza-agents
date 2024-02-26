import os  # noqa: E402

from giza_actions.utils import get_workspace_uri  # noqa: E402

os.environ["PREFECT_API_URL"] = f"{get_workspace_uri()}/api"
os.environ["PREFECT_UI_URL"] = get_workspace_uri()

from prefect.deployments import run_deployment  # noqa: E402


def run_action_deployment(name: str, parameters: dict = None):
    deployment_run = run_deployment(name=name, parameters=parameters)
    print(
        f"Deployment run name: {deployment_run.name} exited with state: {deployment_run.state_name}"
    )
    return deployment_run
