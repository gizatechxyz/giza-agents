import sys
from typing import Optional

import typer
from pydantic import ValidationError
from requests import HTTPError
from rich import print_json

from giza import API_HOST
from giza.client import DeploymentsClient
from giza.frameworks import cairo
from giza.options import DEBUG_OPTION
from giza.schemas.deployments import DeploymentsList
from giza.schemas.proofs import Proof, ProofList
from giza.utils import echo, get_response_info
from giza.utils.enums import Framework, ServiceSize

app = typer.Typer()


def deploy(
    data: str = typer.Argument(None),
    model_id: int = typer.Option(
        None,
        "--model-id",
        "-m",
        help="The ID of the model where a deployment will be created",
    ),
    version_id: int = typer.Option(
        None, "--version-id", "-v", help="The ID of the version that will be deployed"
    ),
    size: ServiceSize = typer.Option(ServiceSize.S, "--size", "-s"),
    framework: Framework = typer.Option(Framework.CAIRO, "--framework", "-f"),
    debug: Optional[bool] = DEBUG_OPTION,
) -> None:
    if framework == Framework.CAIRO:
        cairo.deploy(
            data=data, model_id=model_id, version_id=version_id, size=size, debug=debug
        )
    elif framework == Framework.EZKL:
        raise NotImplementedError(
            "EZKL deployment is not yet supported, please use Cairo instead"
        )
    else:
        raise typer.BadParameter(
            f"Framework {framework} is not supported, please use one of the following: {Framework.CAIRO}, {Framework.EZKL}"
        )


app.command(
    short_help="🚀 Creates a deployment for the specified model version.",
    help="""🚀 Creates a deployment for the specified model version.

    This command has different behavior depending on the framework:

        * For Cairo, it will create an inference endpoint of the deployment in Giza.
        * For EZKL, not implemented yet.

    This command performs several operations:

        * Creates a deployment for the specified version
        * Uploads the specified version file
        * Polls the version until the status is either FAILED or COMPLETED
        * If the status is COMPLETED, sends back the deployment url to make inference requests

    Error handling is also incorporated into this process.
    """,
)(deploy)


@app.command(
    short_help="📜 List the available deployments.",
    help="""📜 Lists all the available deployments in Giza.
    This command retrieves and displays a list of all deployments stored in the server.
    Each deployment's information is printed in a json format for easy readability and further processing.
    If there are no deployments available, an empty list is printed.
    """,
)
def list(
    model_id: int = typer.Option(None, "--model-id", "-m", help="The ID of the model"),
    version_id: int = typer.Option(
        None, "--version-id", "-v", help="The ID of the version"
    ),
    debug: Optional[bool] = DEBUG_OPTION,
) -> None:
    echo("Listing deployments ✅ ")
    try:
        client = DeploymentsClient(API_HOST)
        deployments: DeploymentsList = client.list(model_id, version_id)
    except ValidationError as e:
        echo.error("Deployment validation error")
        echo.error("Review the provided information")
        if debug:
            raise e
        echo.error(str(e))
        sys.exit(1)
    except HTTPError as e:
        info = get_response_info(e.response)
        echo.error("⛔️Could not list deployments")
        echo.error(f"⛔️Detail -> {info.get('detail')}⛔️")
        echo.error(f"⛔️Status code -> {info.get('status_code')}⛔️")
        echo.error(f"⛔️Error message -> {info.get('content')}⛔️")
        echo.error(
            f"⛔️Request ID: Give this to an administrator to trace the error -> {info.get('request_id')}⛔️"
        ) if info.get("request_id") else None
        if debug:
            raise e
        sys.exit(1)
    print_json(deployments.json())


# giza/commands/deployments.py
@app.command(
    short_help="🎯 Get a deployment.",
    help="""🎯 Get a specific deployment in Giza.
    This command retrieves and displays a specific deployment stored in the server.
    The deployment's information is printed in a json format for easy readability and further processing.
    If the deployment is not available, an error message is printed.
    """,
)
def get(
    model_id: int = typer.Option(None, "--model-id", "-m", help="The ID of the model"),
    version_id: int = typer.Option(
        None, "--version-id", "-v", help="The ID of the version"
    ),
    deployment_id: int = typer.Option(
        None, "--deployment-id", "-d", help="The ID of the version"
    ),
    debug: Optional[bool] = DEBUG_OPTION,
) -> None:
    echo(f"Getting deployment {deployment_id} ✅ ")
    try:
        client = DeploymentsClient(API_HOST)
        deployment = client.get(model_id, version_id, deployment_id)
    except ValidationError as e:
        echo.error("Deployment validation error")
        echo.error("Review the provided information")
        if debug:
            raise e
        echo.error(str(e))
        sys.exit(1)
    except HTTPError as e:
        info = get_response_info(e.response)
        echo.error(f"⛔️Could not get deployment {deployment_id}")
        echo.error(f"⛔️Detail -> {info.get('detail')}⛔️")
        echo.error(f"⛔️Status code -> {info.get('status_code')}⛔️")
        echo.error(f"⛔️Error message -> {info.get('content')}⛔️")
        echo.error(
            f"⛔️Request ID: Give this to an administrator to trace the error -> {info.get('request_id')}⛔️"
        ) if info.get("request_id") else None
        if debug:
            raise e
        sys.exit(1)
    print_json(deployment.json())


@app.command(
    name="list-proofs",
    short_help="🔒 List proofs from a deployment.",
    help="""🔒 List proofs from a deployment.
    This command retrieves and displays the proofs generated by a specific deployment stored in the server.
    The proofs' information is printed in a json format for easy readability and further processing.
    If the deployment is not available, an error message is printed.
    """,
)
def list_proofs(
    model_id: int = typer.Option(None, "--model-id", "-m", help="The ID of the model"),
    version_id: int = typer.Option(
        None, "--version-id", "-v", help="The ID of the version"
    ),
    deployment_id: int = typer.Option(
        None, "--deployment-id", "-d", help="The ID of the version"
    ),
    debug: Optional[bool] = DEBUG_OPTION,
) -> None:
    echo(f"Getting proofs from deployment {deployment_id} ✅ ")
    try:
        client = DeploymentsClient(API_HOST)
        proofs: ProofList = client.list_proofs(model_id, version_id, deployment_id)
    except ValidationError as e:
        echo.error("Could not retrieve proofs from deployment")
        echo.error("Review the provided information")
        if debug:
            raise e
        echo.error(str(e))
        sys.exit(1)
    except HTTPError as e:
        info = get_response_info(e.response)
        echo.error(f"⛔️Could not get deployment {deployment_id}")
        echo.error(f"⛔️Detail -> {info.get('detail')}⛔️")
        echo.error(f"⛔️Status code -> {info.get('status_code')}⛔️")
        echo.error(f"⛔️Error message -> {info.get('content')}⛔️")
        echo.error(
            f"⛔️Request ID: Give this to an administrator to trace the error -> {info.get('request_id')}⛔️"
        ) if info.get("request_id") else None
        if debug:
            raise e
        sys.exit(1)
    print_json(proofs.json())


@app.command(
    name="get-proof",
    short_help="🔒 Retrieves information about a proof from a deployment.",
    help="""🔒 Retrieves information about a proof from a deployment.
    This command retrieves and displays the proof generated by a specific deployment stored in the server.
    The proof information is printed in a json format for easy readability and further processing.
    If the deployment is not available, an error message is printed.
    """,
)
def get_proof(
    model_id: int = typer.Option(None, "--model-id", "-m", help="The ID of the model"),
    version_id: int = typer.Option(
        None, "--version-id", "-v", help="The ID of the version"
    ),
    deployment_id: int = typer.Option(
        None, "--deployment-id", "-d", help="The ID of the version"
    ),
    proof_id: str = typer.Option(
        None, "--proof-id", "-p", help="The ID or request id of the proof"
    ),
    debug: Optional[bool] = DEBUG_OPTION,
) -> None:
    echo(f"Getting proof from deployment {deployment_id} ✅ ")
    try:
        client = DeploymentsClient(API_HOST)
        proof: Proof = client.get_proof(model_id, version_id, deployment_id, proof_id)
    except ValidationError as e:
        echo.error("Could not retrieve proof from deployment")
        echo.error("Review the provided information")
        if debug:
            raise e
        echo.error(str(e))
        sys.exit(1)
    except HTTPError as e:
        info = get_response_info(e.response)
        echo.error(f"⛔️Could not get deployment {deployment_id}")
        echo.error(f"⛔️Detail -> {info.get('detail')}⛔️")
        echo.error(f"⛔️Status code -> {info.get('status_code')}⛔️")
        echo.error(f"⛔️Error message -> {info.get('content')}⛔️")
        echo.error(
            f"⛔️Request ID: Give this to an administrator to trace the error -> {info.get('request_id')}⛔️"
        ) if info.get("request_id") else None
        if debug:
            raise e
        sys.exit(1)
    print_json(proof.json())


@app.command(
    name="download-proof",
    short_help="🔒 Downloads a proof from a deployment to the specified path.",
    help="""🔒 Downloads a proof from a deployment to the specified path.
    This command retrieves the proof created in Giza from a specific deployment.
    The proof information is stored in the specified path, defaulting to the current path.
    If the deployment is not available, an error message is printed.
    """,
)
def download_proof(
    model_id: int = typer.Option(None, "--model-id", "-m", help="The ID of the model"),
    version_id: int = typer.Option(
        None, "--version-id", "-v", help="The ID of the version"
    ),
    deployment_id: int = typer.Option(
        None, "--deployment-id", "-d", help="The ID of the version"
    ),
    proof_id: str = typer.Option(
        None, "--proof-id", "-p", help="The ID or request id of the proof"
    ),
    output_path: str = typer.Option(
        "zk.proof",
        "--output-path",
        "-o",
        help="The path where the proof will be stored",
    ),
    debug: Optional[bool] = DEBUG_OPTION,
) -> None:
    echo(f"Getting proof from deployment {deployment_id} ✅ ")
    try:
        client = DeploymentsClient(API_HOST)
        proof: bytes = client.download_proof(
            model_id, version_id, deployment_id, proof_id
        )
        with open(output_path, "wb") as f:
            f.write(proof)
    except ValidationError as e:
        echo.error("Could not retrieve proof from deployment")
        echo.error("Review the provided information")
        if debug:
            raise e
        echo.error(str(e))
        sys.exit(1)
    except HTTPError as e:
        info = get_response_info(e.response)
        echo.error(f"⛔️Could not get deployment {deployment_id}")
        echo.error(f"⛔️Detail -> {info.get('detail')}⛔️")
        echo.error(f"⛔️Status code -> {info.get('status_code')}⛔️")
        echo.error(f"⛔️Error message -> {info.get('content')}⛔️")
        echo.error(
            f"⛔️Request ID: Give this to an administrator to trace the error -> {info.get('request_id')}⛔️"
        ) if info.get("request_id") else None
        if debug:
            raise e
        sys.exit(1)
    echo(f"Proof downloaded to {output_path} ✅ ")
