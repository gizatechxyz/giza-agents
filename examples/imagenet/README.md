# ImageNet Example

This example demonstrates how to use the Giza SDK to perform image classification using a pre-trained ResNet-50 model from the ONNX model zoo.

## Steps

1. Download the model, image, and labels using the `download_model()`, `download_image()`, and `download_labels()` tasks respectively.
2. Read the labels using the `read_labels()` task.
3. Load the model using `GizaModel(model_path=model_path)`.
4. Preprocess the image using the `preprocess(img)` function.
5. Predict the class of the image using the `predict(model.session, labels, img)` function.

## Running the example

To run the example, execute the `execution()` action. This action will perform all the steps mentioned above in sequence.

```
python example.py
```

Then, you can execute the Action using the Prefect UI:

```
prefect server start
```

