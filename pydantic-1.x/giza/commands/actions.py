import typer
from cookiecutter.main import cookiecutter  # type: ignore
from slugify import slugify

from giza.utils import echo

app = typer.Typer()


@app.command()
def new(project_name: str = typer.Argument(...)):
    """
    This command will create a new action by generating a Python project.
    """
    echo(f"Creating a new Action project with name: {project_name} ✅ ")
    cookiecutter(
        "gh:gizatechxyz/actions-template",
        no_input=True,
        extra_context={
            "project_name": project_name,
            "project_slug": slugify(project_name, separator="_"),
        },
    )
    echo(f"Action project created successfully at ./{project_name} ✅")
