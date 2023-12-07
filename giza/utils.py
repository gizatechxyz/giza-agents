import platform
import subprocess
import sys

from prefect.utilities.dockerutils import get_prefect_image_name
from rich.pretty import pprint

import giza


def python_version_minor() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}"


def build_image(
    arch: str = platform.machine(),
    python_version: str = python_version_minor(),
    dry_run: bool = False,
):
    """
    Build a docker image for development.
    """
    # exit_with_error_if_not_editable_install()
    # TODO: Once https://github.com/tiangolo/typer/issues/354 is addressed, the
    #       default can be set in the function signature
    arch = arch or platform.machine()
    python_version = python_version or python_version_minor()

    tag = get_prefect_image_name(python_version=python_version)

    # Here we use a subprocess instead of the docker-py client to easily stream output
    # as it comes
    command = [
        "docker",
        "build",
        str(giza.__development_base_path__),
        "--tag",
        tag,
        "--platform",
        f"linux/{arch}",
        "--build-arg",
        "PREFECT_EXTRAS=[dev]",
        "--build-arg",
        f"PYTHON_VERSION={python_version}",
    ]

    if dry_run:
        print(" ".join(command))
        return

    try:
        subprocess.check_call(command, shell=sys.platform == "win32")
    except subprocess.CalledProcessError:
        pprint("Failed to build image!")
    else:
        pprint(f"Built image {tag!r} for linux/{arch}")
