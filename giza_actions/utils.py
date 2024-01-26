from giza import API_HOST
from giza.client import WorkspaceClient, DeploymentsClient


def get_workspace_uri():
    """
    Retrieves the URI of the current workspace.

    This function creates a WorkspaceClient instance using the API_HOST and
    calls its get method to retrieve the current workspace. It then returns
    the URL of the workspace.

    Returns:
        str: The URL of the current workspace.
    """
    client = WorkspaceClient(API_HOST)
    workspace = client.get()
    return workspace.url


def get_deployment_uri(model_id: int, version_id: int):
    """
    Get the deployment URI associated with a specific model and version.

    Args:
        model_id (int): The ID of the model.
        version_id (int): The ID of the version.

    This function initializes a DeploymentsClient instance using the API_HOST and
    retrieves the deployment URI using its list method. The resulting URL of the
    deployment is returned.

    Returns:
        str: The URI of the deployment.
    """
    client = DeploymentsClient(API_HOST)
    deployments_list = client.list(model_id, version_id)

    deployments = deployments_list.__root__

    if deployments:
        return deployments[0].uri
    else:
        return None
