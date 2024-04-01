from unittest.mock import Mock, patch

from giza.schemas.jobs import Job, JobList

from giza_actions.agent import AgentResult


class EndpointsClientStub:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def list_jobs(self, *args, **kwargs):
        return JobList(root=[Job(id=1, size="S", status="COMPLETED", request_id="123")])


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
