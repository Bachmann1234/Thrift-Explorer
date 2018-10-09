import pytest

from testing_utils import load_thrift_from_testdir
from thrift_explorer import thrift_manager
from thrift_explorer.communication_models import (
    Error,
    ErrorCode,
    FieldError,
    Protocol,
    ThriftRequest,
    Transport,
)
from thrift_explorer.thrift_models import ThriftSpec, TString


def _build_request(**kwargs):
    return ThriftRequest(
        thrift_file=kwargs.get("thrift_file", "todo.thrift"),
        service_name=kwargs.get("service_name", "TodoService"),
        endpoint_name=kwargs.get("endpoint_name", "ping"),
        host=kwargs.get("host", "127.0.0.1"),
        port=kwargs.get("port", "6000"),
        protocol=kwargs.get("protocol", "TBinaryProtocol"),
        transport=kwargs.get("transport", "TBufferedTransport"),
        request_body=kwargs.get("request_body", {}),
    )


@pytest.mark.parametrize(
    "input_protocol, expected",
    [
        (Protocol.BINARY, "TCyBinaryProtocolFactory"),
        (Protocol.JSON, "TJSONProtocolFactory"),
        (Protocol.COMPACT, "TCompactProtocolFactory"),
    ],
)
def test_find_protocol_factory(input_protocol, expected):
    assert (
        expected
        == thrift_manager._find_protocol_factory(input_protocol).__class__.__name__
    )


@pytest.mark.parametrize(
    "input_transport, expected",
    [
        (Transport.BUFFERED, "TCyBufferedTransportFactory"),
        (Transport.FRAMED, "TCyFramedTransportFactory"),
    ],
)
def test_find_transport_factory(input_transport, expected):
    assert (
        expected
        == thrift_manager._find_transport_factory(input_transport).__class__.__name__
    )


def test_invalid_transport_raises_valueerror():
    with pytest.raises(ValueError):
        thrift_manager._find_transport_factory("Bat")


def test_invalid_protocol_raises_valueerror():
    with pytest.raises(ValueError):
        thrift_manager._find_protocol_factory("Bat")


def test_translate_basic_response():
    assert 4 == thrift_manager.translate_thrift_response(4)


def test_dict_response():
    assert {"dog": 7, "cat": 5} == thrift_manager.translate_thrift_response(
        {"dog": 7, "cat": 5}
    )


def test_set_response():
    assert {1, 2, 3} == thrift_manager.translate_thrift_response({1, 2, 3})


def test_list_response():
    assert [1, 2, 3] == thrift_manager.translate_thrift_response([1, 2, 3])


def test_struct_response():
    struct_thrift_module = load_thrift_from_testdir("structThrift.thrift")
    assert {
        "__thrift_struct_class__": "MyStruct",
        "myIntStruct": 4,
        "myOtherStruct": {
            "__thrift_struct_class__": "MyOtherStruct",
            "ints": [9, 4, 1, 11],
            "id": "test",
        },
    } == thrift_manager.translate_thrift_response(
        struct_thrift_module.MyStruct(
            myIntStruct=4,
            myOtherStruct=struct_thrift_module.MyOtherStruct(
                id="test", ints=[9, 4, 1, 11]
            ),
        )
    )


def test_thrift_not_loaded(example_thrift_manager):
    request = _build_request(thrift_file="notathrift.thrift")
    assert [
        Error(
            code=ErrorCode.THRIFT_NOT_LOADED,
            message="Thrift File 'notathrift.thrift' not loaded in ThriftManager",
        )
    ] == example_thrift_manager.validate_request(request)


def test_invalid_service(example_thrift_manager):
    request = _build_request(service_name="notaservice")
    assert [
        Error(
            code=ErrorCode.SERVICE_NOT_IN_THRIFT,
            message="Service 'notaservice' not in thrift 'todo.thrift'",
        )
    ] == example_thrift_manager.validate_request(request)


def test_invalid_endpoint(example_thrift_manager):
    request = _build_request(endpoint_name="notanendpoint")
    assert [
        Error(
            code=ErrorCode.ENDPOINT_NOT_IN_SERVICE,
            message="Endpoint 'notanendpoint' not in service 'TodoService' in thrift 'todo.thrift'",
        )
    ] == example_thrift_manager.validate_request(request)


def test_valid_request(example_thrift_manager):
    request = _build_request(
        endpoint_name="createTask", request_body={"dueDate": "313123123"}
    )
    assert [] == example_thrift_manager.validate_request(request)


def test_required_argument_missing(example_thrift_manager):
    request = _build_request(endpoint_name="completeTask", request_body={})
    assert [
        FieldError(
            arg_spec=ThriftSpec(
                field_id=1, name="taskId", type_info=TString(), required=True
            ),
            code=ErrorCode.REQUIRED_FIELD_MISSING,
            message="Required Field 'taskId' not found",
        )
    ] == example_thrift_manager.validate_request(request)


def test_request_body_has_invalid_data(example_thrift_manager):
    request = _build_request(endpoint_name="completeTask", request_body={"taskId": [4]})
    assert [
        FieldError(
            arg_spec=ThriftSpec(
                field_id=1, name="taskId", type_info=TString(), required=True
            ),
            code=ErrorCode.FIELD_VALIDATION_ERROR,
            message="Expected str but got list",
        )
    ] == example_thrift_manager.validate_request(request)


def test_list_thrift_services(example_thrift_manager):
    assert {
        "Batman.thrift": ["BatPuter"],
        "todo.thrift": ["TodoService"],
    } == example_thrift_manager.list_thrift_services()


def test_get_thrift(example_thrift_manager):
    assert "BatPuter" in example_thrift_manager.get_thrift("Batman.thrift")
    assert not example_thrift_manager.get_thrift("Not.thrift")


def test_get_service(example_thrift_manager):
    service = example_thrift_manager.get_service("Batman.thrift", "BatPuter")
    assert "BatPuter" == service.name
    assert not example_thrift_manager.get_service("Not.thrift", "BatPuter")
    assert not example_thrift_manager.get_service("Batman.thrift", "Billy")


def test_get_method(example_thrift_manager):
    method = example_thrift_manager.get_method("Batman.thrift", "BatPuter", "ping")
    assert method.name == "ping"
    assert not example_thrift_manager.get_method("Not.thrift", "BatPuter", "ping")
    assert not example_thrift_manager.get_method("Batman.thrift", "Billy", "ping")
    assert not example_thrift_manager.get_method("Batman.thrift", "Billy", "pong")


def test_thrift_definition(example_thrift_manager, batman_thrift_text):
    assert batman_thrift_text == example_thrift_manager.thrift_definition(
        "Batman.thrift"
    )
