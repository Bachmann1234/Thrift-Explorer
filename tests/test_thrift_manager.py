import pytest
from testing_utils import load_thrift_from_testdir
from thrift_explorer import thrift_manager
from thrift_explorer.communication_models import Protocol, Transport


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
