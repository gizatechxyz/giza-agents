from unittest.mock import Mock, patch

import pytest
from ape.exceptions import NetworkError
from giza.cli.schemas.jobs import Job, JobList
from giza.cli.schemas.logs import Logs
from giza.cli.schemas.proofs import Proof
from giza.cli.schemas.verify import VerifyResponse

from giza.agents import AgentResult, ContractHandler, GizaAgent


class EndpointsClientStub:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def list_jobs(self, *args, **kwargs):
        return JobList(root=[Job(id=1, size="S", status="COMPLETED", request_id="123")])

    def get_proof(self, *args, **kwargs):
        return Proof(
            id=1, job_id=1, created_date="2022-01-01T00:00:00Z", request_id="123"
        )

    def verify_proof(self, *args, **kwargs):
        return VerifyResponse(
            verification=True,
            verification_time=1,
        )

    def get_logs(self, *args, **kwargs):
        return Logs(logs="dummy_logs")


class JobsClientStub:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def create(self, *args, **kwargs):
        return Job(id=1, size="S", status="COMPLETED")

    def get(self, *args, **kwargs):
        return Job(id=1, size="S", status="COMPLETED")

    def get_logs(self, *args, **kwargs):
        return Logs(logs="dummy_logs")


class AccountTestStub:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def load(self, *args, **kwargs):
        return Mock()


def parser(*args, **kwargs):
    return "dummy_network"


# TODO: find a way to test the agent better than patching the __init__ method
@patch("giza.agents.agent.GizaAgent._check_or_create_account")
@patch("giza.agents.agent.GizaAgent._retrieve_agent_info")
@patch("giza.agents.agent.GizaAgent._check_passphrase_in_env")
@patch("giza.agents.model.GizaModel.__init__")
def test_agent_init(mock_check, mock_agent, mock_check_passphrase_in_env, mock_init_):
    agent = GizaAgent(
        id=1,
        version_id=1,
        contracts={"contract": "0x17807a00bE76716B91d5ba1232dd1647c4414912"},
        chain="ethereum:sepolia:geth",
        account="test",
        network_parser=parser,
    )

    assert agent.contract_handler._contracts == {
        "contract": "0x17807a00bE76716B91d5ba1232dd1647c4414912"
    }
    assert agent.chain == "ethereum:sepolia:geth"
    assert agent.account == "test"
    assert agent._provider == "dummy_network"

    mock_check_passphrase_in_env.assert_called_once()
    mock_init_.assert_called_once()
    mock_check.assert_called_once()
    mock_agent.assert_called_once()


@patch("giza.agents.agent.GizaAgent._retrieve_agent_info")
@patch("giza.agents.model.GizaModel.__init__")
def test_agent_init_with_check_succesful_raise(mock_info, mock_init_):
    """
    Test the agent init without a passphrase in the environment variables

    Args:
        mock_check (_type_): _description_
        mock_info (_type_): _description_
        mock_init_ (_type_): _description_
    """
    with pytest.raises(ValueError):
        GizaAgent(
            id=1,
            version_id=1,
            contracts={"contract": "0x17807a00bE76716B91d5ba1232dd1647c4414912"},
            chain="ethereum:sepolia:geth",
            account="test",
            network_parser=parser,
        )

    mock_init_.assert_called_once()
    mock_info.assert_called_once()


@patch("giza.agents.agent.GizaAgent._check_or_create_account")
@patch("giza.agents.agent.GizaAgent._retrieve_agent_info")
@patch("giza.agents.model.GizaModel.__init__")
@patch.dict("os.environ", {"TEST_PASSPHRASE": "test"})
def test_agent_init_with_check_succesful_check(mock_check, mock_info, mock_init_):
    GizaAgent(
        id=1,
        version_id=1,
        contracts={"contract": "0x17807a00bE76716B91d5ba1232dd1647c4414912"},
        chain="ethereum:sepolia:geth",
        account="test",
        network_parser=parser,
    )

    mock_init_.assert_called_once()
    mock_info.assert_called_once()
    mock_check.assert_called_once()


# TODO: find a better way, this should be kind of an integration test with ape, using a KeyfileAccount
@patch("giza.agents.agent.GizaAgent._update_agent")
@patch("giza.agents.agent.GizaAgent._check_or_create_account")
@patch("giza.agents.agent.GizaAgent._retrieve_agent_info")
@patch("giza.agents.model.GizaModel.__init__")
@patch.dict("os.environ", {"TEST_PASSPHRASE": "test"})
@pytest.mark.use_network("ethereum:local:test")
def test_agent_execute(
    mock_update: Mock, mock_check: Mock, mock_info: Mock, mock_init_: Mock
):
    agent = GizaAgent(
        id=1,
        version_id=1,
        contracts={"contract": "0x17807a00bE76716B91d5ba1232dd1647c4414912"},
        chain="ethereum:local:test",
        account="test",
    )
    with patch("giza.agents.agent.accounts", return_value=AccountTestStub()), patch(
        "giza.agents.agent.Contract"
    ) as mock_get_contract:
        with agent.execute() as contract:
            assert contract is not None

    mock_init_.assert_called_once()
    mock_info.assert_called_once()
    mock_check.assert_called_once()
    mock_get_contract.assert_called_once()
    mock_update.assert_called_once()


@patch("giza.agents.agent.GizaAgent._check_or_create_account")
@patch("giza.agents.agent.GizaAgent._retrieve_agent_info")
@patch("giza.agents.model.GizaModel.__init__")
@patch("giza.agents.model.GizaModel.predict", return_value=([1], "123"))
@patch(
    "giza.agents.agent.AgentResult._get_proof_job",
    return_value=Job(id=1, size="S", status="COMPLETED"),
)
@patch.dict("os.environ", {"TEST_PASSPHRASE": "test"})
def test_agent_predict(
    mock_check: Mock,
    mock_info: Mock,
    mock_init_: Mock,
    mock_predict: Mock,
    mock_get_proof_job: Mock,
):
    # Mock the endpoint data
    GizaAgent.framework = Mock()
    GizaAgent.version_id = Mock()
    GizaAgent.model_id = Mock()

    agent = GizaAgent(
        id=1,
        version_id=1,
        contracts={"contract": "0x17807a00bE76716B91d5ba1232dd1647c4414912"},
        chain="ethereum:local:test",
        account="test",
    )
    agent.endpoint_id = 1

    result = agent.predict(input_feed={"image": [1]}, verifiable=True)

    assert agent.verifiable is True
    assert isinstance(result, AgentResult)
    mock_get_proof_job.assert_called_once()
    mock_predict.assert_called_once()
    mock_init_.assert_called_once()
    mock_check.assert_called_once()
    mock_info.assert_called_once()


def test_agentresult_init():
    result = AgentResult(
        input=[],
        result=[1],
        request_id="123",
        agent=Mock(),
        endpoint_client=EndpointsClientStub(),
    )
    assert result.input == []
    assert result.request_id == "123"
    assert result._AgentResult__value == [1]


@patch("giza.agents.agent.AgentResult._verify", return_value=True)
def test_agentresult_value_already_verified(verify_mock):
    result = AgentResult(
        input=[],
        result=[1],
        request_id="123",
        agent=Mock(),
        endpoint_client=EndpointsClientStub(),
    )

    assert result.value == [1]
    verify_mock.assert_called_once()


def test_agentresult__get_proof_job():
    result = AgentResult(
        input=[],
        result=[1],
        request_id="123",
        agent=Mock(),
        endpoint_client=EndpointsClientStub(),
    )

    job = result._get_proof_job(EndpointsClientStub())

    assert job.id == 1
    assert job.size == "S"
    assert job.status == "COMPLETED"
    assert job.request_id == "123"


@patch("giza.agents.agent.AgentResult._wait_for_proof")
@patch("giza.agents.agent.AgentResult._verify_proof", return_value=True)
def test_agentresult__verify(mock_verify, mock_wait_for_proof):
    result = AgentResult(
        input=[],
        result=[1],
        request_id="123",
        agent=Mock(),
        endpoint_client=EndpointsClientStub(),
    )

    result._verify()

    assert result.verified is True
    mock_wait_for_proof.assert_called_once()
    mock_verify.assert_called_once()


@patch("giza.agents.agent.AgentResult._wait_for")
def test_agentresult__wait_for_proof(mock_wait_for):
    result = AgentResult(
        input=[],
        result=[1],
        request_id="123",
        agent=Mock(),
        endpoint_client=EndpointsClientStub(),
    )

    result._wait_for_proof(EndpointsClientStub())

    assert result._proof.id == 1
    assert result._proof.job_id == 1
    mock_wait_for.assert_called_once()


def test_agentresult__verify_proof():
    result = AgentResult(
        input=[],
        result=[1],
        request_id="123",
        agent=Mock(),
        endpoint_client=EndpointsClientStub(),
    )
    # Add a dummy proof to the result so we can verify it
    result._proof = Proof(
        id=1, job_id=1, created_date="2022-01-01T00:00:00Z", request_id="123"
    )

    assert result._verify_proof(EndpointsClientStub())


def test_agentresult__wait_for_job_completed():
    result = AgentResult(
        input=[],
        result=[1],
        request_id="123",
        agent=Mock(),
        endpoint_client=EndpointsClientStub(),
    )

    wait_return = result._wait_for(
        job=Job(id=1, size="S", status="COMPLETED"), client=JobsClientStub()
    )
    assert wait_return is None


def test_agentresult__wait_for_job_failed():
    result = AgentResult(
        input=[],
        result=[1],
        request_id="123",
        agent=Mock(),
        endpoint_client=EndpointsClientStub(),
    )

    with pytest.raises(ValueError):
        result._wait_for(
            job=Job(id=1, size="S", status="FAILED"), client=JobsClientStub()
        )


def test_agentresult__wait_for_timeout():
    result = AgentResult(
        input=[],
        result=[1],
        request_id="123",
        agent=Mock(),
        endpoint_client=EndpointsClientStub(),
    )

    with pytest.raises(TimeoutError):
        result._wait_for(
            job=Job(id=1, size="S", status="PROCESSING"),
            client=JobsClientStub(),
            timeout=-1,
        )


@patch("giza.agents.agent.time.sleep")
def test_agentresult__wait_for_poll_job(mock_sleep):
    result = AgentResult(
        input=[],
        result=[1],
        request_id="123",
        agent=Mock(),
        endpoint_client=EndpointsClientStub(),
    )

    wait_return = result._wait_for(
        job=Job(id=1, size="S", status="PROCESSING"),
        client=JobsClientStub(),
        poll_interval=0.1,
    )

    assert wait_return is None
    mock_sleep.assert_called_once_with(0.1)


def test_contract_handler_init():
    handler = ContractHandler(
        contracts={"contract": "0x17807a00bE76716B91d5ba1232dd1647c4414912"}
    )

    assert handler._contracts == {
        "contract": "0x17807a00bE76716B91d5ba1232dd1647c4414912"
    }


def test_contract_handler_getattr():
    handler = ContractHandler(
        contracts={"contract": "0x17807a00bE76716B91d5ba1232dd1647c4414912"}
    )

    handler._contracts_instances = {"contract": Mock()}

    handler.contract.execute()

    handler.contract.execute.assert_called_once()


@patch("giza.agents.agent.Contract")
def test_contract_handler__initiate_contract(mock_contract):
    handler = ContractHandler(
        contracts={"contract": "0x17807a00bE76716B91d5ba1232dd1647c4414912"}
    )

    handler._initiate_contract("0x17807a00bE76716B91d5ba1232dd1647c4414912")

    mock_contract.assert_called_with(
        address="0x17807a00bE76716B91d5ba1232dd1647c4414912"
    )


@patch("giza.agents.agent.Contract")
def test_contract_handler_handle(mock_contract):
    handler = ContractHandler(
        contracts={
            "contract": "0x17807a00bE76716B91d5ba1232dd1647c4414912",
            "contract2": "0x17807a00bE76716B91d5ba1232dd1647c4414912",
        }
    )

    result = handler.handle()

    result.contract.test()
    result.contract2.test()

    assert isinstance(result, ContractHandler)
    mock_contract.assert_called_with(
        address="0x17807a00bE76716B91d5ba1232dd1647c4414912"
    )


@patch("giza.agents.agent.ContractHandler._initiate_contract", side_effect=NetworkError)
def test_contract_handler_network_error(mock_contract):
    handler = ContractHandler(
        contracts={
            "contract": "0x17807a00bE76716B91d5ba1232dd1647c4414912",
            "contract2": "0x17807a00bE76716B91d5ba1232dd1647c4414912",
        }
    )

    with pytest.raises(ValueError):
        handler.handle()
