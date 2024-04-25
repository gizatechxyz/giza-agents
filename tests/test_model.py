# TODO: Implement a test env.
import os
import tempfile
from unittest.mock import patch

import numpy as np
from giza.schemas.models import Model
from giza.schemas.versions import Version

from giza_actions.model import GizaModel


class ResponseStub:
    def __init__(self, json):
        self._json = json

    def json(self):
        return self._json

    def raise_for_status(self):
        pass


@patch("giza_actions.model.GizaModel._get_credentials")
@patch("giza_actions.model.GizaModel._get_model", return_value=Model(id=50))
@patch(
    "giza_actions.model.GizaModel._get_version",
    return_value=Version(
        version=2,
        framework="CAIRO",
        size=1,
        status="COMPLETED",
        created_date="2022-01-01T00:00:00Z",
        last_update="2022-01-01T00:00:00Z",
    ),
)
@patch("giza_actions.model.GizaModel._set_session")
@patch("giza_actions.model.GizaModel._retrieve_uri")
@patch("giza_actions.model.GizaModel._get_endpoint_id", return_value=1)
@patch(
    "giza_actions.model.requests.post",
    return_value=ResponseStub(
        {"request_id": "123", "result": {"arr_1": [[1, 2], [3, 4]]}}
    ),
)
@patch(
    "giza_actions.model.GizaModel._parse_cairo_response",
    return_value=np.array([[1, 2], [3, 4]], dtype=np.uint32),
)
@patch(
    "giza_actions.model.VersionsClient.download_original", return_value=b"some bytes"
)
def test_predict_success(*args):
    model = GizaModel(id=50, version=2)

    arr = np.array([[1, 2], [3, 4]], dtype=np.uint32)

    result, req_id = model.predict(
        input_feed={"arr_1": arr}, verifiable=True, custom_output_dtype="dummy_type"
    )

    assert np.array_equal(result, arr)
    assert req_id == "123"


@patch("giza_actions.model.GizaModel._get_credentials")
@patch("giza_actions.model.GizaModel._get_model", return_value=Model(id=50))
@patch(
    "giza_actions.model.GizaModel._get_version",
    return_value=Version(
        version=2,
        framework="CAIRO",
        size=1,
        status="COMPLETED",
        created_date="2022-01-01T00:00:00Z",
        last_update="2022-01-01T00:00:00Z",
    ),
)
@patch("giza_actions.model.GizaModel._set_session")
@patch("giza_actions.model.GizaModel._retrieve_uri")
@patch("giza_actions.model.GizaModel._get_endpoint_id", return_value=1)
@patch(
    "giza_actions.model.requests.post",
    return_value=ResponseStub(
        {"request_id": "123", "result": {"arr_1": [[1, 2], [3, 4]]}}
    ),
)
@patch(
    "giza_actions.model.GizaModel._parse_cairo_response",
    return_value=np.array([[1, 2], [3, 4]], dtype=np.uint32),
)
@patch(
    "giza_actions.model.VersionsClient.download_original", return_value=b"some bytes"
)
def test_predict_success_with_file(*args):
    model = GizaModel(id=50, version=2)

    expected = np.array([[1, 2], [3, 4]], dtype=np.uint32)

    with tempfile.TemporaryDirectory() as tempdir:
        input_file = os.path.join(tempdir, "input.csv")
        np.savetxt(input_file, expected, delimiter=",")
        result, req_id = model.predict(
            input_file=input_file,
            verifiable=True,
            custom_output_dtype="tensor_int",
        )

    assert np.array_equal(result, expected)
    assert req_id == "123"


@patch("giza_actions.model.GizaModel._get_credentials")
@patch("giza_actions.model.GizaModel._get_model", return_value=Model(id=50))
@patch(
    "giza_actions.model.GizaModel._get_version",
    return_value=Version(
        version=2,
        framework="CAIRO",
        size=1,
        status="COMPLETED",
        created_date="2022-01-01T00:00:00Z",
        last_update="2022-01-01T00:00:00Z",
    ),
)
@patch("giza_actions.model.GizaModel._set_session")
@patch("giza_actions.model.GizaModel._get_output_dtype")
@patch("giza_actions.model.GizaModel._retrieve_uri")
@patch("giza_actions.model.GizaModel._get_endpoint_id", return_value=1)
@patch(
    "giza_actions.model.VersionsClient.download_original", return_value=b"some bytes"
)
def test_cache_implementation(*args):
    model = GizaModel(id=50, version=2)

    result1 = model._set_session()
    cache_size_after_first_call = len(model._cache)
    result2 = model._set_session()
    cache_size_after_second_call = len(model._cache)
    assert result1 == result2
    assert cache_size_after_first_call == cache_size_after_second_call

    result3 = model._get_output_dtype()
    cache_size_after_third_call = len(model._cache)
    result4 = model._get_output_dtype()
    cache_size_after_fourth_call = len(model._cache)
    assert result3 == result4
    assert cache_size_after_third_call == cache_size_after_fourth_call
