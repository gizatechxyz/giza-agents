
# Actions SDK

The Actions SDK is a Python library designed to facilitate the development of applications on the Giza platform. It provides a set of decorators and classes to define tasks, actions, and models, and to handle data inputs.

## Installation

The Actions SDK can be installed using [Poetry](https://python-poetry.org/):

```
poetry install
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

## Contributing

Contributions are welcome! Please submit a pull request or create an issue to get started.

## License

The Giza SDK is licensed under the MIT license.