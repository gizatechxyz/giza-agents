from typing import Optional

import typer

from giza.frameworks import cairo, ezkl
from giza.options import DEBUG_OPTION
from giza.utils.enums import Framework, JobSize

app = typer.Typer()


def verify(
    model_id: Optional[int] = typer.Option(None, "--model-id", "-m"),
    version_id: Optional[int] = typer.Option(None, "--version-id", "-v"),
    proof_id: Optional[int] = typer.Option(None, "--proof-id", "-p"),
    proof: Optional[str] = typer.Option(None, "--proof", "-P"),
    size: JobSize = typer.Option(JobSize.S, "--size", "-s"),
    framework: Framework = typer.Option(Framework.CAIRO, "--framework", "-f"),
    debug: Optional[bool] = DEBUG_OPTION,
) -> None:
    if framework == Framework.CAIRO:
        cairo.verify(
            proof_id=proof_id,
            model_id=model_id,
            version_id=version_id,
            size=size,
            debug=debug,
            proof=proof,
        )
    elif framework == Framework.EZKL:
        ezkl.verify(
            proof_id=proof_id,
            model_id=model_id,
            version_id=version_id,
            size=size,
            debug=debug,
            proof=proof,
        )
    else:
        raise typer.BadParameter(
            f"Framework {framework} is not supported, please use one of the following: {Framework.CAIRO}, {Framework.EZKL}"
        )
