from unittest.mock import *
import pytest
from giza.schemas.endpoints import EndpointCreate, Endpoint
from giza.schemas.models import ModelCreate
from giza_actions.utils import get_endpoint_uri

endpoint_data = Endpoint(id=152, size="S", is_active=True, model_id=516, version_id=12)
@patch("giza_actions.utils.get_endpoint_uri", return_value=endpoint_data)
def test_get_endpoint_uri_successful(mock_get):
    """
    Tests successful retrieval of the deployment URI for a model and version.
    """
    uri = get_endpoint_uri(model_id=516, version_id=12)
    assert uri != None
    
@patch("giza_actions.utils.get_endpoint_uri", return_value=endpoint_data)
def test_get_endpoint_uri_not_found(mock_get):
    """
    Tests the case where no active deployment is found for the model and version.
    """
    uri = get_endpoint_uri(model_id=516, version_id=19)
    assert uri is None
