import glob
import os

import thriftpy
from thrift_explorer.communication_models import Protocol, Transport
from thrift_explorer.thrift_models import BaseType
from thrift_explorer.thrift_parser import parse_service_specs
from thriftpy.protocol import (
    TBinaryProtocolFactory,
    TCompactProtocolFactory,
    TJSONProtocolFactory,
)


def _translate_arg(arg_spec, raw_arg):
    """
    translate the raw args into ones the client can handle.
    Basically this means turning parts of a dictionary into
    the correct objects for thrift. This is most relevant when 
    structs are introduced.
    """
    if isinstance(arg_spec.type_info, BaseType):
        return raw_arg
    else:
        raise ValueError("OMG")  # I will rethink this


def _translate_request_body(endpoint, request_body):
    """
    Translate the request dictionary into whatever arguments
    are required to make the call with the thrift client

    endpoint: The endpoint spec as parsed by ThriftManager 

    request_dict: dictionary containing the args that should match
    the service. The values should have been validated before hitting 
    this method
    """
    processed_args = {}
    for arg_spec in endpoint.args:
        processed_args[arg_spec.name] = _translate_arg(
            arg_spec, request_body[arg_spec.name]
        )
    return processed_args


def _load_thrifts(thrift_directory):
    thrifts = {}
    search_path = os.path.join(thrift_directory, "**/*thrift")
    for thrift_path in glob.iglob(search_path, recursive=True):
        thrift_filename = os.path.basename(thrift_path)
        thrifts[thrift_filename] = thriftpy.load(thrift_path)
    return thrifts


def _find_protocol_factory(protocol):
    if protocol == Protocol.BINARY:
        return TBinaryProtocolFactory()
    elif protocol == Protocol.JSON:
        return TJSONProtocolFactory()
    elif protocol == Protocol.COMPACT:
        return TCompactProtocolFactory()
    raise ValueError("Invalid protocol {}".format(protocol))


def _find_transport_factory(transport):
    if transport == Transport.BUFFERED:
        return thriftpy.transport.TBufferedTransportFactory()
    elif transport == Transport.FRAMED:
        return thriftpy.transport.TFramedTransportFactory()
    raise ValueError("Invalid transport {}".format(transport))


class ThriftManager(object):
    def __init__(self, thrift_directory):
        self.thrift_directory = thrift_directory
        self._thrifts = _load_thrifts(self.thrift_directory)
        self.service_specs = parse_service_specs(self._thrifts)

    def make_request(self, thrift_request):
        with thriftpy.rpc.client_context(
            service=getattr(
                self._thrifts[thrift_request.thrift_file], thrift_request.service_name
            ),
            host=thrift_request.host,
            port=thrift_request.port,
            proto_factory=_find_protocol_factory(thrift_request.protocol),
            trans_factory=_find_transport_factory(thrift_request.transport),
        ) as client:
            thrift_spec = self.service_specs[thrift_request.thrift_file]
            service = thrift_spec[thrift_request.service_name]
            return getattr(client, thrift_request.endpoint_name)(
                **_translate_request_body(
                    service.endpoints[thrift_request.endpoint_name],
                    thrift_request.request_body,
                )
            )
