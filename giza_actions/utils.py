from giza import API_HOST
from giza.client import WorkspaceClient


def get_workspace_uri():
    client = WorkspaceClient(API_HOST)
    workspace = client.get()
    return workspace.url
