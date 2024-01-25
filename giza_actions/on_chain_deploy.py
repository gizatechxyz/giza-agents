# Imports: Giza Actions Utils, OS ENV variables, Giza actions init (?)

# Class OCDeployer
#     def __init__(self, model: GizaModel, model_id): self
#     def infer(self, input_file, input_feed): inference
#     def get_model_data(request_id, version_id, deployment_id): proof
#     def process_inference(inference): calldata
#     def deploy(sc_address, calldata, proof): txn hash
class OCDeployer:
    """
    A blockchain deployer. `OC` stands for on-chain. Uses Ape framework and GizaModel to verify a model proof on-chain and execute an action from it.

    Attributes:
        model (GizaModel): The model that this deployer uploads proofs for
        model_id (int): The ID of the GizaModel

    Methods:
        infer: Runs model inference and retrieves the model output
        get_model_data: retrieves the proof from GCP given the request_id, version_id, deployment_id, and internal model_id
        process_inference: overriden by user to specify calldata for a given smart contract function
        deploy: verifies the proof, then calls the smart contract with calldata from inference
    """
# __init__: 
# runs predict() with verifiable=true and stores the output in self.inference

# get_model_data: 
# gets the proof data from GCP after OrionRunner is done and proof is generated

# process_inference:
# SHOULD BE OVERRIDDEN BY USER: takes the inference data and encodes it into transaction calldata for a given smart contract function. By default calls the `action` function with default inference data

# deploy:
# initiates a transaction that verifies the proof on-chain. Waits for the proof to verify, then executes the specified function with the specified calldata. Returns the transaction hash.