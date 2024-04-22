# Train a Linear Regression Using the EZKL backend

This example demonstrates how to train a linear regression model using the EZKL backend.

First, install the `torch`, `hummingbird-ml`, and `scikit-learn` packages by running the following command:

```bash
pip install torch hummingbird-ml scikit-learn
```

This example uses the `scikit-learn` package to train a linear regression model and the `hummingbird-ml` package to convert the trained model to `torch` and then into ONNX, this is to maximize compatibility with `ezkl`.

The code can be found in the [train_linear_regression.py](train_linear_regression.py) file, but we will explain each step.

## Train a Linear Regression Model

The following code trains a linear regression model using the `scikit-learn` package:

```python
import numpy as np
from sklearn.linear_model import LinearRegression

# Create a dataset
X = np.array([[1, 1], [1, 2], [2, 2], [2, 3]])
y = np.dot(X, np.array([1, 2])) + 3

# Train a linear regression model
model = LinearRegression().fit(X, y)
```

## Convert the Trained Model to `torch`

The following code converts the trained model to `torch` using the `hummingbird-ml` package:

```python
import hummingbird.ml

# Convert the trained model to `torch`
hb_model = hummingbird.ml.convert(model, "torch")
```

More information about the `hummingbird-ml` package can be found [here](https://github.com/microsoft/hummingbird).

## Convert the Trained Model to ONNX

Now that we have a torch model, we can export it to ONNX using the default utilities in the `torch` package:

```python
    # Convert the trained model to ONNX
    sample = np.array([7, 2])
    # Input to the model
    shape = sample.shape
    x = torch.rand(1, *shape, requires_grad=True)

    # Export the model
    torch.onnx.export(
        model,
        x,
        "network.onnx",
        export_params=True,
        opset_version=10,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
    )
```

## Create an `input.json` file for transpilation

For the transpilation we need an example of the input data. In this case, we will use the `sample` variable to create the `input.json` file:

```python
with open("input.json", "w") as f:
    f.write(
        json.dumps(
            {
                "input_shapes": [sample.shape],
                "input_data": [sample.tolist()],
            }
        )
    )
```

## Deploy the verifiable model using the EZKL framework

The first step is to use the `giza-cli` to transpile the model and create a version job. Once this job finishes we will be able to deploy the model as a service.

```bash
giza transpile --framework EZKL --input-data? input.json network.onnx
```

The next step is to deploy the model as a service.

```bash
giza deployments deploy --framework EZKL --model-id <model_id> --version-id <version_id>
```

## Perform a prediction

Using the `predict_action.py` you can add the generated `model_id` and `version_id` to the `predict_action.py` file and run the following command:

```bash
python predict_action.py
```

This will start the action to perform the prediction. It includes two tasks, an example of how to perform a prediction using the `GizaModel`:

```python
model = GizaModel(id=MODEL_ID, version=VERSION)

result, request_id = model.predict(input_feed=[7, 2], verifiable=True, job_size="S")

print(f"Result: {result}, request_id: {request_id}")
```

The latter will take the request and wait for the proof to be created. Check the script for [more information](predict_action.py).