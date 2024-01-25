# Imports: Prefect, Giza Actions Utils, OS ENV variables, Giza actions init (?)

# Class OCDeployer
#     def __init__(self, model: GizaModel, input_file, input_feed): self
#     def get_model_data(request_id, model_id, version_id, deployment_id): proof
#     def process_inference(inference): calldata
#     def deploy(sc_address, calldata, proof): txn hash


# __init__: 
# runs predict() with verifiable=true and stores the output in self.inference

# get_model_data: 
# gets the proof data from GCP after OrionRunner is done and proof is generated

# process_inference:
# SHOULD BE OVERRIDDEN BY USER: takes the inference data and encodes it into transaction calldata for a given smart contract function. By default calls the `action` function with default inference data

# deploy:
# initiates a transaction that verifies the proof on-chain. Waits for the proof to verify, then executes the specified function with the specified calldata. Returns the transaction hash.