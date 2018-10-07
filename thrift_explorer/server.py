import json
import os

import attr
from flask import Flask, request

from thrift_explorer.communication_models import (
    CommunicationModelEncoder,
    Error,
    ErrorCode,
    ThriftRequest,
)
from thrift_explorer.thrift_manager import ThriftManager

JSON_CONTENT_TYPE = {"Content-Type": "application/json; charset=utf-8"}
TEXT_CONTENT_TYPE = {"Content-Type": "text/plain; charset=utf-8"}

THRIFT_DIRECTORY_ENV = "THRIFT_DIRECTORY"
DEFAULT_PROTOCOL_ENV = "DEFAULT_THRIFT_PROTOCOL"
DEFAULT_TRANSPORT_ENV = "DEFAULT_THRIFT_TRANSPORT"


def create_app():
    app = Flask(__name__)
    app.config[THRIFT_DIRECTORY_ENV] = os.environ[THRIFT_DIRECTORY_ENV]
    app.config[DEFAULT_PROTOCOL_ENV] = os.environ.get(
        DEFAULT_PROTOCOL_ENV, "TBinaryProtocol"
    )
    app.config[DEFAULT_TRANSPORT_ENV] = os.environ.get(
        DEFAULT_TRANSPORT_ENV, "TBufferedTransport"
    )

    thrift_manager = ThriftManager(app.config[THRIFT_DIRECTORY_ENV])

    def _add_extension_if_needed(thrift):
        if not thrift.endswith(".thrift"):
            thrift = "{}.thrift".format(thrift)
        return thrift

    def _validate_args(thrift, service=None, method=None):
        if not thrift_manager.get_thrift(thrift):
            return "Thrift '{}' not found".format(thrift), 404
        if service and not thrift_manager.get_service(thrift, service):
            return "Service '{}' not found".format(service), 404
        if method and not thrift_manager.get_method(thrift, service, method):
            return "Method '{}' not found".format(method), 404
        return None

    @app.route("/", methods=["GET"])
    def list_services():
        result = []
        for thrift_file, services in thrift_manager.list_thrift_services().items():
            for service in services:
                result.append(
                    {
                        "thrift": thrift_file,
                        "service": service,
                        "methods": sorted(
                            thrift_manager.list_methods(thrift_file, service)
                        ),
                    }
                )
        return (
            json.dumps(
                {"thrifts": sorted(result, key=lambda service: service["thrift"])}
            ),
            200,
            JSON_CONTENT_TYPE,
        )

    @app.route("/<thrift>/", methods=["GET"])
    def get_thrift_definition(thrift):
        thrift = _add_extension_if_needed(thrift)
        error = _validate_args(thrift)
        if error:
            return error
        return thrift_manager.thrift_definition(thrift), 200, TEXT_CONTENT_TYPE

    @app.route("/<thrift>/<service>/", methods=["GET"])
    def get_service_info(thrift, service):
        thrift = _add_extension_if_needed(thrift)
        error = _validate_args(thrift, service)
        if error:
            return error
        methods = thrift_manager.list_methods(thrift, service)
        return (
            json.dumps(
                {"thrift": thrift, "service": service, "methods": sorted(methods)}
            ),
            200,
            JSON_CONTENT_TYPE,
        )

    @app.route("/<thrift>/<service>/<method>/", methods=["GET", "POST"])
    def service_method(thrift, service, method):
        thrift = _add_extension_if_needed(thrift)
        error = _validate_args(thrift, service, method)
        method = thrift_manager.get_method(thrift, service, method)
        if error:
            return error
        if request.method == "POST":
            request_json = request.get_json(force=True)
            errors = []
            try:
                thrift_request = ThriftRequest(
                    thrift_file=thrift,
                    service_name=service,
                    endpoint_name=method.name,
                    host=request_json.get("host"),
                    port=request_json.get("port"),
                    protocol=request_json.get(
                        "protocol", app.config[DEFAULT_PROTOCOL_ENV]
                    ),
                    transport=request_json.get(
                        "transport", app.config[DEFAULT_TRANSPORT_ENV]
                    ),
                    request_body=request_json.get("request_body"),
                )
                errors = thrift_manager.validate_request(thrift_request)
            except ValueError as e:
                errors = [Error(code=ErrorCode.INVALID_REQUEST, message=str(e))]
            except TypeError as e:
                errors = [Error(code=ErrorCode.INVALID_REQUEST, message=str(e.args[0]))]

            if errors:
                return (
                    json.dumps(
                        {
                            "errors": [
                                attr.asdict(error, recurse=True) for error in errors
                            ]
                        },
                        cls=CommunicationModelEncoder,
                    ),
                    400,
                )
            else:
                return (
                    json.dumps(
                        attr.asdict(
                            thrift_manager.make_request(thrift_request), recurse=True
                        ),
                        cls=CommunicationModelEncoder,
                    ),
                    200,
                    JSON_CONTENT_TYPE,
                )
        else:
            return (
                json.dumps(
                    attr.asdict(
                        ThriftRequest(
                            thrift_file=thrift,
                            service_name=service,
                            endpoint_name=method.name,
                            host="<hostname>",
                            port=9090,
                            protocol=app.config[DEFAULT_PROTOCOL_ENV],
                            transport=app.config[DEFAULT_TRANSPORT_ENV],
                            request_body={},
                        ),
                        recurse=True,
                    ),
                    cls=CommunicationModelEncoder,
                ),
                200,
                JSON_CONTENT_TYPE,
            )

    return app
