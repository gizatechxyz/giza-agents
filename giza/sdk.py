# giza/sdk.py

from functools import wraps
from typing import Callable

import numpy as np
import onnx
import httpx
from prefect import task as prefect_task
from prefect import Flow


class GizaModel:
    def __init__(self, model):
        self.model = model

    def predict(self, input):
        # Implement the prediction logic here
        pass

@prefect_task
def action(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def task(func: Callable):
    @prefect_task
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@prefect_task
def model(id: int, version: int):

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Retrieve the model from the API
            response = httpx.get(f'https://api.giza.com/models/{id}/versions/{version}')
            response.raise_for_status()

            # Load the model using ONNX
            model_data = response.content
            model = onnx.load_model_from_string(model_data)

            # Wrap the model in a GizaModel and pass it to the function
            giza_model = GizaModel(model)
            return func(giza_model, *args, **kwargs)
        return wrapper
    return decorator

@prefect_task
def data_input(dtype: str):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            numpy_array = func(*args, **kwargs)
            return numpy_array_to_cairo_data(numpy_array)
        return wrapper
    return decorator

def numpy_array_to_cairo_data(numpy_array: np.ndarray):
    # Convert numpy array to cairo data here
    pass

class Action:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
        self.flow = None

    def __call__(self, func):
        self.flow = Flow(self.id, tasks=[func])
        return self.flow
    
    def deploy(self):
        # Deploy the flow to the platform
        self.flow.serve(name=self.name)

    def execute(self):
        # Implement the execution logic here
        pass

    def apply(self, inference_id: int):
        # Implement the apply logic here
        pass
