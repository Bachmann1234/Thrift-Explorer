import pytest

from thrift_explorer.communication_models import ThriftRequest
from todoserver import service

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


@pytest.fixture(autouse=True)
def clear_todo_db():
    service.clear_db()


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


def test_create_task(todo_server, todo_client, todo_thrift, example_thrift_manager):
    response = example_thrift_manager.make_request(
        _build_request(
            "createTask", {"description": "my task", "dueDate": "1531966806272"}
        )
    )
    assert {
        "__thrift_struct_class__": "Task",
        "description": "my task",
        "dueDate": "1531966806272",
        "taskId": "1",
    } == response


def test_get_task(todo_server, todo_client, example_thrift_manager):
    task = todo_client.createTask("test task", "1531966806272")
    response = example_thrift_manager.make_request(
        _build_request("getTask", {"taskId": task.taskId})
    )
    assert response == {
        "__thrift_struct_class__": "Task",
        "description": "test task",
        "dueDate": "1531966806272",
        "taskId": "1",
    }


def test_list_tasks(todo_server, todo_client, example_thrift_manager):
    todo_client.createTask("test task one", "due 1")
    todo_client.createTask("test task two", "due 2")
    todo_client.createTask("test task three", "due 3")

    response = example_thrift_manager.make_request(_build_request("listTasks", {}))

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
    ] == response
