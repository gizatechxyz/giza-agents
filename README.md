
# Actions SDK

The Actions SDK is a Python library designed to facilitate the development of applications on the Giza platform. It provides a set of decorators and classes to define tasks, actions, and models, and to handle data inputs.

## Installation

The Actions SDK can be installed using [Poetry](https://python-poetry.org/):

```
poetry install
```

Be sure you're logged into the [Giza CLI](https://cli.gizatech.xyz/resources/users) and have created a workspace:

```
giza workspaces create
```

## Usage

### Defining Tasks

Tasks are defined using the `@task` decorator. Here's an example:
```python
from giza.task import task

@task
def preprocess():
    print(f"Preprocessing...")
```

## Defining Actions

Actions are defined using the `@action` decorator. Here's an example:
```python
from giza.action import action

@action
def inference():
    print(f"Running inference...")
```

## Running Actions

Actions can be deployed executing the Python script defining the Action. For example, if the Action is defined in `example.py`, you can run it using:

```
python example.py
```

Then, you can execute the Action using the Prefect UI:

```
prefect server start
```

## Examples

Examples of how to use the Actions SDK can be found in the `examples` directory. Each example includes a README with detailed instructions on how to run the example.

For instance, the `imagenet` example demonstrates how to use the Giza SDK to perform image classification using a pre-trained ResNet-50 model from the ONNX model zoo.

To understand how to execute these examples, please refer to the README file in each example's directory.

## Contributing

Contributions are welcome! Please submit a pull request or create an issue to get started.

## License

The Giza SDK is licensed under the MIT license.
