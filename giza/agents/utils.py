import json
import logging
from typing import Optional

import requests
from giza.cli import API_HOST
from giza.cli.client import EndpointsClient, WorkspaceClient

logger = logging.getLogger(__name__)


def get_workspace_uri() -> str:
    """
    Retrieves the URI of the current workspace.

    This function creates a WorkspaceClient instance using the API_HOST and
    calls its get method to retrieve the current workspace. It then returns
    the URL of the workspace.

    Returns:
        str: The URL of the current workspace.
    """
    client = WorkspaceClient(API_HOST)
    try:
        workspace = client.get()
    except requests.exceptions.RequestException:
        logger.error("Failed to retrieve workspace")
        logger.error(
            "Please check that you have create a workspaces using the Giza CLI"
        )
        raise
    return workspace.url


def get_endpoint_uri(model_id: int, version_id: int) -> Optional[str]:
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
    client = EndpointsClient(API_HOST)
    deployments_list = client.list(
        params={"model_id": model_id, "version_id": version_id, "is_active": True}
    )

    if len(deployments_list.root) == 1:
        return deployments_list.root[0].uri
    else:
        return None


def read_json(file_path: str) -> dict:
    """
    Read the JSON file from the specified path and return the
    JSON data.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The JSON data.
    """
    with open(file_path) as file:
        return json.load(file)
