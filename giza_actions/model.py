import logging
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union

import numpy as np
import onnx
import onnxruntime as ort
import requests
from diskcache import Cache
from giza import API_HOST
from giza.client import ApiClient, EndpointsClient, ModelsClient, VersionsClient
from giza.schemas.models import Model
from giza.schemas.versions import Version
from giza.utils.enums import Framework, VersionStatus
from osiris.app import (
    create_tensor_from_array,
    deserialize,
    load_data,
    serialize,
    serializer,
)

if TYPE_CHECKING:
    from giza_actions.agent import AgentResult

from giza_actions.utils import get_endpoint_uri

logger = logging.getLogger(__name__)


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
        model_id (int): The unique identifier of the model in the Giza platform.
        version_id (int): The version number of the model in the Giza platform.

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
            raise ValueError("Either model_path or id and version must be provided.")

        if model_path is None and (id is None or version is None):
            raise ValueError("Both id and version must be provided.")

        if model_path and (id or version):
            raise ValueError("Either model_path or id and version must be provided.")

        if model_path and id and version:
            raise ValueError(
                "Only one of model_path or id and version should be provided."
            )

        if model_path:
            if ".onnx" in model_path:
                self.session = ort.InferenceSession(model_path)
            # TODO (@alejandromartinezgotor): if ".json" in model_path create session for non-verifiable inference.
        elif id and version:
            self.model_id = id
            self.version_id = version
            self.model_client = ModelsClient(API_HOST)
            self.version_client = VersionsClient(API_HOST)
            self.api_client = ApiClient(API_HOST)
            self.endpoints_client = EndpointsClient(API_HOST)
            self._get_credentials()
            self.model = self._get_model(id)
            self.version = self._get_version(version)
            self.framework = self.version.framework
            self.uri = self._retrieve_uri()
            self.endpoint_id = self._get_endpoint_id()
            self._cache = Cache(os.path.join(os.getcwd(), "tmp", "cachedir"))
            self.session = self._set_session()
            if output_path is not None:
                self._output_path = output_path
            else:
                self._output_path = os.path.join(
                    tempfile.gettempdir(),
                    f"{self.model_id}_{self.version_id}_{self.model.name}",
                )
            self._download_model()

    def _get_endpoint_id(self) -> int:
        """
        Retrieves the endpoint id for the deployed model.

        Returns:
            The endpoint id for the deployed model.
        """
        deployments_list = self.endpoints_client.list(
            params={
                "model_id": self.model.id,
                "version_id": self.version.version,
                "is_active": True,
            }
        )

        if len(deployments_list.root) == 1:
            return deployments_list.root[0].id
        elif len(deployments_list.root) > 1:
            raise ValueError("Multiple versions deployed for the same model")
        else:
            raise ValueError("No active deployments found")

    def _retrieve_uri(self) -> str:
        """
        Retrieves the URI for making prediction requests to a deployed model.

        Args:
            version_id (int): The version number of the model.

        Returns:
            The URI for making prediction requests to the deployed model.
        """
        # Different URI per framework
        uri = get_endpoint_uri(self.model.id, self.version.version)
        if self.framework == Framework.CAIRO:
            return f"{uri}/cairo_run"
        else:
            return f"{uri}/predict"

    def _get_model(self, model_id: int) -> Model:
        """
        Retrieves the model specified by model_id.

        Args:
            model_id (int): The unique identifier of the model.

        Returns:
            The model.
        """
        return self.model_client.get(model_id)

    def _get_version(self, version_id: int) -> Version:
        """
        Retrieves the version of the model specified by model id and version id.

        Args:
            version_id (int): The version number of the model.

        Returns:
            The version of the model.
        """
        return self.version_client.get(self.model.id, version_id)

    def _set_session(self) -> Optional[ort.InferenceSession]:
        """
        Set onnxruntime session for the model specified by model id.

        Raises:
            ValueError: If the model version status is not completed.
        """

        if self.version.status != VersionStatus.COMPLETED:
            raise ValueError(
                f"Model version status is not completed {self.version.status}"
            )

        try:
            self._download_model()

            if self._output_path in self._cache:
                file_path = Path(self._cache.get(self._output_path))
                with open(file_path, "rb") as f:
                    onnx_model = f.read()

            return ort.InferenceSession(onnx_model)

        except Exception as e:
            logger.info(f"Could not download model: {e}")
            return None

    def _download_model(self) -> None:
        """
        Downloads the model specified by model id and version id to the given output_path.

        Args:
            output_path (str): The file path where the downloaded model should be saved.

        Raises:
            ValueError: If the model version status is not completed.
        """

        if self.version.status != VersionStatus.COMPLETED:
            raise ValueError(
                f"Model version status is not completed {self.version.status}"
            )

        if self._output_path not in self._cache:
            onnx_model = self.version_client.download_original(
                self.model.id, self.version.version
            )

            logger.info("Model is ready, downloading! ✅")

            if (".onnx" or ".json") in self._output_path:
                save_path = Path(self._output_path)
            else:
                save_path = Path(f"{self._output_path}.onnx")

            with open(save_path, "wb") as f:
                f.write(onnx_model)

            self._cache[self._output_path] = save_path

            logger.info(f"Model saved at: {save_path} ✅")
        else:
            logger.info(f"Model already downloaded at: {self._output_path} ✅")

    def _get_credentials(self) -> None:
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
        fp_impl: str = "FP16x16",
        custom_output_dtype: Optional[str] = None,
        model_category="ONNX_ORION",
        job_size: str = "M",
        dry_run: bool = False,
    ) -> Optional[Union[Tuple[Any, Any], "AgentResult"]]:
        """
        Makes a prediction using either a local ONNX session or a remote deployed model, depending on the
        instance configuration.

        Args:
            input_file (Optional[str]): The path to the input file for prediction. Defaults to None.
            input_feed (Optional[Dict]): A dictionary containing the input data for prediction. Defaults to None.
            verifiable (bool): A flag indicating whether to use the verifiable computation endpoint. Defaults to False.
            fp_impl (str): The fixed point implementation to use, when computed in verifiable mode. Defaults to "FP16x16".
            custom_output_dtype (Optional[str]): Specify the data type of the result when computed in verifiable mode. Defaults to None.
            model_category (str): The category of model. "ONNX_ORION" | "XGB" | "LGBM"

        Returns:
            A tuple (predictions, request_id) where predictions is the result of the prediction and request_id
            is the identifier of the prediction request if verifiable computation is used, otherwise None.

        Raises:
            ValueError: If required parameters are not provided or the session is not initialized.
        """
        try:
            logger.info("Predicting")
            if verifiable:
                if not self.uri:
                    raise ValueError("Model has not been deployed")

                # Non common arguments should be named parameters
                payload = self._format_inputs_for_framework(
                    input_file,
                    input_feed,
                    fp_impl=fp_impl,
                    model_category=model_category,
                    job_size=job_size,
                )

                if dry_run:
                    payload["dry_run"] = True

                response = requests.post(self.uri, json=payload)

                try:
                    response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    logger.error(f"An error occurred in predict: {e}")
                    error_message = f"Deployment predict error: {response.text}"
                    logger.error(error_message)
                    raise e

                body = response.json()
                serialized_output = body["result"]
                request_id = body["request_id"]

                if self.framework == Framework.CAIRO:
                    logger.info("Serialized: %s", serialized_output)

                    if model_category == "ONNX_ORION":
                        if custom_output_dtype is None:
                            output_dtype = self._get_output_dtype()
                        else:
                            output_dtype = custom_output_dtype
                    elif model_category in ["XGB", "LGBM"]:
                        output_dtype = "i32"

                    logger.debug("Output dtype: %s", output_dtype)
                    preds = self._parse_cairo_response(
                        serialized_output, output_dtype, model_category
                    )

                elif self.framework == Framework.EZKL:
                    preds = np.array(serialized_output[0])
                return (preds, request_id)
            # Here we are returning different things, Tuple vs np.ndarray
            # TODO: make it consistent
            else:
                if self.session is None:
                    raise ValueError("Session is not initialized.")
                if input_feed is None:
                    raise ValueError("Input feed is none")
                preds = self.session.run(None, input_feed)[0]
                return (preds, None)
        except Exception as e:
            logger.error(f"An error occurred in predict: {e}")
            raise e

    def _format_inputs_for_framework(self, *args: Any, **kwargs: Any) -> Any:
        """
        Formats the inputs for a prediction request for a specific framework.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        match self.framework:
            case Framework.CAIRO:
                return self._format_inputs_for_cairo(*args, **kwargs)
            case Framework.EZKL:
                return self._format_inputs_for_ezkl(*args, **kwargs)
            case _:
                # This should never happen
                raise ValueError(f"Unsupported framework: {self.framework}")

    def _format_inputs_for_cairo(
        self,
        input_file: Optional[str],
        input_feed: Optional[Dict],
        fp_impl: str,
        model_category: str,
        job_size: str,
    ) -> Dict[str, str]:
        """
        Formats the inputs for a prediction request using OrionRunner.

        Parameters:
            input_file (Optional[str]): Path to the input file for prediction.
            input_feed (Optional[Dict]): Dictionary containing the input data for prediction.
            fp_impl (str): The fixed point implementation to be used.
            model_category (str): The category of the model, which can be one of 'ONNX_ORION', 'XGB', or 'LGBM'.
            job_size (str): Description or identifier for the size of the job.

        Returns:
            Dict: A dictionary representing the formatted inputs for the Cairo prediction request.
        """
        formatted_args = []

        if input_file:
            formatted_args.append(serialize(input_file, model_category))

        if input_feed:
            for name, value in input_feed.items():
                if isinstance(value, np.ndarray):
                    if model_category == "ONNX_ORION":
                        tensor = create_tensor_from_array(value, fp_impl)
                    elif model_category in ["XGB", "LGBM"]:
                        tensor = value * 100000
                        tensor = tensor.astype(np.int64)
                    else:
                        tensor = create_tensor_from_array(value, "FP16x16")
                    formatted_args.append(serializer(tensor))

        return {"job_size": job_size, "args": " ".join(formatted_args)}

    def _format_inputs_for_ezkl(
        self,
        input_file: str,
        input_feed: Dict,
        job_size: str,
        *args: Any,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Formats the inputs for a prediction request for EZKL.

        Args:
            input_file (str): The path to the input file for prediction.
            input_feed (Dict): A dictionary containing the input data for prediction.

        Returns:
            dict: A dictionary representing the formatted inputs for the EZKL prediction request.
        """
        if input_file is not None:
            data = load_data(input_file).reshape([-1])
        elif input_feed is not None:
            match input_feed:
                case dict():
                    data = input_feed["input_data"]
                case list():
                    data = input_feed
                case np.ndarray():
                    data = input_feed.reshape([-1])
                case _:
                    raise ValueError(
                        "Invalid input_feed format. Must be a dictionary with 'input_data' containintg the data array."
                    )
        return {"input_data": [data], "job_size": job_size}

    def _parse_cairo_response(
        self, response: str, data_type: str, model_category: str
    ) -> str:
        """
        Parses the response from a OrionRunner prediction request.

        Args:
            response (str): The serialized response from the Cairo prediction request.
            data_type (str): The data type to which the response should be deserialized.
            fp_impl (str): The fixed point implementation used.

        Returns:
            The deserialized prediction result.
        """
        return deserialize(response, data_type, framework=model_category)

    def _get_output_dtype(self) -> Optional[str]:
        """
        Retrieve the Cairo output data type base on the operator type of the final node.

        Returns:
            The output dtype as a string.
        """

        self._download_model()

        if self._output_path in self._cache:
            file_path = Path(self._cache.get(self._output_path))
            with open(file_path, "rb") as f:
                file = f.read()

        model = onnx.load_model_from_string(file)
        graph = model.graph
        output_tensor_name = graph.output[0].name

        def find_producing_node(
            graph: onnx.GraphProto, tensor_name: str
        ) -> Optional[onnx.NodeProto]:
            for node in graph.node:
                if tensor_name in node.output:
                    return node
            return None

        final_node = find_producing_node(graph, output_tensor_name)
        if final_node is None:
            return None
        optype = final_node.op_type

        match optype:
            case "TreeEnsembleClassifier":
                return "(Span<u32>, MutMatrix<FP16x16>)"

            case "TreeEnsembleRegressor":
                return "MutMatrix::<FP16x16>"

            case "LinearClassifier":
                return "(Span<u32>, Tensor<FP16x16>)"
            case _:
                return "Tensor<FP16x16>"
