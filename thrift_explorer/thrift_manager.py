import glob
import os
from collections import defaultdict

import thriftpy
from thriftpy.protocol import (
    TBinaryProtocolFactory,
    TCompactProtocolFactory,
    TJSONProtocolFactory,
)
from thriftpy.thrift import TType

from thrift_explorer.communication_models import Protocol, Transport
from thrift_explorer.thrift_models import (
    BaseType,
    CollectionType,
    EnumType,
    MapType,
    ServiceEndpoint,
    StructType,
    ThriftService,
    ThriftSpec,
)

_COLLECTION_TYPES = set(["SET", "LIST"])


def _parse_type(type_info):
    try:
        ttype_code, nested_type_info = type_info
    except TypeError:
        ttype_code = type_info
        nested_type_info = None

    ttype = TType._VALUES_TO_NAMES[ttype_code]
    if nested_type_info is None:
        return BaseType(ttype)
    elif ttype in _COLLECTION_TYPES:
        return CollectionType(ttype=ttype, value_type=_parse_type(nested_type_info))
    elif ttype == "MAP":
        key, value = nested_type_info
        return MapType(
            ttype=ttype, key_type=_parse_type(key), value_type=_parse_type(value)
        )
    elif ttype == "STRUCT":
        return StructType(
            ttype=ttype,
            name=nested_type_info.__name__,
            fields=[
                _parse_arg(result) for result in nested_type_info.thrift_spec.values()
            ],
        )
    # Its a basic type but has defined nested type info. its probably an enum
    return EnumType(
        ttype=ttype,
        name=nested_type_info.__name__,
        names_to_values=nested_type_info._NAMES_TO_VALUES,
        values_to_names=nested_type_info._VALUES_TO_NAMES,
    )


def _parse_arg(thrift_arg):  # Consider renaming?
    try:
        ttype_code, name, required = thrift_arg
        type_info = None
    except ValueError:
        ttype_code, name, type_info, required = thrift_arg
    return ThriftSpec(
        name=name, type_info=_parse_type((ttype_code, type_info)), required=required
    )


def parse_thrift_endpoint(service, endpoint):
    endpoint_args = getattr(service, "{}_args".format(endpoint))
    endpoint_results = getattr(service, "{}_result".format(endpoint))
    return ServiceEndpoint(
        name=endpoint,
        args=[_parse_arg(arg) for arg in endpoint_args.thrift_spec.values()],
        results=[
            _parse_arg(result) for result in endpoint_results.thrift_spec.values()
        ],
    )


def parse_thrift_service(thrift_file, service, endpoints):
    return ThriftService(
        thrift_file,
        service.__name__,
        [parse_thrift_endpoint(service, endpoint) for endpoint in endpoints],
    )


def _load_thrifts(thrift_directory):
    thrifts = {}
    search_path = os.path.join(thrift_directory, "**/*thrift")
    for thrift_path in glob.iglob(search_path, recursive=True):
        thrift_filename = os.path.basename(thrift_path)
        thrifts[thrift_filename] = thriftpy.load(thrift_path)
    return thrifts


def _parse_service_specs(thrifts):
    result = defaultdict(dict)
    for thrift_file, module in thrifts.items():
        for thrift_service in module.__thrift_meta__["services"]:
            result[thrift_file][thrift_service.__name__] = parse_thrift_service(
                thrift_file,
                thrift_service,
                # I'm a bit confused why this is called services and not 'methods' or 'endpoints'
                thrift_service.thrift_services,
            )
    return result


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
        self.service_specs = _parse_service_specs(self._thrifts)

    def translate_request_body(self, request):
        return {}

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
            return getattr(client, thrift_request.endpoint_name)(
                self.translate_request_body(thrift_request)
            )
