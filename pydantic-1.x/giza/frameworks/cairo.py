import json
import sys
import time
import zipfile
from pathlib import Path
from typing import Optional

import typer
from pydantic import ValidationError
from requests import HTTPError
from rich import print_json
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.spinner import Spinner

from giza import API_HOST
from giza.client import (
    DeploymentsClient,
    JobsClient,
    ModelsClient,
    ProofsClient,
    VersionsClient,
)
from giza.options import DEBUG_OPTION
from giza.schemas.deployments import DeploymentCreate, DeploymentsList
from giza.schemas.jobs import Job, JobCreate
from giza.schemas.models import ModelCreate
from giza.schemas.proofs import Proof
from giza.schemas.versions import VersionCreate, VersionUpdate
from giza.utils import Echo, echo, get_response_info
from giza.utils.enums import (
    Framework,
    JobKind,
    JobSize,
    JobStatus,
    ServiceSize,
    VersionStatus,
)
from giza.utils.misc import download_model_or_sierra

app = typer.Typer()


def prove(
    data: list[str],
    debug: Optional[bool],
    size: JobSize = JobSize.S,
    framework: Framework = Framework.CAIRO,
    output_path: str = "zk.proof",
) -> None:
    """
    Command to prove as spceific cairo program, previously converted to CASM.
    This will create a proving job and check the status, once it finishes if COMPLETED the proof is downloaded at the output path
    The daily jobs allowed are rate limited by the backend.

    Args:
        data: main CASM file
        size: Size of the job, allowed values are S, M, L and XL. Defaults to S.
        output_path: output path of the zk proof generated in the job
        debug (Optional[bool], optional): Whether to add debug information, will show requests, extra logs and traceback if there is an Exception. Defaults to DEBUG_OPTION (False).

    Raises:
        ValidationError: input fields are validated, if these are not suitable the exception is raised
        HTTPError: request error to the API, 4XX or 5XX
    """
    try:
        client = JobsClient(API_HOST)
        trace_path, memory_path = data
        with open(trace_path, "rb") as trace, open(memory_path, "rb") as memory:
            job: Job = client.create(
                JobCreate(size=size, framework=framework), trace, memory
            )
        echo(f"Proving job created with name '{job.job_name}' and id -> {job.id} ✅")
        with Live() as live:
            while True:
                current_job: Job = client.get(job.id)
                if current_job.status == JobStatus.COMPLETED:
                    live.update(echo.format_message("Proving job is successful ✅"))
                    break
                elif current_job.status == JobStatus.FAILED:
                    live.update(
                        echo.format_error(
                            f"Proving Job with name '{current_job.job_name}' and id {current_job.id} failed"
                        )
                    )
                    sys.exit(1)
                else:
                    live.update(
                        echo.format_message(
                            f"Job status is '{current_job.status}', elapsed {current_job.elapsed_time}s"
                        )
                    )
                    time.sleep(20)
        with open(output_path, "wb") as f:
            proof_client = ProofsClient(API_HOST)
            proof: Proof = proof_client.get_by_job_id(current_job.id)
            echo("Proof metrics:")
            print_json(json.dumps(proof.metrics))
            f.write(proof_client.download(proof.id))
            echo(f"Proof saved at: {output_path}")
    except ValidationError as e:
        echo.error("Job validation error")
        echo.error("Review the provided information")
        if debug:
            raise e
        echo.error(str(e))
        sys.exit(1)
    except HTTPError as e:
        info = get_response_info(e.response)
        echo.error("⛔️Could not create the job")
        echo.error(f"⛔️Detail -> {info.get('detail')}⛔️")
        echo.error(f"⛔️Status code -> {info.get('status_code')}⛔️")
        echo.error(f"⛔️Error message -> {info.get('content')}⛔️")
        echo.error(
            f"⛔️Request ID: Give this to an administrator to trace the error -> {info.get('request_id')}⛔️"
        ) if info.get("request_id") else None
        if debug:
            raise e
        sys.exit(1)


def deploy(
    model_id: int,
    version_id: int,
    data: Optional[str] = None,
    size: ServiceSize = ServiceSize.S,
    debug: Optional[bool] = DEBUG_OPTION,
) -> str:
    """
    Command to deploy a specific version of a model. This will create a deployment for the specified version and check the status, once it finishes if COMPLETED the deployment is ready to be used.

    Args:
        data: main SIERRA file
        model_id: model id to deploy
        version_id: version id to deploy
        size: Size of the service, allowed values are S, M, L and XL. Defaults to S.
        debug (Optional[bool], optional): Whether to add debug information, will show requests, extra logs and traceback if there is an Exception. Defaults to DEBUG_OPTION (False).

    Raises:
        ValidationError: input fields are validated, if these are not suitable the exception is raised
        HTTPError: request error to the API, 4XX or 5XX
    """
    try:
        client = DeploymentsClient(API_HOST)

        deployments_list: DeploymentsList = client.list(model_id, version_id)
        deployments: dict = json.loads(deployments_list.json())

        if len(deployments) > 0:
            echo.info(
                f"Deployment for model id {model_id} and version id {version_id} already exists! ✅"
            )
            echo.info(f"Deployment id -> {deployments[0]['id']} ✅")
            echo.info(f'You can start doing inferences at: {deployments[0]["uri"]} 🚀')
            sys.exit(1)

        spinner = Spinner(name="aesthetic", text="Creating deployment!")

        with Live(renderable=spinner):
            if data is None:
                deployment = client.create(
                    model_id,
                    version_id,
                    DeploymentCreate(
                        size=size,
                        model_id=model_id,
                        version_id=version_id,
                    ),
                    None,
                )
            else:
                with open(data, "rb") as sierra:
                    deployment = client.create(
                        model_id,
                        version_id,
                        DeploymentCreate(
                            size=size,
                            model_id=model_id,
                            version_id=version_id,
                        ),
                        sierra,
                    )

    except ValidationError as e:
        echo.error("Deployment validation error")
        echo.error("Review the provided information")
        if debug:
            raise e
        echo.error(str(e))
        sys.exit(1)
    except HTTPError as e:
        info = get_response_info(e.response)
        echo.error("⛔️Could not create the deployment")
        echo.error(f"⛔️Detail -> {info.get('detail')}⛔️")
        echo.error(f"⛔️Status code -> {info.get('status_code')}⛔️")
        echo.error(f"⛔️Error message -> {info.get('content')}⛔️")
        echo.error(
            f"⛔️Request ID: Give this to an administrator to trace the error -> {info.get('request_id')}⛔️"
        ) if info.get("request_id") else None
        if debug:
            raise e
        sys.exit(1)
    echo("Deployment is successful ✅")
    echo(f"Deployment created with id -> {deployment.id} ✅")
    echo(f"Deployment created with endpoint URL: {deployment.uri} 🎉")
    return deployment


def transpile(
    model_path: str,
    model_id: int,
    desc: str,
    model_desc: str,
    output_path: str,
    download_model: bool,
    download_sierra: bool,
    debug: Optional[bool],
) -> None:
    """
    This function is responsible for transpiling a model. The overall objective is to prepare a model for use by converting it into a different format (transpiling).
    The function performs the following steps:

    1. Checks if a model_id is provided. If not, it extracts the model_name from the model_path.
    2. If a model description is provided and a model_id is also provided, it ignores the provided description.
    3. It then attempts to retrieve the model. If the model does not exist, it creates a new one.
    4. The function then creates a new version for the model, uploads the model file, and updates the status to UPLOADED.
    5. It then continuously checks the status of the version until it is either COMPLETED or FAILED.
    6. If the status is COMPLETED, it downloads the model to the specified path.
    7. If any errors occur during this process, they are handled and appropriate error messages are displayed.

    Args:
        model_path (str): Path of the model to transpile.
        model_id (int, optional): The ID of the model where a new version will be created. Defaults to None.
        desc (int, optional): Description of the version. Defaults to None.
        model_desc (int, optional): Description of the Model to create if model_id is not provided. Defaults to None.
        output_path (str, optional): The path where the cairo model will be saved. Defaults to "cairo_model".
        download_model (bool): A flag used to determine whether to download the model or not.
        download_sierra (bool): A flag used to determine whether to download the sierra or not.
        debug (bool, optional): A flag used to determine whether to raise exceptions or not. Defaults to DEBUG_OPTION.

    Raises:
        ValidationError: If there is a validation error with the model or version.
        HTTPError: If there is an HTTP error while communicating with the server.
    """
    echo = Echo(debug=debug)
    if model_path is None:
        echo.error("No model name provided, please provide a model path ⛔️")
        sys.exit(1)
    if model_id is None:
        model_name = model_path.split("/")[-1].split(".")[0]
        echo("No model id provided, checking if model exists ✅ ")
        echo(f"Model name is: {model_name}")
    if model_desc is not None and model_id is not None:
        echo(
            "Model description is not required when model id is provided, ignoring provided description ✅ "
        )
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            model_task = progress.add_task(
                description="Retrieving Model...", total=None
            )
            echo.debug(f"Reading model from path: {model_path}")
            models_client = ModelsClient(API_HOST)
            if model_id is None:
                model = models_client.get_by_name(model_name)
                if model is not None:
                    echo("Model already exists, using existing model ✅ ")
                    echo(f"Model found with id -> {model.id}! ✅")
                else:
                    model_create = ModelCreate(name=model_name, description=model_desc)
                    model = models_client.create(model_create)
                    echo(f"Model Created with id -> {model.id}! ✅")
            else:
                model = models_client.get(model_id)
                echo(f"Model found with id -> {model.id}! ✅")
            progress.update(model_task, completed=True, visible=False)
            version_task = progress.add_task(
                description="Creating Version...", total=None
            )
            client = VersionsClient(API_HOST)
            version_create = VersionCreate(
                description=desc if desc else "Intial version",
                size=Path(model_path).stat().st_size,
                framework=Framework.CAIRO,
            )
            version, upload_url = client.create(
                model.id, version_create, model_path.split("/")[-1]
            )
            echo(f"Version Created with id -> {version.version}! ✅")
            progress.update(version_task, completed=True, visible=False)
            echo("Sending model for transpilation ✅ ")
            with open(model_path, "rb") as f:
                client._upload(upload_url, f)
                echo.debug("Model Uploaded! ✅")

            client.update(
                model.id, version.version, VersionUpdate(status=VersionStatus.UPLOADED)
            )

            progress.add_task(description="Transpiling Model...", total=None)
            start_time = time.time()
            while True:
                version = client.get(model.id, version.version)
                if version.status not in (
                    VersionStatus.COMPLETED,
                    VersionStatus.FAILED,
                    VersionStatus.PARTIALLY_SUPPORTED,
                ):
                    spent = time.time() - start_time
                    echo.debug(
                        f"[{spent:.2f}s]Transpilation is not ready yet, retrying in 10s"
                    )
                    time.sleep(10)
                elif version.status == VersionStatus.COMPLETED:
                    echo.debug("Transpilation is ready, downloading! ✅")
                    echo(
                        "Transpilation is fully compatible. Version compiled and Sierra is saved at Giza ✅"
                    )
                    break
                elif version.status == VersionStatus.PARTIALLY_SUPPORTED:
                    echo.warning(
                        "🔎 Transpilation is partially supported. "
                        "Some operators are not yet supported in the Transpiler/Orion"
                    )
                    echo.warning(
                        "Please check the compatibility list in Orion: "
                        "https://cli.gizatech.xyz/frameworks/cairo/transpile#supported-operators"
                    )
                    break
                elif version.status == VersionStatus.FAILED:
                    echo.error("⛔️ Transpilation failed! ⛔️")
                    echo.error(f"⛔️ Reason -> {version.message} ⛔️")
                    sys.exit(1)
    except ValidationError as e:
        echo.error("Version validation error")
        echo.error("Review the provided information")
        if debug:
            raise e
        echo.error(str(e))
        sys.exit(1)
    except HTTPError as e:
        info = get_response_info(e.response)
        echo.error("⛔️Error at transpilation⛔️")
        echo.error(f"⛔️Detail -> {info.get('detail')}⛔️")
        echo.error(f"⛔️Status code -> {info.get('status_code')}⛔️")
        echo.error(f"⛔️Error message -> {info.get('content')}⛔️")
        echo.error(
            f"⛔️Request ID: Give this to an administrator to trace the error -> {info.get('request_id')}⛔️"
        ) if info.get("request_id") else None
        if debug:
            raise e
        sys.exit(1)

    try:
        if download_model or download_sierra:
            params = {
                "download_model": download_model,
                "download_sierra": download_sierra,
            }
            downloads = client.download(model.id, version.version, params)
            for name, content in downloads.items():
                echo(f"Downloading {name} ✅")
                download_model_or_sierra(content, output_path, name)
                echo(f"{name} saved at: {output_path}")
    except zipfile.BadZipFile as zip_error:
        echo.error("Something went wrong with the transpiled file")
        echo.error(f"Error -> {zip_error.args[0]}")
        if debug:
            raise zip_error
        sys.exit(1)


def verify(
    proof_id: Optional[int],
    model_id: Optional[int],
    version_id: Optional[int],
    proof: Optional[str] = None,
    debug: Optional[bool] = False,
    size: JobSize = JobSize.S,
):
    """
    Create a verification job.
    This command will create a verification job with the provided proof id.
    The job size, model id, and version id can be optionally specified.
    """
    echo = Echo()
    if not model_id or not version_id:
        if proof_id:
            echo.error("Model id and version id must be provided along with proof id.")
            sys.exit(1)
        echo.warning(
            "Model id and version id are not provided and proof won't be linked."
        )
    if proof_id and proof:
        echo.error("You can only use either proof_id or proof, but not both.")
        sys.exit(1)
    try:
        job: Job
        client = JobsClient(API_HOST)
        if proof_id:
            job = client.create(
                JobCreate(
                    size=size,
                    framework=Framework.CAIRO,
                    kind=JobKind.VERIFY,
                    model_id=model_id,
                    version_id=version_id,
                    proof_id=proof_id,
                ),
                None,
            )
        elif proof:
            with open(proof, "rb") as data:
                job = client.create(
                    JobCreate(
                        size=size,
                        framework=Framework.CAIRO,
                        kind=JobKind.VERIFY,
                        model_id=model_id,
                        version_id=version_id,
                    ),
                    data,
                )
        echo(
            f"Verification job created with name '{job.job_name}' and id -> {job.id} ✅"
        )
        with Live() as live:
            while True:
                current_job: Job = client.get(job.id, params={"kind": JobKind.VERIFY})
                if current_job.status == JobStatus.COMPLETED:
                    live.update(echo.format_message("Verification job is successful ✅"))
                    break
                elif current_job.status == JobStatus.FAILED:
                    live.update(
                        echo.format_error(
                            f"Verification Job with name '{current_job.job_name}' and id {current_job.id} failed"
                        )
                    )
                    sys.exit(1)
                else:
                    live.update(
                        echo.format_message(
                            f"Job status is '{current_job.status}', elapsed {current_job.elapsed_time}s"
                        )
                    )
                    time.sleep(20)
    except ValidationError as e:
        echo.error("Job validation error")
        echo.error("Review the provided information")
        if debug:
            raise e
        echo.error(str(e))
        sys.exit(1)
    except HTTPError as e:
        info = get_response_info(e.response)
        echo.error("⛔️Could not create the job")
        echo.error(f"⛔️Detail -> {info.get('detail')}⛔️")
        echo.error(f"⛔️Status code -> {info.get('status_code')}⛔️")
        echo.error(f"⛔️Error message -> {info.get('content')}⛔️")
        echo.error(
            f"⛔️Request ID: Give this to an administrator to trace the error -> {info.get('request_id')}⛔️"
        ) if info.get("request_id") else None
        if debug:
            raise e
        sys.exit(1)
