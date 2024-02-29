import json
from web3 import Web3
from web3.exceptions import TransactionError
from eth_account import Account
from giza_actions.model import GizaModel
import requests
import logging
from giza.frameworks.cairo import verify

class GizaAgent:
    """
    A blockchain AI agent that helps users put their Actions on-chain. Uses Ape framework and GizaModel to verify a model proof off-chain, sign it with the user's account, and send results to a select EVM chain to execute code.

    Attributes:
        model (GizaModel): The model that this deployer uploads proofs for. This model must have the following fields: id, version, orion_runner_service_url in order to work. This is because all on-chain models require a proof to be generated by Orion Runner.
        model_id: The model_id of the model we are using for on-chain inference
        version_id: The version_id of the model we are using for on-chain inference
        inference: The result of the GizaModel inference
        request_id: The request_id of the proof to fetch from the GCP
        proof: The proof from GCP that we will use to verify, sign, and send along with inference data
        

    Methods:
        infer: Runs model inference and retrieves the model output
        get_model_data: retrieves the proof from GCP given the request_id, version_id, deployment_id, and internal model_id
        generate_calldate: generates calldata for a given smart contract function
        verify: verifies the proof locally
        deploy: verifies the proof, then calls the smart contract with calldata from inference
    """
    
    def __init__(self, model: GizaModel, model_id, version_id):
        """Initialize deployer.
        
        Args:
            model (GizaModel): GizaModel instance
        """
        self.model = model
        self.model_id = model_id
        self.version_id = version_id

    def infer(self, input_file=None, input_feed=None):

        params = {}
        
        if input_file is not None:
            params['input_file'] = input_file
            
        if input_feed is not None:
            params['input_feed'] = input_feed

        params['verifiable'] = True
        params['job_size'] = "L"
        params['output_dtype'] = "Tensor<FP16x16>"
        
        self.inference, self.request_id = self.model.predict(**params)

        print("Inference saved! ✅ Result: ", self.inference, self.request_id)
        
    async def _get_model_data(self):
        """Get proof data from GCP and save it as a class attribute"""
        
        uri = self.model.get_deployment_uri(self.model_id, self.version_id)
        proof_metadata_url = f"https://api-dev.gizatech.xyz/api/v1/models/{self.model.id}/versions/{self.model.version}/deployments/{uri}/proofs/{self.request_id}"

        response = requests.get(proof_metadata_url)
        
        logging.info(f"Response status code: {response.status_code}")
        logging.debug(f"Full response: {response.text}")

        if response.status_code == 200:
            proof_metadata = response.json()
            self.proof = proof_metadata
            return proof_metadata
        else:
            raise Exception(f"Failed to get proof metadata: {response.text}")

    def generate_calldata(self, abi_path, function_name, parameters):
        """
        Generate calldata for calling a smart contract function

        Args:
            abi_path (str): Path to JSON ABI for the contract
            function_name (str): Name of contract function to call 
            parameters (list): Arguments to pass to the function

        Returns:
            str: Hex string of calldata
        """
        with open(abi_path, 'r') as f:
            abi = json.load(f)
        
        web3 = Web3()
        contract = web3.eth.contract(abi=abi)
        
        function_abi = next((x for x in abi if x['name'] == function_name), None)
        if function_abi is None:
            raise ValueError(f"Function {function_name} not found in ABI")
            
        calldata = contract.encodeABI(function_name, args=parameters)
        return calldata
    
    async def verify(self, proof):
        """
        Verify proof locally. Must be run *after* infer() and _get_model_data() have been run.
        
        Returns:
            bool: True if proof is valid
        """
        model_id = self.model.id
        version_id = self.model.version
        try:
            result = verify(proof, model_id, version_id)
            if result is None:
                return True
            else:
                return False
        except BaseException:
            logging.error("An error occurred when verifying")
            return False
        
    def transmit(self, account: Account, contract_address: str, contract_abi: list, proof, signed_proof, calldata: str):
        """
        Transmit: Verify the model proof, 
        
        Returns:
            A transaction receipt
        """    
        web3 = Web3()
        # Verify the proof signature
        signer = web3.eth.account.recover_message(text=proof, signature=signed_proof)
        assert signer.lower() == account.address.lower()
        # Verify the proof
        assert self.verify(proof)
        
        print("All good! ✅ Sending transaction...")
        
        try:
            web3 = Web3()
            contract = web3.eth.contract(address=contract_address, abi=contract_abi)
            nonce = web3.eth.get_transaction_count(account.address)  

            tx = contract.caller.call(tx={
                "to": contract_address, 
                "data": calldata,
                "nonce": nonce,
                "gas": 2000000
            })
        
            signed_tx = account.sign_transaction(tx)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)  
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            return receipt
        
        except ValueError as e:
            print(f"Error encoding transaction: {e}")
            return None

        except TransactionError as e:
            print(f"Transaction error: {e}") 
            return None

        except Exception as e:
            print(f"Error transmitting transaction: {e}")
            return None