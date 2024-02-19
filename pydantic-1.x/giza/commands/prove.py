from typing import List, Optional

import typer

from giza.frameworks import cairo, ezkl
from giza.options import DEBUG_OPTION
from giza.utils.enums import Framework, JobSize

app = typer.Typer()


def prove(
    data: List[str] = typer.Argument(None),
    model_id: Optional[int] = typer.Option(None, "--model-id", "-m"),
    version_id: Optional[int] = typer.Option(None, "--version-id", "-v"),
    size: JobSize = typer.Option(JobSize.S, "--size", "-s"),
    framework: Framework = typer.Option(Framework.CAIRO, "--framework", "-f"),
    output_path: str = typer.Option("zk.proof", "--output-path", "-o"),
    debug: Optional[bool] = DEBUG_OPTION,
) -> None:
    if framework == Framework.CAIRO:
        cairo.prove(data=data, size=size, output_path=output_path, debug=debug)
    elif framework == Framework.EZKL:
        ezkl.prove(
            input_data=data[0],
            model_id=model_id,
            version_id=version_id,
            size=size,
            output_path=output_path,
            debug=debug,
        )
    else:
        raise typer.BadParameter(
            f"Framework {framework} is not supported, please use one of the following: {Framework.CAIRO}, {Framework.EZKL}"
        )
