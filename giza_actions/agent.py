import os
import asyncio
import json
import time
from web3 import Web3
from web3.exceptions import TimeExhausted, ContractCustomError
from eth_account import Account
from eth_account.messages import SignableMessage
from eth_typing import Address
from giza_actions.model import GizaModel
import requests
import logging
from giza.frameworks.cairo import verify
from giza_actions.utils import get_deployment_uri
from giza.client import DeploymentsClient
from giza import API_HOST
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class ProofType(BaseModel):
    model_id: int # The model being used for inference
    proof_path: Optional[str] # The path to the proof of inference
    address: Address # Who is the signer?
    
    class Config:
        protected_namespaces = ()
    
class ProofMessage(BaseModel):
    proofType: ProofType
    
class GizaAgent(GizaModel):
    """
    A blockchain AI agent that helps users put their Actions on-chain. Uses Ape framework and GizaModel to verify a model proof off-chain, sign it with the user's account, and send results to a select EVM chain to execute code.

    Attributes:
        model (GizaModel): The model that this deployer uploads proofs for. This model must have the following fields: id, version, orion_runner_service_url in order to work. This is because all on-chain models require a proof to be generated by Orion Runner.
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
    
    def __init__(self, id: Optional[int] = None, version: Optional[int] = None, **kwargs):
        """Initialize deployer.
        
        Args:
            model (GizaModel): GizaModel instance
        """
        super().__init__(id=id, version=version, **kwargs)

    def infer(self, input_file=None, input_feed=None, job_size="M"):
        """
        Need docs on these ASAP
        """
        params = {}
        
        if input_file is not None:
            params['input_file'] = input_file
            
        if input_feed is not None:
            params['input_feed'] = input_feed

        params['verifiable'] = True
        params['job_size'] = job_size
        params['output_dtype'] = "Tensor<FP16x16>"
        
        self.inference, self.request_id = self.predict(**params)

        print("Inference saved! ✅ Result: ", self.inference, self.request_id)
        
    def get_model_data(self):
        """Get proof data from GCP and save it as a class attribute"""
        client = DeploymentsClient(API_HOST)

        uri = get_deployment_uri(self.model_id, self.version_id)
        # get this from CLI
        proof_metadata_url = f"https://api.gizatech.xyz/api/v1/models/{self.model_id}/versions/{self.version_id}/deployments/{uri}/proofs/{self.request_id}:download"

        time.sleep(3)
        logging.info(f"Fetching proof metadata from {proof_metadata_url}... ⏳")
        deployment_id = get_deployment_id(self.model_id, self.version_id)
        timeout = time.time() + 8000
        print(f"Deployment ID: {deployment_id}")
        print(f"Request ID: {self.request_id}")
        print(f"Model ID: {self.model_id}")
        print(f"Version ID: {self.version_id}")
        print(f"Framework: {self.framework}")

        while True:
            now = time.time()
            if now > timeout:
                print("Proof retrieval timed out")
                raise TimeoutError("Proof retrieval timed out")
            try:
                proof = client.get_proof(self.model_id, self.version_id, deployment_id, self.request_id)
                print(f"Proof: {proof.json(exclude_unset=True)}")
                break  # Exit the loop if proof is retrieved successfully
            except requests.exceptions.HTTPError as e:
                print("Proof retrieval failing, sleeping for 5 seconds")
                print(e)
                time.sleep(5)
                
        # Save the proof to a file
        proof_file = "zk.proof"
        content = client.download_proof(self.model_id, self.version_id, deployment_id, self.request_id)
        with open(proof_file, "wb") as f:
            f.write(content)

        return (content, os.path.abspath(proof_file))
                
    def _generate_calldata(self, contract_address: Address, chain_id, abi_path: str, function_name, parameters):
        """
        Generate calldata for calling a smart contract function

        Args:
            abi_path (str): Path to JSON ABI for the contract
            function_name (str): Name of contract function to call 
            parameters (list): Arguments to pass to the function

        Returns:
            str: Hex string of calldata
        """
        print("Fetching calldata... 🗣️")
        with open(abi_path, 'r') as f:
            abi = json.load(f)
        
        web3 = Web3()
        contract = web3.eth.contract(abi=abi)
        
        function_abi = next((item for item in abi if 'name' in item and item['name'] == function_name), None)
        
        if function_abi is None:
            raise ValueError(f"Function {function_name} not found in ABI")
        
        if not isinstance(parameters, (list, tuple)):
            parameters = [parameters]  # Convert single value to a list
        
        contract = web3.eth.contract(address=contract_address, abi=abi)
        calldata = contract.encodeABI(function_name, args=parameters)
        print("Calldata: ", calldata)
        return calldata
    
    def sign_proof(self, account: Account, proof: Optional[bytes], proof_path: Optional[str]):
        address = account.address
        
        proofType = ProofType(model_id=self.model_id, proof_path=proof_path, address=address)
        proofMessage = ProofMessage(proofType=proofType)
        
        version = b'\x19'
        header = b''
        
        if proof is None:
            dummy_message = "dummy_proof"
            dummy_body = dummy_message.encode('utf-8')
            dummy_signable_message = SignableMessage(version=version, header=header, body=dummy_body)
            dummy_signature = account.sign_message(dummy_signable_message)
            return (dummy_signature, True, proofMessage, dummy_signable_message)
        
        if isinstance(proof, str):
            body = proof.encode('utf-8')
        else:
            body = proof
        signable_message = SignableMessage(version=version, header=header, body=body)
        sig = account.sign_message(signable_message)
        return (sig, False, proofMessage, signable_message)
        
    async def verify(self, proof_path):
        """
        Verify proof locally. Must be run *after* infer() and _get_model_data() have been run.
        
        Returns:
            bool: True if proof is valid
        """
        model_id = self.model_id
        version_id = self.version_id
        try:
            result = verify(None, proof=proof_path, model_id=model_id, version_id=version_id)
            if result is None:
                return True
            else:
                return False
        except BaseException as e:
            logging.error("An error occurred when verifying")
            print(e)
            return False
                
    async def transmit(self, account: Account, contract_address: Address, abi_path: str, chain_id: int, function_name: str, params, value, signed_proof: SignableMessage, is_none, proofMessage: ProofMessage, signedProofMessage, rpc_url: Optional[str], unsafe: bool = False):
        """
        Transmit: Verify the proof signature (so we know that the account owner signed off on the proof verification), verify the proof, then send the transaction to the contract.
        
        Returns:
            A transaction receipt
        """    
        
        web3 = Web3()
        
        v, r, s = signed_proof.v, signed_proof.r, signed_proof.s
        signed_proof_elements = (v, r, s)
        
        if not unsafe:
            if is_none:
                raise ValueError("Proof cannot be None when unsafe is False")
            
            signer = web3.eth.account.recover_message(signedProofMessage, signed_proof_elements)
            assert signer.lower() == account.address.lower()
            print("Proof signature verified! 🔥")
            assert self.verify(proofMessage.proofType.proof_path)
            print("Proof verified! ⚡️")
        else:
            if is_none:
                print("Warning: Proof is None. Skipping proof verification.")
            else:
                print("Signed proof retrieved! ✅")
                signer = web3.eth.account.recover_message(signedProofMessage, signed_proof_elements)
                assert signer.lower() == account.address.lower()
                print("Proof signature verified! 🔥")
                assert await self.verify(proofMessage.proofType.proof_path)
                print("Proof verified! ⚡️")
        
        print("All good! ✅ Sending transaction...")
        
        try:
            if rpc_url is not None:
                web3 = Web3(Web3.HTTPProvider(rpc_url))
            else:
                alchemy_url = os.getenv("ALCHEMY_URL")
                web3 = Web3(Web3.HTTPProvider(alchemy_url))
            nonce = web3.eth.get_transaction_count(account.address)  
            try:
                # Make this await again when we use etherscan to fetch ABIs
                calldata = self._generate_calldata(contract_address, chain_id, abi_path, function_name, params)
            except KeyError as e:
                print(f"Error generating calldata: {str(e)}")
                raise
            #TODO: Figure out how to get gasPrice
            try:
                transaction = {
                    "to": contract_address, 
                    "data": calldata,
                    "nonce": nonce,
                    "gas": web3.eth.estimate_gas({"to": contract_address, "data": calldata}),
                    "gasPrice": 40000000000,
                    "value": value
                }
            except KeyError as e:
                print(f"Error creating transaction dictionary: {str(e)}")
                raise
            print(f"Transaction: {transaction}")
            try:
                signed_tx = account.sign_transaction(transaction)
            except KeyError as e:
                print(f"Error signing transaction: {str(e)}")
                raise     
            print (f"Signed transaction: {signed_tx}")       
            try:
                tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            except ValueError as e:
                print(f"Error sending transaction: {str(e)}")
                return None
            except Exception as e:
                print(f"Error sending transaction: {str(e)}")  
                return None
            try:
                receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
                print("Transaction Completed.")
                return receipt
            except TimeExhausted:
                print("Transaction receipt retrieval timed out.")
                return None

            except asyncio.TimeoutError:
                print("Transaction receipt retrieval timed out after 300 seconds.")
                return None
        
        except ValueError as e:
            print(f"Error encoding transaction: {e}")
            return None
        
        except ContractCustomError as e:
            print(f"Custom error occurred: {e}")
            print(f"Error message: {e.args[0]}")
            return None

        except Exception as e:
            print(f"Error transmitting transaction: {str(e)}")
            print(f"Exception type: {type(e)}")
            return None
    
        
        
def get_deployment_id(model_id, version_id):
    """
    Retrieve the deployment ID for the model and version.

    Returns:
        int: The ID of the deployment.
    """
    client = DeploymentsClient(API_HOST)
    return client.list(model_id, version_id).root[0].id