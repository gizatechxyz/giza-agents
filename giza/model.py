from functools import wraps
from typing import Callable

import httpx
import onnxruntime

class GizaModel():

    def __init__(self, id: int, version: int):
        response = httpx.get(f"http://api.onnx.models.com/{id}/{version}")
        self.model = onnxruntime.InferenceSession(response.json())

    def predict(self):
        # self.model.predict()
        pass

def model(func: Callable, id: int, version: int):
    @wraps(func)
    def wrapper(*args, **kwargs):
        model = GizaModel()
        return func(*args, **kwargs)
    return wrapper
