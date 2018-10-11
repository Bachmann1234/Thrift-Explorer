import datetime
import glob
import os
from collections import defaultdict

import thriftpy
from thriftpy import rpc as thriftpy_client
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
    thrift_paths = {}
    search_path = os.path.join(thrift_directory, "**/*thrift")
    for thrift_path in glob.iglob(search_path, recursive=True):
        thrift_filename = os.path.basename(thrift_path)
        thrifts[thrift_filename] = thriftpy.load(thrift_path)
        thrift_paths[thrift_filename] = thrift_path
    return thrifts, thrift_paths


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


def translate_request_body(endpoint, request_body, thriftpy_service_class):
    """
    Translate the request dictionary into whatever arguments
    are required to make the call with the thrift client

    This method assumes the request body had been validated and is correct

    endpoint: The endpoint spec as parsed by ThriftManager

    request_body: dictionary containing the args that should match
    the service. The values should have been validated before hitting
    this method

    thriftpy_service_class: the service class from thriftpy from module created 
     when thriftpy loaded the thrift file
    """
    processed_args = {}
    for arg_spec in endpoint.args:
        thrift_arg = getattr(
            thriftpy_service_class, "{}_args".format(endpoint.name)
        ).thrift_spec[arg_spec.field_id]
        try:
            ttype_code, name, required = thrift_arg
            type_info = None
        except ValueError:
            ttype_code, name, type_info, required = thrift_arg
        try:
            processed_args[arg_spec.name] = arg_spec.type_info.format_arg_for_thrift(
                request_body[arg_spec.name], type_info
            )
        except KeyError:
            # We assume validation happened earlier so if an arg
            # is missing we assume it is not required
            continue
    return processed_args


def translate_thrift_response(response):
    # I considered just using TJSONProtocol. But once it became clear
    # there was not a simple "just call this" method the result
    # started getting as complicated as this.
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
        time_to_make_request=datetime.datetime.now() - time_before_request,
        time_to_connect=time_after_client,
    )


class ThriftManager(object):
    """
    self.thrift_directory - str - path to the thrift files
    self.thrift_paths - list[str] - list of paths to thrift files
    self.service_spec -  dict[string][dict[string][ThriftService]]

    self.service_spec is keyed by thrift file name. The value is a dictionary 
    keyed by service name with its value being the ThriftService object 
    which has all the useful information you need

    I may need to have a good think about that last field.
    """

    def __init__(self, thrift_directory):
        self.thrift_directory = thrift_directory
        self._thrifts, self.thrift_paths = _load_thrifts(self.thrift_directory)
        self.service_specs = parse_service_specs(self._thrifts)

    def list_thrift_services(self):
        results = defaultdict(list)
        for key in self.service_specs.keys():
            for service in self.service_specs[key]:
                results[key].append(service)
        return results

    def get_thrift(self, thrift):
        return self.service_specs.get(thrift)

    def get_service(self, thrift_name, service_name):
        service = None
        thrift_spec = self.get_thrift(thrift_name)
        if thrift_spec:
            service = self.service_specs[thrift_name].get(service_name)
        return service

    def get_method(self, thrift_name, service_name, method_name):
        method = None
        service = self.get_service(thrift_name, service_name)
        if service:
            method = service.endpoints.get(method_name)
        return method

    def list_methods(self, thrift, service):
        loaded_thrift = self.service_specs[thrift]
        loaded_service = loaded_thrift[service]
        return [key for key in loaded_service.endpoints.keys()]

    def thrift_definition(self, thrift):
        with open(self.thrift_paths[thrift]) as infile:
            return infile.read()

    def _thrift_is_loaded(self, thrift_request):
        try:
            thrift_spec = self.service_specs[thrift_request.thrift_file]
            return None
        except KeyError:
            return [
                Error(
                    code=ErrorCode.THRIFT_NOT_LOADED,
                    message="Thrift File '{}' not loaded in ThriftManager".format(
                        thrift_request.thrift_file
                    ),
                )
            ]

    def _service_in_thrift(self, thrift_spec, service_name, thrift_file):
        try:
            service_spec = thrift_spec[service_name]
        except KeyError:
            return [
                Error(
                    code=ErrorCode.SERVICE_NOT_IN_THRIFT,
                    message="Service '{}' not in thrift '{}'".format(
                        service_name, thrift_file
                    ),
                )
            ]

    def _endpoint_in_service(
        self, service_spec, endpoint_name, service_name, thrift_file
    ):
        try:
            endpoint_spec = service_spec.endpoints[endpoint_name]
        except KeyError:
            return [
                Error(
                    code=ErrorCode.ENDPOINT_NOT_IN_SERVICE,
                    message="Endpoint '{}' not in service '{}' in thrift '{}'".format(
                        endpoint_name, service_name, thrift_file
                    ),
                )
            ]

    def _validate_request_body(
        self, thrift_file, service_name, endpoint_name, request_body
    ):
        validation_errors = []
        for arg_spec in (
            self.service_specs[thrift_file][service_name]
            .endpoints[endpoint_name]
            .args  # this kind of crap makes me think I need to rethink my structures
        ):
            try:
                error = arg_spec.type_info.validate_arg(request_body[arg_spec.name])
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

    def validate_request(self, thrift_request):
        return (
            self._thrift_is_loaded(thrift_request)
            or self._service_in_thrift(
                self.service_specs[thrift_request.thrift_file],
                thrift_request.service_name,
                thrift_request.thrift_file,
            )
            or self._endpoint_in_service(
                self.service_specs[thrift_request.thrift_file][
                    thrift_request.service_name
                ],
                thrift_request.endpoint_name,
                thrift_request.service_name,
                thrift_request.thrift_file,
            )
            or self._validate_request_body(
                thrift_request.thrift_file,
                thrift_request.service_name,
                thrift_request.endpoint_name,
                thrift_request.request_body,
            )
        )

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
            with thriftpy_client.client_context(
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
                time_to_make_request=None,
                time_to_connect=None,
            )
