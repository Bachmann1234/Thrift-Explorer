import datetime
import json

import pytest

from thrift_explorer import server
from thrift_explorer.server import (
    DEFAULT_PROTOCOL_ENV,
    DEFAULT_TRANSPORT_ENV,
    THRIFT_DIRECTORY_ENV,
)
from todoserver import service


def get_client(thirft_dir, monkeypatch):
    monkeypatch.setenv(THRIFT_DIRECTORY_ENV, thirft_dir)
    from thrift_explorer.wsgi import application

    application.testing = True
    return application.test_client()


@pytest.fixture
def flask_client(example_thrift_directory, monkeypatch):
    yield get_client(example_thrift_directory, monkeypatch)


@pytest.fixture(autouse=True)
def clear_todo_db():
    service.clear_db()


def test_list_services(flask_client):
    response = flask_client.get("/")
    assert response.status == "200 OK"
    assert json.loads(response.data) == {
        "thrifts": [
            {
                "methods": ["addVillain", "getVillain", "ping", "saveCase"],
                "service": "BatPuter",
                "thrift": "Batman.thrift",
            },
            {
                "methods": [
                    "completeTask",
                    "createTask",
                    "createTaskWithObject",
                    "fancyNewMethod",
                    "getTask",
                    "listTasks",
                    "numTasks",
                    "ping",
                ],
                "service": "TodoService",
                "thrift": "todo.thrift",
            },
        ]
    }


def test_get_service_info(flask_client):
    response = flask_client.get("/Batman/BatPuter/")
    assert response.status == "200 OK"
    assert (
        response.data
        == b'{"thrift": "Batman.thrift", "service": "BatPuter", "methods": ["addVillain", "getVillain", "ping", "saveCase"]}'
    )


def test_get_service_info_invalid_thrift(flask_client):
    response = flask_client.get("/notAThrift/BatPuter/")
    assert response.status == "404 NOT FOUND"
    assert response.data == b"Thrift 'notAThrift.thrift' not found"


def test_get_service_info_invalid_service(flask_client):
    response = flask_client.get("/Batman/NotAService/")
    assert response.status == "404 NOT FOUND"
    assert response.data == b"Service 'NotAService' not found"


def test_service_method_invalid_thrift(flask_client):
    response = flask_client.get("/notAThrift/BatPuter/getVillain/")
    assert response.status == "404 NOT FOUND"
    assert response.data == b"Thrift 'notAThrift.thrift' not found"


def test_service_method_info_invalid_method(flask_client):
    response = flask_client.get("/Batman/BatPuter/notAMethod/")
    assert response.status == "404 NOT FOUND"
    assert response.data == b"Method 'notAMethod' not found"


def test_get_thrift_definition_invalid_thrift(flask_client):
    response = flask_client.get("/notAThrift/")
    assert response.status == "404 NOT FOUND"
    assert response.data == b"Thrift 'notAThrift.thrift' not found"


def test_get_thrift_definition(flask_client, batman_thrift_text):
    response = flask_client.get("/Batman/")
    assert response.status == "200 OK"
    assert response.data == batman_thrift_text.encode("utf-8")


def test_service_method_get(flask_client):
    response = flask_client.get("/Batman/BatPuter/getVillain/")
    assert response.status == "200 OK"
    assert json.loads(response.data) == {
        "thrift_file": "Batman.thrift",
        "service_name": "BatPuter",
        "endpoint_name": "getVillain",
        "host": "<hostname>",
        "port": 9090,
        "protocol": "tbinaryprotocol",
        "transport": "tbufferedtransport",
        "request_body": {},
    }


def test_service_method_post(todo_server, todo_client, flask_client):
    response = flask_client.post(
        "/todo/TodoService/createTask/",
        data=json.dumps(
            {
                "host": "127.0.0.1",
                "port": 6000,
                "request_body": {"description": "task 1", "dueDate": "12-12-2012"},
            }
        ),
    )
    assert response.status == "200 OK"

    response = flask_client.post(
        "/todo/TodoService/numTasks/",
        data=json.dumps({"host": "127.0.0.1", "port": 6000, "request_body": {}}),
    )
    expected = {
        "status": "Success",
        "request": {
            "thrift_file": "todo.thrift",
            "service_name": "TodoService",
            "endpoint_name": "numTasks",
            "host": "127.0.0.1",
            "port": 6000,
            "protocol": "tbinaryprotocol",
            "transport": "tbufferedtransport",
            "request_body": {},
        },
        "data": 1,
    }

    actual = json.loads(response.data)
    # Time wont be exact. But make sure we get properly formatted data
    datetime.datetime.strptime(actual["time_to_make_request"], "%H:%M:%S.%f")
    datetime.datetime.strptime(actual["time_to_connect"], "%H:%M:%S.%f")
    del actual["time_to_make_request"]
    del actual["time_to_connect"]
    assert response.status == "200 OK"
    assert actual == expected


def test_service_method_post_with_object_arg(todo_server, todo_client, flask_client):
    response = flask_client.post(
        "/todo/TodoService/createTaskWithObject/",
        data=json.dumps(
            {
                "host": "127.0.0.1",
                "port": 6000,
                "request_body": {
                    "task": {"description": "task 1", "dueDate": "12-12-2012"}
                },
            }
        ),
    )
    assert response.status == "200 OK"

    response = flask_client.post(
        "/todo/TodoService/numTasks/",
        data=json.dumps({"host": "127.0.0.1", "port": 6000, "request_body": {}}),
    )
    expected = {
        "status": "Success",
        "request": {
            "thrift_file": "todo.thrift",
            "service_name": "TodoService",
            "endpoint_name": "numTasks",
            "host": "127.0.0.1",
            "port": 6000,
            "protocol": "tbinaryprotocol",
            "transport": "tbufferedtransport",
            "request_body": {},
        },
        "data": 1,
    }

    actual = json.loads(response.data)
    # Time wont be exact. But make sure we get properly formatted data
    datetime.datetime.strptime(actual["time_to_make_request"], "%H:%M:%S.%f")
    datetime.datetime.strptime(actual["time_to_connect"], "%H:%M:%S.%f")
    del actual["time_to_make_request"]
    del actual["time_to_connect"]
    assert response.status == "200 OK"
    assert actual == expected


def test_service_invalid_call(todo_server, todo_client, flask_client):
    response = flask_client.post(
        "/todo/TodoService/completeTask/",
        data=json.dumps({"host": "127.0.0.1", "port": 6000, "request_body": {}}),
    )
    assert response.status == "400 BAD REQUEST"
    assert json.loads(response.data) == {
        "errors": [
            {
                "arg_spec": {
                    "field_id": 1,
                    "name": "taskId",
                    "required": True,
                    "type_info": {"ttype": "string"},
                },
                "code": "REQUIRED_FIELD_MISSING",
                "message": "Required Field 'taskId' not found",
            }
        ]
    }


def test_service_missing_host(todo_server, todo_client, flask_client):
    response = flask_client.post(
        "/todo/TodoService/createTask/",
        data=json.dumps(
            {
                "port": 6000,
                "request_body": {"description": "task 1", "dueDate": "12-12-2012"},
            }
        ),
    )
    assert response.status == "400 BAD REQUEST"
    assert json.loads(response.data) == {
        "errors": [
            {
                "code": "INVALID_REQUEST",
                "message": "'host' must be <class 'str'> (got None that is a <class 'NoneType'>).",
            }
        ]
    }


def test_invalid_protocol(todo_server, todo_client, flask_client):
    response = flask_client.post(
        "/todo/TodoService/createTask/",
        data=json.dumps(
            {
                "host": "localhost",
                "transport": "batman!",
                "port": 6000,
                "request_body": {"description": "task 1", "dueDate": "12-12-2012"},
            }
        ),
    )
    assert response.status == "400 BAD REQUEST"
    assert json.loads(response.data) == {
        "errors": [
            {"code": "INVALID_REQUEST", "message": "'batman!' is not a valid Transport"}
        ]
    }
