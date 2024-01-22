from giza import API_HOST
from giza.client import WorkspaceClient


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
