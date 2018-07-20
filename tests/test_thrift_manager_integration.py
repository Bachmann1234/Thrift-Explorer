import pytest
from thrift_explorer.communication_models import ThriftRequest

pytestmark = pytest.mark.uses_server


def _build_request(method, body):
    return ThriftRequest(
        thrift_file="todo.thrift",
        service_name="TodoService",
        endpoint_name=method,
        host="127.0.0.1",
        port="6000",
        protocol="BINARY",
        transport="BUFFERED",
        request_body=body,
    )


def test_ping(todo_server, example_thrift_manager):
    response = example_thrift_manager.make_request(_build_request("ping", {}))
    assert not response


def test_complete_task_found(
    todo_server, todo_client, todo_thrift, example_thrift_manager
):
    task = todo_client.createTask("test task", "1531966806272")
    assert todo_client.getTask(task.taskId).description == "test task"
    response = example_thrift_manager.make_request(
        _build_request("completeTask", {"taskId": task.taskId})
    )
    assert response is None
    with pytest.raises(todo_thrift.Exceptions.NotFound):
        assert todo_client.getTask(task.taskId)
