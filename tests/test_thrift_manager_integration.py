import datetime

import pytest

from thrift_explorer.communication_models import ThriftRequest
from todoserver import service

pytestmark = pytest.mark.uses_server


def _build_request(method, body, port="6000"):
    return ThriftRequest(
        thrift_file="todo.thrift",
        service_name="TodoService",
        endpoint_name=method,
        host="127.0.0.1",
        port=port,
        protocol="TBinaryProtocol",
        transport="TBufferedTransport",
        request_body=body,
    )


@pytest.fixture(autouse=True)
def clear_todo_db():
    service.clear_db()


def test_ping(todo_server, example_thrift_manager):
    request = _build_request("ping", {})
    assert [] == example_thrift_manager.validate_request(request)
    response = example_thrift_manager.make_request(request)
    assert response.data is None
    assert response.request == request
    assert response.status == "Success"
    assert response.time_to_connect > datetime.timedelta()
    assert response.time_to_make_reqeust > datetime.timedelta()


def test_complete_task_found(
    todo_server, todo_client, todo_thrift, example_thrift_manager
):
    task = todo_client.createTask("test task", "1531966806272")
    request = _build_request("completeTask", {"taskId": task.taskId})
    assert [] == example_thrift_manager.validate_request(request)
    assert todo_client.getTask(task.taskId).description == "test task"
    response = example_thrift_manager.make_request(request)
    assert response.data is None
    assert response.request == request
    assert response.status == "Success"
    assert response.time_to_connect > datetime.timedelta()
    assert response.time_to_make_reqeust > datetime.timedelta()
    with pytest.raises(todo_thrift.Exceptions.NotFound):
        assert todo_client.getTask(task.taskId)


def test_create_task(todo_server, todo_client, todo_thrift, example_thrift_manager):
    request = _build_request(
        "createTask", {"description": "my task", "dueDate": "1531966806272"}
    )
    assert [] == example_thrift_manager.validate_request(request)
    response = example_thrift_manager.make_request(request)
    assert {
        "__thrift_struct_class__": "Task",
        "description": "my task",
        "dueDate": "1531966806272",
        "taskId": "1",
    } == response.data
    assert response.request == request
    assert response.status == "Success"
    assert response.time_to_connect > datetime.timedelta()
    assert response.time_to_make_reqeust > datetime.timedelta()


def test_get_task(todo_server, todo_client, example_thrift_manager):
    task = todo_client.createTask("test task", "1531966806272")
    request = _build_request("getTask", {"taskId": task.taskId})
    assert [] == example_thrift_manager.validate_request(request)
    response = example_thrift_manager.make_request(request)
    assert response.data == {
        "__thrift_struct_class__": "Task",
        "description": "test task",
        "dueDate": "1531966806272",
        "taskId": "1",
    }
    assert response.request == request
    assert response.status == "Success"
    assert response.time_to_connect > datetime.timedelta()
    assert response.time_to_make_reqeust > datetime.timedelta()


def test_list_tasks(todo_server, todo_client, example_thrift_manager):
    todo_client.createTask("test task one", "due 1")
    todo_client.createTask("test task two", "due 2")
    todo_client.createTask("test task three", "due 3")

    request = _build_request("listTasks", {})
    assert [] == example_thrift_manager.validate_request(request)
    response = example_thrift_manager.make_request(request)

    assert [
        {
            "__thrift_struct_class__": "Task",
            "description": "test task one",
            "dueDate": "due 1",
            "taskId": "1",
        },
        {
            "__thrift_struct_class__": "Task",
            "description": "test task two",
            "dueDate": "due 2",
            "taskId": "2",
        },
        {
            "__thrift_struct_class__": "Task",
            "description": "test task three",
            "dueDate": "due 3",
            "taskId": "3",
        },
    ] == response.data
    assert response.request == request
    assert response.status == "Success"
    assert response.time_to_connect > datetime.timedelta()
    assert response.time_to_make_reqeust > datetime.timedelta()


def test_count_tasks(todo_server, todo_client, example_thrift_manager):
    todo_client.createTask("test task one", "due 1")
    todo_client.createTask("test task two", "due 2")
    todo_client.createTask("test task three", "due 3")

    request = _build_request("numTasks", {})
    assert [] == example_thrift_manager.validate_request(request)
    response = example_thrift_manager.make_request(request)
    assert 3 == response.data


def test_handle_exception(todo_server, example_thrift_manager):
    request = _build_request("getTask", {"taskId": "whatever"})
    assert [] == example_thrift_manager.validate_request(request)
    response = example_thrift_manager.make_request(request)
    assert response.data == {"__thrift_struct_class__": "NotFound"}
    assert response.request == request
    assert response.status == "NotFound"
    assert response.time_to_connect > datetime.timedelta()
    assert response.time_to_make_reqeust > datetime.timedelta()


def test_handle_unimplemented_method(todo_server, example_thrift_manager):
    # Designed to handle the case where the client thrift and the server
    # thrift are incompatible. In this case its a client method not handled
    # by the server
    request = _build_request("fancyNewMethod", {})
    assert [] == example_thrift_manager.validate_request(request)
    response = example_thrift_manager.make_request(request)
    assert response.data == "Failed to make call: TSocket read 0 bytes"
    assert response.request == request
    assert response.status == "ServerError"
    assert response.time_to_connect > datetime.timedelta()
    assert response.time_to_make_reqeust > datetime.timedelta()


def test_invalid_port(todo_server, example_thrift_manager):
    request = _build_request("ping", {}, port=9999)
    assert [] == example_thrift_manager.validate_request(request)
    response = example_thrift_manager.make_request(request)
    assert (
        response.data
        == "Failed to make client connection: Could not connect to ('127.0.0.1', 9999)"
    )
    assert response.request == request
    assert response.status == "ConnectionError"
    assert response.time_to_connect is None
    assert response.time_to_make_reqeust is None
