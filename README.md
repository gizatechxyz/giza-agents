# Giza SDK

Giza SDK is a Python library that provides a simple and intuitive way to interact with the Giza platform. It allows you to define actions, tasks, models, and data inputs for your machine learning workflows.

## Installation

You can install the Giza SDK using Poetry:

```bash
poetry add giza-sdk
```

## Usage

Here is a basic example of how to use the Giza SDK:

```python
from giza.sdk import action, task, model, data_input

@task(log_prints=True)
def preprocess(name: str):
    print(f"Hello {name}!")

@action
@model(id=1, version=1)
def apy_prediction():
    allocations = load_input()
    input = preprocess(allocations)
    model = load_model()
    return model.predict(input)

@data_input(dtype = "FP16x16")
def load_input(path):
    # Load the data from the path
    # Return a numpy array
```

You can then execute an inference in Python:

```python
apy_prediction.run()
```

Or simulate the transpiled mode:

```python
apy_prediction.check()
```

You can also register the action on Giza:

```python
apy_prediction.register(
    name="my-first-deployment",
    cron="* * * * *",
    tags=["testing", "tutorial"],
    description="Given a GitHub repository, logs repository statistics for that repo.",
    version="tutorial/deployments",
)
```

And execute the registered action in the platform:

```python
apy_prediction.execute() # expecting to run on platform
```

Or execute in the platform and create the `input.cairo`, run Cairo VM and create a proof:

```python
apy_prediction.apply(inference_id="asdf")
```

## CLI Usage

You can also interact with the Giza platform using the CLI:

```bash
# Execute an action in the platform
giza action execute --action-id xx

# Apply an action to a specific inference-id
giza action apply --action-id xx --inference-id xx
```

## Development

To run the tests, use the following command:

```bash
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT
