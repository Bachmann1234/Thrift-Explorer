import pytest

from thrift_explorer import server


@pytest.fixture
def client(example_thrift_directory):
    app = server.create_app({"THRIFT_DIRECTORY": example_thrift_directory})
    client = app.test_client()
    yield client


def test_list_services(client):
    response = client.get("/")
    assert (
        response.data
        == b'{"thrifts": {"Batman.thrift": ["BatPuter"], "todo.thrift": ["TodoService"]}}'
    )


def test_get_service_info(client):
    response = client.get("/Batman/BatPuter")
    assert (
        response.data
        == b'{"thrift": "Batman.thrift", "service": "BatPuter", "methods": ["ping", "getVillain", "addVillain", "saveCase"]}'
    )
    response = client.get("/Batman.thrift/BatPuter")
    assert (
        response.data
        == b'{"thrift": "Batman.thrift", "service": "BatPuter", "methods": ["ping", "getVillain", "addVillain", "saveCase"]}'
    )


def test_get_service_info_invalid_thrift(client):
    response = client.get("/notAThrift/BatPuter")
    assert response.status == "404 NOT FOUND"
    assert response.data == b"Thrift 'notAThrift.thrift' not found"


def test_get_service_info_invalid_service(client):
    response = client.get("/Batman/NotAService")
    assert response.status == "404 NOT FOUND"
    assert response.data == b"Service 'NotAService' not found"


def test_service_method_invalid_thrift(client):
    response = client.get("/notAThrift/BatPuter/getVillain")
    assert response.status == "404 NOT FOUND"
    assert response.data == b"Thrift 'notAThrift.thrift' not found"


def test_service_method_info_invalid_method(client):
    response = client.get("/Batman/BatPuter/notAMethod")
    assert response.status == "404 NOT FOUND"
    assert response.data == b"Method 'notAMethod' not found"
