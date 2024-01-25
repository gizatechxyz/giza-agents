from giza_actions.model import GizaModel
from ape import Contract

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
    
    def __init__(self, model: GizaModel, model_id: int):
        """
        Initialize deployer.
        
        Args:
            model: GizaModel instance
            model_id: Model ID
        """
        self.model = model
        self.model_id = model_id

    def infer(self, input_file, input_feed):
        """Run model inference and store output."""
        self.inference = self.model.predict(input_file, input_feed, verifiable=True)

    def get_model_data(self, request_id, version_id, deployment_id):
        """Get proof data from GCP."""
        # TODO: Implement GCP communication

    def process_inference(self):
        """
        Process inference data into contract calldata.
        
        Raises:
            Exception: If inference not run yet. 
        """
        if self.inference is None:
            raise Exception("Please run infer() before calling process_inference()")
            
        # Default just sends inference result to contract
        return self.inference

    def deploy(self, sc_address, calldata, proof):
        """
        Deploy model: Verify proof and execute contract function.
        
        Returns:
            Transaction hash
        """        
        contract = Contract(sc_address)
        # TODO: Validate proof and execute contract
        