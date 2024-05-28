import json

import numpy as np
import torch
from hummingbird.ml import convert
from sklearn.linear_model import LinearRegression


def train():
    X = np.array([[1, 1], [1, 2], [2, 2], [2, 3]])

    y = np.dot(X, np.array([1, 2])) + 3
    reg = LinearRegression().fit(X, y)

    return reg


def convert_to_torch(linear_regression, sample):
    return convert(linear_regression, "torch", sample).model


def convert_to_onnx(model, sample):
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


def create_input_file(sample: np.ndarray):
    with open("input.json", "w") as f:
        f.write(
            json.dumps(
                {
                    "input_shapes": [sample.shape],
                    "input_data": [sample.tolist()],
                }
            )
        )


def model_to_onnx():
    lr = train()
    sample = np.array([7, 2])
    model = convert_to_torch(lr, sample)
    convert_to_onnx(model, sample)
    create_input_file(sample)


model_to_onnx()
