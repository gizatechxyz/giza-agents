from unittest.mock import *
import pytest
from giza.schemas.endpoints import Endpoint, EndpointsList
from giza_actions.utils import get_endpoint_uri

endpoint_data = Endpoint(id=999, size="S", is_active=True, model_id=999, version_id=999, uri="testing.uri")
endpoint_list = EndpointsList(root=[endpoint_data])
@patch("giza.client.EndpointsClient.list", return_value=endpoint_list)
def test_get_endpoint_uri_successful(mock_get):
    """
    Tests successful retrieval of the deployment URI for a model and version.
    """
    uri = get_endpoint_uri(model_id=788, version_id=23)
    assert uri is "testing.uri"
    mock_get.assert_called_once()

endpoint_list = EndpointsList(root=[])
@patch("giza.client.EndpointsClient.list", return_value=endpoint_list)
def test_get_endpoint_uri_not_found(mock_get):
    """
    Tests the case where no active deployment is found for the model and version.
    """
    uri = get_endpoint_uri(model_id=516, version_id=19)
    assert uri is None
    mock_get.assert_called_once()