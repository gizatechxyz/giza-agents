# giza/cli.py

import click
from giza.sdk import Action

@click.group()
def cli():
    pass

@cli.command()
@click.option('--action-id', required=True, type=int, help='The id of the action to execute.')
def execute(action_id):
    """This command executes an action in the platform."""
    action = Action(id=action_id)
    action.execute()

@cli.command()
@click.option('--action-id', required=True, type=int, help='The id of the action to apply.')
@click.option('--inference-id', required=True, type=int, help='The id of the inference to apply the action to.')
def apply(action_id, inference_id):
    """This command applies an action to a specific inference-id."""
    action = Action(id=action_id)
    action.apply(inference_id=inference_id)

if __name__ == '__main__':
    cli()
