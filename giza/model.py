from functools import wraps
from typing import Callable

import httpx
import onnx
import onnxruntime as ort


class GizaModel():

    def __init__(self, model_path: str, id: int = 0, version: int = 0):
        if id != 0 and version != 0:
            response = httpx.get(f"http://api.onnx.models.com/{id}/{version}")
            self.session = ort.InferenceSession(response.json())
        else:
            model = onnx.load(model_path)
            # Start from ORT 1.10, ORT requires explicitly setting the providers parameter if you want to use execution providers
            # other than the default CPU provider (as opposed to the previous behavior of providers getting set/registered by default
            # based on the build flags) when instantiating InferenceSession.
            # For example, if NVIDIA GPU is available and ORT Python package is built with CUDA, then call API as following:
            # onnxruntime.InferenceSession(path/to/model, providers=['CUDAExecutionProvider']).
            self.session = ort.InferenceSession(model.SerializeToString())


    def predict(self):
        # self.model.predict()
        pass

def model(func: Callable, id: int, version: int):
    @wraps(func)
    def wrapper(*args, **kwargs):
        model = GizaModel()
        return func(*args, **kwargs)
    return wrapper
