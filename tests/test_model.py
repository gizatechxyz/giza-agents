# TODO: Implement a test env. 

import numpy as np

from giza_actions.model import GizaModel


def test_predict_success():
    model = GizaModel(id=50, version=2)

    arr = np.array([[1, 2], [3, 4]], dtype=np.uint32)

    result = model.predict(
        input_feed={"arr_1": arr}, verifiable=True, output_dtype="tensor_int"
    )

    assert np.array_equal(result, arr)


def test_predict_success_with_file():
    model = GizaModel(id=50, version=2)

    expected = np.array([[1, 2], [3, 4]], dtype=np.uint32)

    result = model.predict(
        input_file="tests/data/simple_tensor.csv",
        verifiable=True,
        output_dtype="tensor_int",
    )

    assert np.array_equal(result, expected)
