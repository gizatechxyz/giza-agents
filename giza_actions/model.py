import json
import logging
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import onnxruntime as ort
import requests
from giza import API_HOST
from giza.client import ApiClient, ModelsClient, VersionsClient
from giza.utils.enums import VersionStatus
from osiris.app import create_tensor_from_array, deserialize, serialize, serializer

from giza_actions.utils import get_deployment_uri


class GizaModel:
    def __init__(
        self,
        model_path: Optional[str] = None,
        id: Optional[int] = None,
        version: Optional[int] = None,
        output_path: Optional[str] = None,
    ):
        if model_path is None and id is None and version is None:
            raise ValueError(
                "Either model_path or id and version must be provided.")

        if model_path is None and (id is None or version is None):
            raise ValueError("Both id and version must be provided.")

        if model_path and (id or version):
            raise ValueError(
                "Either model_path or id and version must be provided.")

        if model_path:
            self.session = ort.InferenceSession(model_path)
        elif id and version:
            self.model_client = ModelsClient(API_HOST)
            self.version_client = VersionsClient(API_HOST)
            self.api_client = ApiClient(API_HOST)
            self.uri = get_deployment_uri(id, version)
            self._get_credentials()
            self.session = None
            if output_path:
                self._download_model(id, version, output_path)

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

    def predict(
        self,
        input_file: Optional[str] = None,
        input_feed: Optional[Dict] = None,
        verifiable: bool = False,
        fp_impl="FP16x16",
        output_dtype: str = "tensor_fixed_point",
    ):
        try:
            if verifiable:
                if not self.uri:
                    raise ValueError("Model has not been deployed")

                endpoint = f"{self.uri}/cairo_run"

                cairo_payload = self._format_inputs_for_cairo(
                    input_file, input_feed, fp_impl
                )

                response = requests.post(endpoint, json=cairo_payload)

                if response.status_code == 200:
                    serialized_output = json.dumps(response.json()["result"])
                    request_id = json.dumps(response.json()["request_id"])

                    preds = self._parse_cairo_response(
                        serialized_output, output_dtype, fp_impl
                    )
                    return (preds, request_id)
                else:
                    error_message = f"OrionRunner service error: {response.text}"
                    logging.error(error_message)
                    raise Exception(error_message)

            else:
                if self.session is None:
                    raise ValueError("Session is not initialized.")
                if input_feed is None:
                    raise ValueError("Input feed is none")
                preds = self.session.run(None, input_feed)[0]
                return preds
        except Exception as e:
            logging.error(f"An error occurred in predict: {e}")
            return (None, None)

    def _format_inputs_for_cairo(
        self, input_file: Optional[str], input_feed: Optional[Dict], fp_impl
    ):
        serialized = None

        if input_file is not None:
            serialized = serialize(input_file, fp_impl)

        if input_feed is not None:
            for name in input_feed:
                value = input_feed[name]
                if isinstance(value, np.ndarray):
                    tensor = create_tensor_from_array(value, fp_impl)
                    serialized = serializer(tensor)
                else:
                    serialized = serializer(value)

        return {"job_size": "M", "args": serialized}

    def _parse_cairo_response(self, response, data_type: str, fp_impl):
        return deserialize(response, data_type, fp_impl)
