import os
import re
import subprocess
import zipfile
from io import BytesIO
from typing import Optional

from giza.exceptions import PasswordError, ScarbBuildError, ScarbNotFound
from giza.utils import echo


def _check_password_strength(password: str) -> None:
    """
    Check if the password meets the requirements.

    Args:
        password (str): password to check

    Raises:
        PasswordError: if the password does not meet the requirements
    """
    regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d#?!@$%^&*-_]{8,}$"
    if not re.match(regex, password):
        raise PasswordError(
            "Password must be at least 8 characters long, contain at least one uppercase letter, one lowercase letter and one number."
        )


def download_model_or_sierra(
    content: bytes, output_path: str, name: Optional[str] = None
):
    """
    Download the model or sierra file.

    Args:
        content (bytes): file content
        output_path (str): path to save the file
        name (str): file name. Defaults to None.
    """
    f = BytesIO(content)
    is_zip = zipfile.is_zipfile(f)
    if not is_zip and name is not None:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        with open(os.path.join(output_path, name), "wb") as file_:
            file_.write(content)
    else:
        zip_file = zipfile.ZipFile(f)
        zip_file.extractall(output_path)


def zip_folder(source_folder: str, dst_folder: str) -> str:
    """
    Zip the folder to a specific location.

    Args:
        source_folder (str): path to the folder
        dst_folder (str): destination folder

    Returns:
        str: path to the zip file
    """
    zip_file_path = os.path.join(dst_folder, "model.zip")
    if os.path.exists(zip_file_path):
        os.remove(zip_file_path)
    elif not os.path.exists(dst_folder):
        os.makedirs(dst_folder)
    with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_folder):
            for file_ in files:
                if "target" not in root:
                    zipf.write(os.path.join(root, file_))
    return zip_file_path


def scarb_build(folder) -> None:
    """
    Build the scarb model.

    Args:
        folder (str): path to the folder
    """
    try:
        subprocess.run(["scarb", "--version"], check=True)
    except subprocess.CalledProcessError as e:
        echo.error("Scarb not found in the system")
        raise ScarbNotFound("Scarb not found in the system") from e
    echo("Scarb is installed, proceeding with the build.")

    try:
        subprocess.run(
            [
                "scarb",
                "build",
            ],
            check=True,
            cwd=folder,
        )
    except subprocess.CalledProcessError as e:
        echo.error("Compilation failed")
        raise ScarbBuildError("Compilation failed") from e
    echo("Compilation successful")
