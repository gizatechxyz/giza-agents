# import json
# import unittest
# from unittest.mock import patch, Mock

# import numpy as np

# from giza_actions.model import GizaModel


# def test_predict_success():

#     model = GizaModel(
#         model_path="",
#         orion_runner_service_url="https://deployment-admin-1-1-a10d06cd-6nn4ryaqca-ew.a.run.app")

#     arr = np.array([[1, 2], [3, 4]], dtype=np.uint32)

#     result = model.predict(
#         input_feed={"a": arr}, verifiable=True, output_dtype='signed_int')
