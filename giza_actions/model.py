from functools import wraps
import json
from pathlib import Path
from typing import Callable, Optional, Dict
import numpy as np

import requests
import onnxruntime as ort
from giza import API_HOST
from giza.client import ApiClient, ModelsClient, VersionsClient
from giza.utils.enums import VersionStatus
from osiris.app import serialize, deserialize, serializer, create_tensor_from_array


class GizaModel:
    def __init__(
        self,
        model_path: Optional[str] = None,
        id: Optional[int] = None,
        version: Optional[int] = None,
        output_path: Optional[str] = None,
        orion_runner_service_url: Optional[str] = None,
    ):
        if model_path is None and id is None and version is None:
            raise ValueError(
                "Either model_path or id and version must be provided.")

        if model_path is None and (id is None or version is None):
            raise ValueError("Both id and version must be provided.")

        if model_path and (id or version):
            raise ValueError(
                "Either model_path or id and version must be provided.")

        self.orion_runner_service_url = orion_runner_service_url

        if model_path:
            self.session = ort.InferenceSession(model_path)
        elif id and version:
            self.model_client = ModelsClient(API_HOST)
            self.version_client = VersionsClient(API_HOST)
            self.api_client = ApiClient(API_HOST)
            self._get_credentials()
            self._download_model(id, version, output_path)
            self.session = None

    def _download_model(self, model_id: int, version_id: int, output_path: str):
        version = self.version_client.get(model_id, version_id)

        if version.status != VersionStatus.COMPLETED:
            raise ValueError(
                f"Model version status is not completed {version.status}")

        print("ONNX model is ready, downloading! ✅")
        onnx_model = self.api_client.download_original(
            model_id, version.version)

        model_name = version.original_model_path.split("/")[-1]
        save_path = Path(output_path) / model_name

        with open(save_path, "wb") as f:
            f.write(onnx_model)

        print(f"ONNX model saved at: {save_path}")
        self.session = ort.InferenceSession(save_path)
        print("Model ready for inference with ONNX Runtime! ✅")

    def _get_credentials(self):
        self.api_client.retrieve_token()
        self.api_client.retrieve_api_key()

    def predict(self, input_file: Optional[str] = None, input_feed: Optional[Dict] = None, verifiable: bool = False, fp_impl='FP16x16', output_dtype: str = 'tensor_fixed_point'):
        if verifiable:
            if not self.orion_runner_service_url:
                raise ValueError("Orion Runner service URL must be provided")

            endpoint = f"{self.orion_runner_service_url}/cairo_run"

            cairo_payload = self._format_inputs_for_cairo(
                input_file, input_feed, fp_impl)

            response = requests.post(endpoint, json=cairo_payload)

            if response.status_code == 200:
                preds = self._parse_cairo_response(
                    response.json(), output_dtype, fp_impl)
            else:
                raise Exception(f"OrionRunner service error: {response.text}")

        else:
            if self.session is None:
                raise ValueError("Session is not initialized.")
            if input_feed is None:
                raise ValueError("Input feed is none")
            preds = self.session.run(None, input_feed)[0]
        return preds

    def _format_inputs_for_cairo(self, input_file: Optional[str], input_feed: Optional[Dict], fp_impl) -> str:
        serialized = []

        if input_file is not None:
            serialized.extend(serialize(input, fp_impl))

        if input_feed is not None:
            for name in input_feed:
                value = input_feed[name]
                if isinstance(value, np.ndarray):
                    tensor = create_tensor_from_array(value, fp_impl)
                    serialized.extend(serializer(tensor))
                else:
                    serialized.extend(serializer(value))

        payload = {"args": json.dumps(serialized)}
        return json.dumps(payload)

    def _parse_cairo_response(self, response, data_type: str, fp_impl):
        return deserialize(response, data_type, fp_impl)


def model(func: Callable, id: int, version: int):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
