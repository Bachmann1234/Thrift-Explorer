import datetime
import glob
import os
from collections import defaultdict

import thriftpy
from thriftpy.protocol import (
    TBinaryProtocolFactory,
    TCompactProtocolFactory,
    TJSONProtocolFactory,
)
from thriftpy.thrift import TException

from thrift_explorer.communication_models import (
    Error,
    ErrorCode,
    FieldError,
    Protocol,
    ThriftResponse,
    Transport,
)
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
    # Consider just dumping into json with the TJSONProtocol
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


def find_request_exceptions(thriftpy_service, thrift_request):
    possible_results = getattr(
        thriftpy_service, "{}_result".format(thrift_request.endpoint_name)
    )
    exceptions = []
    for result in possible_results.thrift_spec.values():
        _, _, clazz, _ = result
        if issubclass(clazz, BaseException):
            exceptions.append(clazz)
    return tuple(exceptions)


def _make_client_call(
    client, time_after_client, thrift_request, thriftpy_service, endpoint_spec
):
    translated_request_body = translate_request_body(
        endpoint_spec, thrift_request.request_body, thriftpy_service
    )
    time_before_request = datetime.datetime.now()
    try:
        response = getattr(client, thrift_request.endpoint_name)(
            **translated_request_body
        )
        status = "Success"
    except find_request_exceptions(thriftpy_service, thrift_request) as exception:
        status = exception.__class__.__name__
        response = exception
    except TException as exception:
        status = "ServerError"
        response = "Failed to make call: {}".format(getattr(exception, "message"))
    response_body = translate_thrift_response(response)
    return ThriftResponse(
        status=status,
        request=thrift_request,
        data=response_body,
        time_to_make_reqeust=datetime.datetime.now() - time_before_request,
        time_to_connect=time_after_client,
    )


class ThriftManager(object):
    def __init__(self, thrift_directory):
        self.thrift_directory = thrift_directory
        self._thrifts = _load_thrifts(self.thrift_directory)
        self.service_specs = parse_service_specs(self._thrifts)

    def list_thrift_services(self):
        results = defaultdict(list)
        for key in self.service_specs.keys():
            for service in self.service_specs[key]:
                results[key].append(service)
        return results

    def validate_request(self, thrift_request):
        try:
            thrift_spec = self.service_specs[thrift_request.thrift_file]
        except KeyError:
            return [
                Error(
                    code=ErrorCode.THRIFT_NOT_LOADED,
                    message="Thrift File '{}' not loaded in ThriftManager".format(
                        thrift_request.thrift_file
                    ),
                )
            ]
        try:
            service_spec = thrift_spec[thrift_request.service_name]
        except KeyError:
            return [
                Error(
                    code=ErrorCode.SERVICE_NOT_IN_THRIFT,
                    message="Service '{}' not in thrift '{}'".format(
                        thrift_request.service_name, thrift_request.thrift_file
                    ),
                )
            ]
        try:
            endpoint_spec = service_spec.endpoints[thrift_request.endpoint_name]
        except KeyError:
            return [
                Error(
                    code=ErrorCode.ENDPOINT_NOT_IN_SERVICE,
                    message="Endpoint '{}' not in service '{}' in thrift '{}'".format(
                        thrift_request.endpoint_name,
                        thrift_request.service_name,
                        thrift_request.thrift_file,
                    ),
                )
            ]

        validation_errors = []
        for arg_spec in endpoint_spec.args:
            try:
                error = arg_spec.type_info.validate_arg(
                    thrift_request.request_body[arg_spec.name]
                )
                if error:
                    validation_errors.append(
                        FieldError(
                            arg_spec=arg_spec,
                            code=ErrorCode.FIELD_VALIDATION_ERROR,
                            message=error,
                        )
                    )
            except KeyError:
                if arg_spec.required:
                    validation_errors.append(
                        FieldError(
                            arg_spec=arg_spec,
                            code=ErrorCode.REQUIRED_FIELD_MISSING,
                            message="Required Field '{}' not found".format(
                                arg_spec.name
                            ),
                        )
                    )
        return validation_errors

    def make_request(self, thrift_request):
        thriftpy_service = getattr(
            self._thrifts[thrift_request.thrift_file], thrift_request.service_name
        )
        thrift_spec = self.service_specs[thrift_request.thrift_file]
        endpoint_spec = thrift_spec[thrift_request.service_name].endpoints[
            thrift_request.endpoint_name
        ]
        time_before_client = datetime.datetime.now()
        try:
            with thriftpy.rpc.client_context(
                service=thriftpy_service,
                host=thrift_request.host,
                port=thrift_request.port,
                proto_factory=_find_protocol_factory(thrift_request.protocol),
                trans_factory=_find_transport_factory(thrift_request.transport),
            ) as client:
                time_after_client = datetime.datetime.now() - time_before_client
                return _make_client_call(
                    client,
                    time_after_client,
                    thrift_request,
                    thriftpy_service,
                    endpoint_spec,
                )
        except TException as exception:
            status = "ConnectionError"
            response = "Failed to make client connection: {}".format(
                getattr(exception, "message")
            )
            return ThriftResponse(
                status=status,
                request=thrift_request,
                data=response,
                time_to_make_reqeust=None,
                time_to_connect=None,
            )
