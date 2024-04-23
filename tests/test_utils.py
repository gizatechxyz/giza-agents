from unittest.mock import patch

from giza.schemas.endpoints import Endpoint, EndpointsList

from giza_actions.utils import get_endpoint_uri


@patch("giza.client.EndpointsClient.list")
def test_get_endpoint_uri_successful(mock_get):
    """
    Tests successful retrieval of the deployment URI for a model and version.
    """
    endpoint_data = Endpoint(
        id=999,
        size="S",
        is_active=True,
        model_id=999,
        version_id=999,
        uri="testing.uri",
    )
    endpoint_list = EndpointsList(root=[endpoint_data])
    mock_get.return_value = endpoint_list
    uri = get_endpoint_uri(model_id=788, version_id=23)
    assert uri == "testing.uri"
    mock_get.assert_called_once()


@patch("giza.client.EndpointsClient.list")
def test_get_endpoint_uri_not_found(mock_list):
    """
    Tests the case where no active deployment is found for the model and version.
    """
    endpoint_list = EndpointsList(root=[])
    mock_list.return_value = endpoint_list
    uri = get_endpoint_uri(model_id=516, version_id=19)
    assert uri is None
    mock_list.assert_called_once()
