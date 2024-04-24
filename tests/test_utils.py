from unittest import TestCase, mock

import requests
from giza.schemas.workspaces import Workspace

from giza_actions.utils import get_workspace_uri


@mock.patch("giza.client.WorkspaceClient.get")
def test_get_workspace_uri_successful(mock_get):
    """
    Tests successful retrieval the URI of the current workspace.
    """
    mock_workspace = Workspace(status="test", url="test_url")
    mock_get.return_value = mock_workspace
    workspace_uri = get_workspace_uri()
    assert workspace_uri == "test_url"
    mock_get.assert_called_once()


@mock.patch("giza.client.WorkspaceClient.get")
def test_get_workspace_uri_request_exception(mock_get):
    """
    Tests RequestException in get_workspace_uri method().
    """
    mock_get.side_effect = requests.exceptions.RequestException

    TestCase.assertRaises(
        TestCase, requests.exceptions.RequestException, get_workspace_uri
    )
