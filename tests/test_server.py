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
