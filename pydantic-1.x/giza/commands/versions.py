import glob
import os
import sys
import zipfile
from tempfile import TemporaryDirectory
from typing import Dict, Optional

import typer
from rich import print_json

from giza import API_HOST
from giza.client import TranspileClient, VersionsClient
from giza.frameworks import cairo, ezkl
from giza.options import DEBUG_OPTION
from giza.schemas.versions import Version, VersionList
from giza.utils import echo
from giza.utils.enums import Framework, VersionStatus
from giza.utils.exception_handling import ExceptionHandler
from giza.utils.misc import download_model_or_sierra, scarb_build, zip_folder

app = typer.Typer()


def update_sierra(model_id: int, version_id: int, model_path: str):
    sierra_path = glob.glob(
        os.path.join(model_path, "inference", "**/*.sierra"), recursive=True
    )[0]
    with open(sierra_path, "rb") as f:
        TranspileClient(API_HOST).update_transpilation(model_id, version_id, f)
        echo("Sierra updated ✅ ")


@app.command(
    short_help="📦 Retrieves information about a version in Giza.",
    help="""📦 Retrieves information about a version in Giza.

    This commands needs a model id and version id to retrieve data from the server.

    If no version exists with the specified id an empty json is printed.
    """,
)
def get(
    model_id: int = typer.Option(None, help="The ID of the model"),
    version_id: int = typer.Option(None, help="The ID of the version"),
    debug: bool = DEBUG_OPTION,
) -> None:
    if any([model_id is None, version_id is None]):
        echo.error("⛔️Model ID and version ID are required⛔️")
        sys.exit(1)
    echo("Retrieving version information ✅ ")
    with ExceptionHandler(debug=debug):
        client = VersionsClient(API_HOST)
        version: Version = client.get(model_id, version_id)
    print_json(version.json())


def transpile(
    model_path: str = typer.Argument(None, help="Path of the model to transpile"),
    model_id: int = typer.Option(
        None, help="The ID of the model where a new version will be created"
    ),
    desc: str = typer.Option(None, help="Description of the version"),
    model_desc: str = typer.Option(
        None, help="Description of the Model to create if model_id is not provided"
    ),
    framework: Framework = typer.Option(Framework.CAIRO, "--framework", "-f"),
    output_path: str = typer.Option(
        "cairo_model",
        "--output-path",
        "-o",
        help="The path where the cairo model will be saved",
    ),
    input_data: str = typer.Option(
        None,
        "--input-data",
        "-i",
        help="The input data to use for the transpilation",
    ),
    download_model: bool = typer.Option(
        True,
        "--download-model",
        help="Download the transpiled model after the transpilation is completed. CAIRO only.",
    ),
    download_sierra: bool = typer.Option(
        False,
        "--download-sierra",
        help="Download the siera file is the modle is fully compatible. CAIRO only.",
    ),
    debug: Optional[bool] = DEBUG_OPTION,
) -> None:
    if framework == Framework.CAIRO:
        cairo.transpile(
            model_path=model_path,
            model_id=model_id,
            desc=desc,
            model_desc=model_desc,
            output_path=output_path,
            download_model=download_model,
            download_sierra=download_sierra,
            debug=debug,
        )
    elif framework == Framework.EZKL:
        ezkl.setup(
            model_path=model_path,
            model_id=model_id,
            desc=desc,
            model_desc=model_desc,
            input_data=input_data,
            debug=debug,
        )
    else:
        raise typer.BadParameter(
            f"Framework {framework} is not supported, please use one of the following: {Framework.CAIRO}, {Framework.EZKL}"
        )


app.command(
    short_help="🔧 Sends the specified model for transpilation.",
    help="""🔧 Sends the specified model for transpilation.

    This command has different behavior depending on the framework:

        * For Cairo, it will transpile the specified file and upload it to Giza.
        * For EZKL, it will create a version and perform the trusted setup, creating al the necessary files for it.

    This command performs several operations:

        * Creates a version for the specified model
        * Uploads the specified file
        * Updates the status to UPLOADED
        * Polls the version until the status is either FAILED or COMPLETED
        * If the status is COMPLETED, downloads the model to the specified path

    Error handling is also incorporated into this process.
    """,
)(transpile)


@app.command(
    short_help="🔄 Update version data or a partially supported version",
    help="""🔄 Update version data or a partially supported vers.

    This command aims to update version data or if a model is partially supported,
    it will try to update the model to a fully supported version if a cairo model path is provided.

    It will retrigger compilation of the model and if the model is fully supported, it will update the version to completed.
    """,
)
def update(
    model_id: int = typer.Option(None, "--model-id", "-m", help="The ID of the model"),
    version_id: int = typer.Option(
        None, "--version-id", "-v", help="The ID of the version"
    ),
    model_path: str = typer.Option(
        None, "--model-path", "-M", help="Path of the model to update"
    ),
    debug: bool = DEBUG_OPTION,
) -> None:
    if any([model_id is None, version_id is None]):
        echo.error("⛔️Model ID and version ID are required to update the version⛔️")
        sys.exit(1)
    echo("Checking version ✅ ")
    with ExceptionHandler(debug=debug):
        client = VersionsClient(API_HOST)
        version = client.get(model_id, version_id)

        if (
            version.status != VersionStatus.PARTIALLY_SUPPORTED
            and model_path is not None
        ):
            echo.error("⛔️Version has a different status than PARTIALLY_SUPPORTED⛔️")
            sys.exit(1)
        elif (
            version.status == VersionStatus.PARTIALLY_SUPPORTED
            and model_path is not None
        ):
            scarb_build(os.path.join(model_path, "inference"))
            update_sierra(model_id, version_id, model_path)
            with TemporaryDirectory() as tmp_dir:
                zip_path = zip_folder(model_path, tmp_dir)
                version = client.upload_cairo(model_id, version_id, zip_path)
        echo("Version updated ✅ ")
    print_json(version.json())


@app.command(
    short_help="📜 List the available versions for a model.",
    help="""📜 List the available versions for a model.

    This command needs a model id to retrieve the list of versions.
    """,
)
def list(
    model_id: int = typer.Option(None, help="The ID of the model"),
    debug: bool = DEBUG_OPTION,
) -> None:
    if model_id is None:
        echo.error("⛔️Model ID is required⛔️")
        sys.exit(1)
    echo("Listing versions for the model ✅ ")
    with ExceptionHandler(debug=debug):
        client = VersionsClient(API_HOST)
        versions: VersionList = client.list(model_id)
    print_json(versions.json())


@app.command(
    short_help="⚡️ Download the transpiled cairo model if available.",
    help="""⚡️ Download the transpiled cairo model if available.

    Download an unzip a transpiled model.

    Verification and an active token is needed.
    """,
)
def download(
    model_id: int = typer.Option(None, help="The ID of the model"),
    version_id: int = typer.Option(None, help="The ID of the version"),
    output_path: str = typer.Option(
        "cairo_model", "--output-path", "-o", help="Path to output the cairo model"
    ),
    download_model: bool = typer.Option(
        False,
        "--download-model",
        help="Download the transpiled model after the transpilation is completed. CAIRO only.",
    ),
    download_sierra: bool = typer.Option(
        False,
        "--download-sierra",
        help="Download the siera file is the modle is fully compatible. CAIRO only.",
    ),
    debug: bool = DEBUG_OPTION,
) -> None:
    """
    Retrieve information about the current user and print it as json to stdout.

    Args:
        debug (Optional[bool], optional): Whether to add debug information, will show requests, extra logs and traceback if there is an Exception. Defaults to DEBUG_OPTION (False)
    """

    with ExceptionHandler(debug=debug):
        if any([model_id is None, version_id is None]):
            raise ValueError("⛔️Model ID and version ID are required⛔️")

        client = VersionsClient(API_HOST, debug=debug)
        version = client.get(model_id, version_id)

        if version.status != VersionStatus.COMPLETED:
            raise ValueError(f"Model version status is not completed {version.status}")

        echo("Data is ready, downloading! ✅")
        downloads: Dict[str, bytes] = client.download(
            model_id,
            version.version,
            {"download_model": download_model, "download_sierra": download_sierra},
        )

        for name, content in downloads.items():
            try:
                echo(f"Downloading {name} ✅")
                download_model_or_sierra(content, output_path, name)
            except zipfile.BadZipFile as zip_error:
                raise ValueError(
                    "Something went wrong with the download", zip_error.args[0]
                ) from None
            echo(f"{name} saved at: {output_path}")


@app.command(
    short_help="⚡️ Download the original ONNX model.",
    help="""⚡️ Download the original ONNX model.

    Verification and an active token is needed.
    """,
)
def download_original(
    model_id: int = typer.Option(None, help="The ID of the model"),
    version_id: int = typer.Option(None, help="The ID of the version"),
    output_path: str = typer.Option(
        "model.onnx", "--output-path", "-o", help="Path to output the ONNX model"
    ),
    debug: bool = DEBUG_OPTION,
) -> None:
    """
    Retrieve information about the current user and print it as json to stdout.

    Args:
        debug (Optional[bool], optional): Whether to add debug information, will show requests, extra logs and traceback if there is an Exception. Defaults to DEBUG_OPTION (False)
    """

    with ExceptionHandler(debug=debug):
        if any([model_id is None, version_id is None]):
            raise ValueError("⛔️Model ID and version ID are required⛔️")

        client = VersionsClient(API_HOST, debug=debug)
        version = client.get(model_id, version_id)

        if version.status != VersionStatus.COMPLETED:
            raise ValueError(f"Model version status is not completed {version.status}")

        echo("ONNX model is ready, downloading! ✅")
        onnx_model = client.download_original(model_id, version.version)

        with open(output_path, "wb") as f:
            f.write(onnx_model)

        echo(f"ONNX model saved at: {output_path}")
