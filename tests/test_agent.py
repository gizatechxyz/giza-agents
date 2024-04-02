from unittest.mock import Mock, patch

import pytest
from giza.schemas.jobs import Job, JobList
from giza.schemas.proofs import Proof

from giza_actions.agent import AgentResult


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


class JobsClientStub:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def create(self, *args, **kwargs):
        return Job(id=1, size="S", status="COMPLETED")

    def get(self, *args, **kwargs):
        return Job(id=1, size="S", status="COMPLETED")


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


@patch("giza_actions.agent.AgentResult._verify", return_value=True)
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


@patch("giza_actions.agent.AgentResult._wait_for_proof")
@patch("giza_actions.agent.AgentResult._start_verify_job")
@patch("giza_actions.agent.AgentResult._wait_for_verify")
def test_agentresult__verify(
    mock_wait_for_verify, mock_start_verify_job, mock_wait_for_proof
):
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
    mock_start_verify_job.assert_called_once()
    mock_wait_for_verify.assert_called_once()


@patch("giza_actions.agent.AgentResult._wait_for")
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


def test_agentresult__start_verify_job():
    agent = Mock()
    agent.framework = "CAIRO"
    agent.model_id = 1
    agent.version_id = 1

    result = AgentResult(
        input=[],
        result=[1],
        request_id="123",
        agent=agent,
        endpoint_client=EndpointsClientStub(),
    )

    result._proof = Proof(
        id=1, job_id=1, created_date="2022-01-01T00:00:00Z", request_id="123"
    )

    job = result._start_verify_job(JobsClientStub())

    assert job.id == 1
    assert job.size == "S"
    assert job.status == "COMPLETED"


@patch("giza_actions.agent.AgentResult._wait_for")
def test_agentresult__wait_for_verify(mock_wait_for):
    result = AgentResult(
        input=[],
        result=[1],
        request_id="123",
        agent=Mock(),
        endpoint_client=EndpointsClientStub(),
    )

    result._wait_for_verify(JobsClientStub())
    mock_wait_for.assert_called_once()


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


@patch("giza_actions.agent.time.sleep")
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
