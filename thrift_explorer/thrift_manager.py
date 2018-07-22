import datetime
import glob
import os

import thriftpy
from thriftpy.protocol import (
    TBinaryProtocolFactory,
    TCompactProtocolFactory,
    TJSONProtocolFactory,
)

from thrift_explorer.communication_models import Protocol, ThriftResponse, Transport
from thrift_explorer.thrift_parser import parse_service_specs


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


def translate_request_body(endpoint, request_body, thrift_module):
    """
    Translate the request dictionary into whatever arguments
    are required to make the call with the thrift client

    This method assumes the request body had been validated and is correct

    endpoint: The endpoint spec as parsed by ThriftManager

    request_body: dictionary containing the args that should match
    the service. The values should have been validated before hitting
    this method

    thrift_module: thrift file as loaded in by thriftpy.load
    """
    processed_args = {}
    for arg_spec in endpoint.args:
        processed_args[arg_spec.name] = arg_spec.type_info.format_arg_for_thrift(
            request_body[arg_spec.name], thrift_module
        )
    return processed_args


def translate_thrift_response(response):
    if not response:
        return response
    elif isinstance(response, (list,)):
        return [translate_thrift_response(prop) for prop in response]
    elif isinstance(response, (set,)):
        return {translate_thrift_response(prop) for prop in response}
    elif isinstance(response, (dict,)):
        return {
            translate_thrift_response(key): translate_thrift_response(value)
            for key, value in response.items()
        }
    elif hasattr(response, "thrift_spec"):
        struct = {"__thrift_struct_class__": response.__class__.__name__}
        for thrift_spec_parts in response.thrift_spec.values():
            try:
                _, name, _ = thrift_spec_parts
            except ValueError:
                _, name, _, _ = thrift_spec_parts
            struct[name] = translate_thrift_response(getattr(response, name, None))
        return struct
    return response


def find_request_exceptions(possible_results):
    exceptions = []
    for result in possible_results.thrift_spec.values():
        try:
            _, _, clazz, _ = result
            if issubclass(clazz, BaseException):
                exceptions.append(clazz)
        except TypeError:
            # Exceptions must be classes.
            # Results that dont blow up into 4
            # values cannot be classes
            pass
    return tuple(exceptions)


class ThriftManager(object):
    def __init__(self, thrift_directory):
        self.thrift_directory = thrift_directory
        self._thrifts = _load_thrifts(self.thrift_directory)
        self.service_specs = parse_service_specs(self._thrifts)

    def make_request(self, thrift_request):
        thriftpy_service = getattr(
            self._thrifts[thrift_request.thrift_file], thrift_request.service_name
        )
        time_before_client = datetime.datetime.now()
        with thriftpy.rpc.client_context(
            service=thriftpy_service,
            host=thrift_request.host,
            port=thrift_request.port,
            proto_factory=_find_protocol_factory(thrift_request.protocol),
            trans_factory=_find_transport_factory(thrift_request.transport),
        ) as client:
            time_after_client = datetime.datetime.now()
            thrift_spec = self.service_specs[thrift_request.thrift_file]
            service_spec = thrift_spec[thrift_request.service_name]
            client_method = getattr(client, thrift_request.endpoint_name)
            possible_results = getattr(
                thriftpy_service, "{}_result".format(thrift_request.endpoint_name)
            )
            request_body = translate_request_body(
                service_spec.endpoints[thrift_request.endpoint_name],
                thrift_request.request_body,
                thriftpy_service,
            )
            possible_exceptions = find_request_exceptions(possible_results)
            time_before_request = datetime.datetime.now()
            try:
                response = client_method(**request_body)
                status = "success"
            except possible_exceptions as exception:
                status = exception.__class__.__name__
                response = exception
            time_after_request = datetime.datetime.now()
            response_body = translate_thrift_response(response)
            return ThriftResponse(
                status=status,
                request=thrift_request,
                data=response_body,
                elapsed=time_after_request - time_before_request,
                connection_elapsed=time_after_client - time_before_client,
            )
