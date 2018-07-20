import pytest
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
