import attr
from enum import Enum

"""
    Here are some things I can theoredically support
    but am punting on until I am further along
    timeout
    certificates/ssl
    timeouts (not sure I want this one)
    http vs rpc (currently supporting just rpc)
    unix socket rather than server
    finagle protocol
    mutliplex protocol
"""


class Protocol(Enum):
    BINARY = "binary"
    JSON = "json"
    COMPACT = "compact"


class Transport(Enum):
    BUFFERED = "buffered"
    FRAMED = "framed"


@attr.s(frozen=True)
class ThriftRequest(object):
    """
    The model containing all the information necessary to make a thrift request
        service:
            Service of the endpoint being requested
        endpoint:
            Endpoint being requested
        host:
            Hostname (or IP) where the service is hosted
        port:
            Port of the service being hit
        protocol:
            One of the supported thrift protocols
                BINARY
                JSON
                COMPACT
                MULTIPLEXED
        transport:
            One of the supported thrift transports
                BUFFERED
                FRAMED
        request_body:
            dictionary that represents the request being made
    """

    service = attr.ib()
    endpoint = attr.ib()
    host = attr.ib()
    port = attr.ib(converter=int)
    protocol = attr.ib(converter=Protocol)
    transport = attr.ib(converter=Transport)
    request_body = attr.ib(default=attr.Factory(dict))
