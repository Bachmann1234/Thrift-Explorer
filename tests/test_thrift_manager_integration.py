import pytest
from thrift_explorer.communication_models import ThriftRequest

pytestmark = pytest.mark.uses_server


def test_void_argless_method(todo_server, example_thrift_manager):
    response = example_thrift_manager.make_request(
        ThriftRequest(
            thrift_file="todo.thrift",
            service_name="TodoService",
            endpoint_name="ping",
            host="127.0.0.1",
            port="6000",
            protocol="BINARY",
            transport="BUFFERED",
            request_body={},
        )
    )
    assert not response
