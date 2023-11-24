# tests/test_sdk.py

import pytest
from giza.sdk import GizaModel, action, task, model, data_input, Action

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

def test_model_decorator():
    @model(id=1, version=1)
    def test_func(model, name):
        return f"Hello, {name}!"
    assert test_func("World") == "Hello, World!"

def test_data_input_decorator():
    @data_input(dtype="FP16x16")
    def test_func(path):
        return "Hello, World!"
    assert test_func("path") == "Hello, World!"

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
