import json
import logging
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Self, Tuple, Union

from ape import Contract, accounts, networks
from ape.contracts import ContractInstance
from ape.exceptions import NetworkError
from ape_accounts.accounts import InvalidPasswordError
from giza.cli import API_HOST
from giza.cli.client import AgentsClient, EndpointsClient, JobsClient, ProofsClient
from giza.cli.schemas.agents import Agent, AgentList, AgentUpdate
from giza.cli.schemas.jobs import Job, JobList
from giza.cli.schemas.proofs import Proof
from giza.cli.utils.enums import JobKind, JobStatus
from requests import HTTPError

from giza.agents.model import GizaModel
from giza.agents.utils import read_json

logger = logging.getLogger(__name__)


class GizaAgent(GizaModel):
    """
    Agents are intermediaries between users and Smart Contracts, facilitating seamless interaction with verifiable ML models and executing associated contracts. Uses Ape framework and GizaModel to verify a model proof off-chain, sign it with the user's account, and send results to a select EVM chain to execute code.
    """

    # TODO: (GIZ 502) Find a way to abstract away the chain_id to just a string with the chain name
    def __init__(
        self,
        id: int,
        version_id: int,
        contracts: Dict[str, str],
        chain: Optional[str] = None,
        account: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Args:
            model_id (int): The ID of the model.
            version_id (int): The version of the model.
            contracts (Dict[str, str]): The contracts to handle, must be a dictionary with the contract name as the key and the contract address as the value.
            chain_id (int): The ID of the blockchain network.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(id=id, version=version_id)
        self._agents_client = kwargs.pop("agents_client", AgentsClient(API_HOST))
        self._agent = self._retrieve_agent_info(self._agents_client)

        # Here we try to get the info from the agent in Giza if not provided
        try:
            if not contracts:
                contracts = self._agent.parameters["contracts"]
            if not chain:
                chain = self._agent.parameters["chain"]
            if not account:
                account = self._agent.parameters["account"]
        except KeyError as e:
            logger.error("Agent is missing required parameters")
            raise ValueError(f"Agent is missing required parameters: {e}")

        self.contract_handler = ContractHandler(contracts)
        self.chain = chain
        self.account = account
        self._check_passphrase_in_env()
        self._check_or_create_account()

        # Useful for testing
        network_parser: Callable = kwargs.get(
            "network_parser", networks.parse_network_choice
        )

        try:
            self._provider = network_parser(self.chain)
        except NetworkError:
            logger.error(f"Chain {self.chain} not found")
            raise ValueError(f"Chain {self.chain} not found")

    @classmethod
    def from_id(
        cls,
        id: int,
        contracts: Optional[Dict[str, Any]] = None,
        chain: Optional[str] = None,
        account: Optional[str] = None,
        **kwargs: Any,
    ) -> "GizaAgent":
        """
        Create an agent from an ID.
        """

        client: AgentsClient = kwargs.pop("client", AgentsClient(API_HOST))
        try:
            agent: Agent = client.get(id)
        except HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Agent with id {id} not found")
                raise ValueError(f"Agent with id {id} not found")
            logger.error(f"Failed to get agent: {e}")
            raise ValueError(f"Failed to get agent with id {id}: {e}")
        return cls(
            id=agent.parameters["model_id"],
            version_id=agent.parameters["version_id"],
            contracts=contracts if contracts else agent.parameters["contracts"],
            chain=chain if chain else agent.parameters["chain"],
            account=account if account else agent.parameters["account"],
            **kwargs,
        )

    def _check_or_create_account(self) -> None:
        """
        Check if the account exists in the execution environment, if not create it from the agent.
        """
        try:
            accounts.load(self.account)
        except Exception:
            logger.info(
                f"Account {self.account} not found locally, creating it from agent"
            )
            agent = self._agents_client.get(
                self._agent.id, params={"account_data": True}
            )
            account_path = Path.home().joinpath(".ape/accounts")
            logger.info(f"Creating account {self.account} from agent at {account_path}")
            account_path.mkdir(parents=True, exist_ok=True)
            with open(account_path / f"{self.account}.json", "w") as f:
                json.dump(agent.parameters["account_data"], f)
            logger.info(f"Account {self.account} created from agent")

    def _retrieve_agent_info(self, client: AgentsClient) -> Agent:
        """
        Retrieve the agent info.
        """
        try:
            params = {
                "q": [
                    f"model_id=={self.model_id}",
                    f"version_id=={self.version_id}",
                    f"endpoint_id=={self.endpoint_id}",
                ]
            }
            agents: AgentList = client.list(
                params=params,
            )
            if len(agents.root) == 0:
                raise ValueError(
                    f"Agent with model ID {self.model_id} and version ID {self.version_id} not found"
                )
            return agents.root[0]
        except HTTPError as e:
            logger.error(f"Failed to get agent: {e}")
            raise ValueError(f"Failed to get agent with id {self.model_id}: {e}")

    def _update_agent(self) -> None:
        """
        Update the agent.
        """
        try:
            parameters: Dict[Any, Any] = {}
            if (
                "chain" not in self._agent.parameters
                or self._agent.parameters["chain"] != self.chain
            ):
                self._agent.parameters["chain"] = self.chain
                parameters["chain"] = self.chain
                logger.info(f"Updating agent with chain {self.chain}")

            if (
                "account" not in self._agent.parameters
                or self._agent.parameters["account"] != self.account
            ):
                self._agent.parameters["account"] = self.account
                parameters["account"] = self.account
                path = (
                    Path.home()
                    .joinpath(".ape/accounts")
                    .joinpath(f"{self.account}.json")
                )
                account_data = read_json(str(path))
                parameters["account_data"] = account_data
                logger.info(f"Updating agent with account {self.account}")
            if (
                "contracts" not in self._agent.parameters
                or self._agent.parameters["contracts"]
                != self.contract_handler._contracts
            ):
                self._agent.parameters["contracts"] = self.contract_handler._contracts
                parameters["contracts"] = self.contract_handler._contracts
                logger.info("Updating agent with latest contracts")
            agent = AgentUpdate(parameters=parameters)
            self._agents_client.patch(self._agent.id, agent)
            logger.info("Agent updated!")
        except HTTPError as e:
            logger.error(f"Failed to update agent: {e}")
            raise ValueError(f"Failed to update agent with id {self.model_id}: {e}")

    def _check_passphrase_in_env(self) -> None:
        """
        Check if the passphrase is in the environment variables.
        """
        if self.account is None:
            raise ValueError("Account is not specified.")

        if f"{self.account.upper()}_PASSPHRASE" not in os.environ:
            logger.error(
                f"Passphrase for account {self.account} not found in environment variables. Passphrase must be stored in an environment variable named {self.account.upper()}_PASSPHRASE."
            )
            raise ValueError(
                f"Passphrase for account {self.account} not found in environment variables"
            )

    @contextmanager
    def execute(self) -> Any:
        """
        Execute the agent in the given ecosystem. Return the contract instace so the user can execute it.

        Args:
            ecosystem: The ecosystem to execute the agent in.
        """
        logger.debug("Provider configured")
        self._update_agent()
        with self._provider:
            self._account = accounts.load(self.account)
            logger.debug("Account loaded")
            try:
                if self.account is None:
                    raise ValueError("Account is not specified.")
                self._account.set_autosign(
                    True, passphrase=os.getenv(f"{self.account.upper()}_PASSPHRASE")
                )
            except InvalidPasswordError as e:
                logger.error(
                    f"Invalid passphrase for account {self.account}. Could not decrypt account."
                )
                raise ValueError(
                    f"Invalid passphrase for account {self.account}. Could not decrypt account."
                ) from e
            logger.debug("Autosign enabled")
            with accounts.use_sender(self._account):
                yield self.contract_handler.handle()

    def predict(
        self,
        input_file: Optional[str] = None,
        input_feed: Optional[Dict] = None,
        verifiable: bool = False,
        fp_impl: str = "FP16x16",
        custom_output_dtype: Optional[str] = None,
        job_size: str = "M",
        dry_run: bool = False,
        model_category: Optional[str] = None,
        **result_kwargs: Any,
    ) -> Optional[Union[Tuple[Any, Any], "AgentResult"]]:
        """
        Runs a round of inference on the model and saves the result.

        Args:
            input_file: The input file to use for inference
            input_feed: The input feed to use for inference
            job_size: The size of the job to run
        """
        result = super().predict(
            input_file=input_file,
            input_feed=input_feed,
            verifiable=verifiable,
            fp_impl=fp_impl,
            custom_output_dtype=custom_output_dtype,
            job_size=job_size,
            dry_run=dry_run,
            model_category=model_category,
        )

        self.verifiable = verifiable

        if not verifiable:
            logger.warning(
                "Inference is not verifiable. No request ID was returned. No proof will be generated."
            )
            return result

        if result is None:
            raise ValueError("The prediction result is None!")
        if isinstance(result, tuple):
            pred, request_id = result
            return AgentResult(
                input=input_feed,
                request_id=request_id,
                result=pred,
                endpoint_id=self.endpoint_id,
                agent=self,
                dry_run=dry_run,
                **result_kwargs,
            )
        else:
            raise ValueError("We are expecting result to be a tuple!")


class AgentResult:
    """
    A class to represent the result of an agent's inference.
    """

    def __init__(
        self,
        input: Any,
        request_id: str,
        result: Any,
        agent: GizaAgent,
        endpoint_client: EndpointsClient = EndpointsClient(API_HOST),
        jobs_client: JobsClient = JobsClient(API_HOST),
        proofs_client: ProofsClient = ProofsClient(API_HOST),
        **kwargs: Any,
    ):
        """
        Args:
            input (list): The input to the agent.
            request_id (str): The request ID of the proof.
            value (int): The value of the inference.
        """
        self.input: Any = input
        self.request_id: str = request_id
        self.__value: Any = result
        self.verified: bool = False
        self._endpoint_client = endpoint_client
        self._jobs_client = jobs_client
        self._proofs_client = proofs_client
        self._endpoint_id = agent.endpoint_id
        self._framework = agent.framework
        self._model_id = agent.model_id
        self._version_id = agent.version_id
        self._verify_job: Optional[Job] = None
        self._timeout: int = kwargs.get("timeout", 600)
        self._poll_interval: int = kwargs.get("poll_interval", 10)
        self._proof: Proof = None
        self._dry_run: bool = kwargs.get("dry_run", False)

        if not self._dry_run:
            self._proof_job: Job = self._get_proof_job(self._endpoint_client)

    def __repr__(self) -> str:
        return f"AgentResult(input={self.input}, request_id={self.request_id}, value={self.__value})"

    def _get_proof_job(self, client: EndpointsClient) -> Job:
        """
        Get the proof job.
        """

        jobs: JobList = client.list_jobs(self._endpoint_id)
        for job in jobs.root:
            if job.request_id == self.request_id:
                return job
        raise ValueError(f"Proof job for request ID {self.request_id} not found")

    @property
    def value(self) -> Any:
        """
        Get the value of the inference.
        """
        if self.verified:
            return self.__value
        self._verify()
        return self.__value

    def _verify(self) -> None:
        """
        Verify the proof. Check for the proof job, if its done start the verify job, then wait for verification.
        """
        if self._dry_run:
            logger.warning("Dry run enabled. Skipping verification.")
            self.verified = True
            return

        self._wait_for_proof(self._jobs_client, self._timeout, self._poll_interval)
        self.verified = self._verify_proof(self._endpoint_client)

    def _wait_for_proof(
        self, client: JobsClient, timeout: int = 600, poll_interval: int = 10
    ) -> None:
        """
        Wait for the proof job to finish.
        """
        self._wait_for(self._proof_job, client, timeout, poll_interval, JobKind.PROOF)
        self._proof = self._endpoint_client.get_proof(
            self._endpoint_id, self._proof_job.request_id
        )

    def _verify_proof(self, client: EndpointsClient) -> bool:
        """
        Verify the proof.
        """
        verify_result = client.verify_proof(
            self._endpoint_id,
            self._proof.id,
        )
        logger.info(f"Verify result is {verify_result.verification}")
        logger.info(f"Verify time is {verify_result.verification_time}")
        return True

    def _wait_for(
        self,
        job: Job,
        client: JobsClient,
        timeout: int = 600,
        poll_interval: int = 10,
        kind: JobKind = JobKind.VERIFY,
    ) -> None:
        """
        Wait for a job to finish.

        Args:
            job (Job): The job to wait for.
            client (JobsClient): The client to use.
            timeout (int): The timeout.
            poll_interval (int): The poll interval.
            kind (JobKind): The kind of job.

        Raises:
            ValueError: If the job failed.
            TimeoutError: If the job timed out.
        """
        start_time = time.time()
        wait_timeout = start_time + float(timeout)

        while True:
            now = time.time()
            if job.status == JobStatus.COMPLETED:
                logger.info(f"{str(kind).capitalize()} job completed")
                return
            elif job.status == JobStatus.FAILED:
                logger.error(f"{str(kind).capitalize()} job failed")
                raise ValueError(f"{str(kind).capitalize()} job failed")
            elif now > wait_timeout:
                logger.error(f"{str(kind).capitalize()} job timed out")
                raise TimeoutError(f"{str(kind).capitalize()} job timed out")
            else:
                job = client.get(job.id, params={"kind": kind})
                logger.info(
                    f"{str(kind).capitalize()} job is still running, elapsed time: {now - start_time}"
                )
            time.sleep(poll_interval)


class ContractHandler:
    """
    A class to handle multiple contracts and it's executions.

    The initiation of the contracts must be done inside ape's provider context,
    which means that it should be done insede the GizaAgent's execute context.
    """

    def __init__(self, contracts: Dict[str, str]) -> None:
        self._contracts = contracts
        self._contracts_instances: Dict[str, ContractInstance] = {}

    def __getattr__(self, name: str) -> ContractInstance:
        """
        Get the contract by name.
        """
        return self._contracts_instances[name]

    def _initiate_contract(self, address: str) -> ContractInstance:
        """
        Initiate the contract.
        """
        return Contract(address=address)

    def handle(self) -> Self:
        """
        Handle the contracts.
        """
        try:
            for name, address in self._contracts.items():
                self._contracts_instances[name] = self._initiate_contract(address)
        except NetworkError as e:
            logger.error(f"Failed to initiate contract: {e}")
            raise ValueError(
                f"Failed to initiate contract: {e}. Make sure this is executed inside `GizaAgent.execute()` or a provider context."
            )

        return self
