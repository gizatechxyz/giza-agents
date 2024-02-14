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
    """
    A class to manage the lifecycle and predictions of models using both local ONNX runtime sessions and
    remote deployments via the Giza SDK.

    Attributes:
        session (ort.InferenceSession | None): An ONNX runtime inference session for local model predictions.
        model_client (ModelsClient): Client to interact with the models endpoint of the Giza API.
        version_client (VersionsClient): Client to interact with the versions endpoint of the Giza API.
        api_client (ApiClient): General client for interacting with the Giza API.
        uri (str): The URI for making prediction requests to a deployed model.

    Args:
        model_path (Optional[str]): The file path to a local ONNX model. Defaults to None.
        id (Optional[int]): The unique identifier of the model in the Giza platform. Defaults to None.
        version (Optional[int]): The version number of the model in the Giza platform. Defaults to None.
        output_path (Optional[str]): The file path where the downloaded model should be saved. Defaults to None.

    Raises:
        ValueError: If the necessary combination of parameters is not provided.
    """

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
        """
        Downloads the model specified by model_id and version_id to the given output_path.

        Args:
            model_id (int): The unique identifier of the model.
            version_id (int): The version number of the model.
            output_path (str): The file path where the downloaded model should be saved.

        Raises:
            ValueError: If the model version status is not completed.
        """
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
        """
        Retrieves and sets the necessary credentials for API access.
        """
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
        """
        Makes a prediction using either a local ONNX session or a remote deployed model, depending on the
        instance configuration.

        Args:
            input_file (Optional[str]): The path to the input file for prediction. Defaults to None.
            input_feed (Optional[Dict]): A dictionary containing the input data for prediction. Defaults to None.
            verifiable (bool): A flag indicating whether to use the verifiable computation endpoint. Defaults to False.
            fp_impl (str): The fixed point implementation to use, when computed in verifiable mode. Defaults to "FP16x16".
            output_dtype (str): The data type of the result when computed in verifiable mode. Defaults to "tensor_fixed_point".

        Returns:
            A tuple (predictions, request_id) where predictions is the result of the prediction and request_id
            is the identifier of the prediction request if verifiable computation is used, otherwise None.

        Raises:
            ValueError: If required parameters are not provided or the session is not initialized.
        """
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

                    logging.info("Serialized: ", serialized_output)

                    preds = self._parse_cairo_response(
                        serialized_output, output_dtype
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
        """
        Formats the inputs for a prediction request for OrionRunner.

        Args:
            input_file (Optional[str]): The path to the input file for prediction. Defaults to None.
            input_feed (Optional[Dict]): A dictionary containing the input data for prediction. Defaults to None.
            fp_impl (str): The fixed point implementation to use.

        Returns:
            dict: A dictionary representing the formatted inputs for the Cairo prediction request.
        """
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

    def _parse_cairo_response(self, response, data_type: str):
        """
        Parses the response from a OrionRunner prediction request.

        Args:
            response (str): The serialized response from the Cairo prediction request.
            data_type (str): The data type to which the response should be deserialized.
            fp_impl (str): The fixed point implementation used.

        Returns:
            The deserialized prediction result.
        """
        return deserialize(response, data_type)
