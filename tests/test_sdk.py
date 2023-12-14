# tests/test_sdk.py

import numpy as np
import pytest

from giza_actions.action import Action, action
from giza_actions.cairo.data_converter import FixedImpl, to_fp
from giza_actions.cairo.file_manager import CairoData
from giza_actions.model import GizaModel
from giza_actions.task import task


def test_giza_model():
    giza_model = GizaModel(None)
    assert isinstance(giza_model, GizaModel)


def test_action_decorator():
    @action
    def test_func():
        return "Hello, World!"

    assert test_func() == "Hello, World!"


def test_task_decorator():
    @task
    def test_func():
        return "Hello, World!"

    assert test_func() == "Hello, World!"


def test_action_class():
    action = Action(id=1)
    assert isinstance(action, Action)


def test_action_execute_method():
    action = Action(id=1)
    with pytest.raises(NotImplementedError):
        action.execute()


def test_action_apply_method():
    action = Action(id=1)
    with pytest.raises(NotImplementedError):
        action.apply(inference_id=1)


def test_cairo_data_class():
    cairo_data = CairoData("path")
    assert isinstance(cairo_data, CairoData)


def test_data_conversion():
    data = np.array([1, 2, 3])
    converted_data = to_fp(data, FixedImpl.FP16x16)
    assert np.all(converted_data == (data * 2**16).astype(np.int64))
