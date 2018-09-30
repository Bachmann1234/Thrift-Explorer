import datetime
import json

import pytest

from thrift_explorer import server
from todoserver import service


def get_client(thrift_dir):
    app = server.create_app(
        {
            "THRIFT_DIRECTORY": thrift_dir,
            "DEFAULT_PROTOCOL": "TBinaryProtocol",
            "DEFAULT_TRANSPORT": "TBufferedTransport",
        }
    )
    app.testing = True
    return app.test_client()


@pytest.fixture
def flask_client(example_thrift_directory):
    yield get_client(example_thrift_directory)


@pytest.fixture(autouse=True)
def clear_todo_db():
    service.clear_db()


def test_list_services(flask_client):
    response = flask_client.get("/")
    assert response.status == "200 OK"
    assert (
        response.data
        == b'{"thrifts": {"Batman.thrift": ["BatPuter"], "todo.thrift": ["TodoService"]}}'
    )


def test_get_service_info(flask_client):
    response = flask_client.get("/Batman/BatPuter")
    assert response.status == "200 OK"
    assert (
        response.data
        == b'{"thrift": "Batman.thrift", "service": "BatPuter", "methods": ["ping", "getVillain", "addVillain", "saveCase"]}'
    )
    response = flask_client.get("/Batman.thrift/BatPuter")
    assert (
        response.data
        == b'{"thrift": "Batman.thrift", "service": "BatPuter", "methods": ["ping", "getVillain", "addVillain", "saveCase"]}'
    )


def test_get_service_info_invalid_thrift(flask_client):
    response = flask_client.get("/notAThrift/BatPuter")
    assert response.status == "404 NOT FOUND"
    assert response.data == b"Thrift 'notAThrift.thrift' not found"


def test_get_service_info_invalid_service(flask_client):
    response = flask_client.get("/Batman/NotAService")
    assert response.status == "404 NOT FOUND"
    assert response.data == b"Service 'NotAService' not found"


def test_service_method_invalid_thrift(flask_client):
    response = flask_client.get("/notAThrift/BatPuter/getVillain")
    assert response.status == "404 NOT FOUND"
    assert response.data == b"Thrift 'notAThrift.thrift' not found"


def test_service_method_info_invalid_method(flask_client):
    response = flask_client.get("/Batman/BatPuter/notAMethod")
    assert response.status == "404 NOT FOUND"
    assert response.data == b"Method 'notAMethod' not found"


def test_get_thrift_definition_invalid_thrift(flask_client):
    response = flask_client.get("/notAThrift")
    assert response.status == "404 NOT FOUND"
    assert response.data == b"Thrift 'notAThrift.thrift' not found"


def test_get_thrift_definition(flask_client, batman_thrift_text):
    response = flask_client.get("/Batman")
    assert response.status == "200 OK"
    assert response.data == batman_thrift_text.encode("utf-8")


def test_service_method_get(flask_client):
    response = flask_client.get("/Batman/BatPuter/getVillain")
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
    todo_client.createTask("task 1", "12-12-2012")
    todo_client.createTask("task 2", "12-12-2012")
    response = flask_client.post(
        "/todo/TodoService/numTasks",
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
        "data": 2,
    }

    actual = json.loads(response.data)
    # Time wont be exact. But make sure we get properly formatted data
    datetime.datetime.strptime(actual["time_to_make_request"], "%H:%M:%S.%f")
    datetime.datetime.strptime(actual["time_to_connect"], "%H:%M:%S.%f")
    del actual["time_to_make_request"]
    del actual["time_to_connect"]
    assert response.status == "200 OK"
    assert actual == expected
