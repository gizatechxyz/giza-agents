
# Actions SDK

The Actions SDK is a Python library designed to facilitate the development of ZKML applications on the Giza platform. It provides a set of decorators and classes to define tasks, actions, and models, and to handle data inputs.

## Where to start?
Check out our extensive [documentation](https://actions.gizatech.xyz/welcome/giza-actions-sdk) to understand concepts and follow how-to-guides.

## Installation

Start by creating a virtual environment in your project directory and activate it:
```bash
$ python -m venv .env

# Activate the virtual environment. On Linux and MacOs
$ source .env/bin/activate

# Activate Virtual environment on Windows:
$ .env/Scripts/activate
```
Now you’re ready to install ⚡Actions with the following command:

```bash
$ pip install giza-actions
```

## Setup

From your terminal, create a Giza user through our CLI in order to access the Giza Platform:
```bash
$ giza users create
```
After creating your user, log into Giza:
```bash
$ giza users login
```
Optional: you can create an API Key for your user in order to not regenerate your access token every few hours.
```bash
$ giza users create-api-key
```
To create Actions Runs you will need a Giza Workspace, create it executing the following command in your terminal:
```bash
$ giza workspaces create
```

## Usage

### Defining Tasks
A task is a function that represents a distinct segment of work in a Giza Actions workflow. Tasks provide a way to encapsulate parts of your workflow logic in traceable, reusable units across actions.

Tasks are defined using the `@task` decorator. Here's an example:
```python
from giza.task import task

@task
def preprocess():
    print(f"Preprocessing...")
```

### Defining Actions
An action serves as a framework for coding ML inferencing workflow logic, enabling users to tailor the behaviour of their workflows.

Actions are defined using the `@action` decorator. Here's an example:
```python
from giza.action import action

@action(name="My Action")
def inference():
    print(f"Running inference...")
```

### Deploy Actions

Deployments are server-side representations of actions. They keep essential metadata required for remote orchestration, including when, where, and how a workflow should run. Deployments transform workflows from functions that need to be manually activated to API-managed entities capable of being triggered remotely.

We can easily create a deployment by creating the Action object and then calling the serve function in the entrypoint script:

```python
from giza_actions.action import Action, action
from giza_actions.task import task

@task
def print_hello():
    print(f"Hello Action!")

@action
def hello_world():
    print_hello()

if __name__ == '__main__':
    action_deploy = Action(entrypoint=hello_world, name="hello-world-action")
    action_deploy.serve(name="hello-world-action-deployment")
```

Running this script will do two things:
- Create a deployment called "hello-world-action" for your action in the Giza Platform.
- Stay running to listen for action runs for this deployment; when a run is found, it will be asynchronously executed within a subprocess locally.

## Examples

Examples of how to use the Actions SDK can be found in the `examples` directory. Each example includes a README or a Notebook with detailed instructions on how to run the example.

## Contributing

Contributions are welcome! Please submit a pull request or create an issue to get started.

## License

The Giza SDK is licensed under the MIT license.
