import json
import os

from flask import Flask, request

from thrift_explorer.communication_models import ThriftRequest
from thrift_explorer.thrift_manager import ThriftManager

JSON_CONTENT_TYPE = {"Content-Type": "application/json; charset=utf-8"}
TEXT_CONTENT_TYPE = {"Content-Type": "text/plain; charset=utf-8"}


def create_app(test_config=None):
    app = Flask(__name__)
    if test_config is None:
        app.config["THRIFT_DIRECTORY"] = os.environ["THRIFT_DIRECTORY"]
        app.config["DEFAULT_PROTOCOL"] = os.environ.get(
            "DEFAULT_THRIFT_PROTOCOL", "TBinaryProtocol"
        )
        app.config["DEFAULT_TRANSPORT"] = os.environ.get(
            "DEFAULT_THRIFT_TRANSPORT", "TBufferedTransport"
        )
    else:
        app.config.from_mapping(test_config)

    thrift_manager = ThriftManager(app.config["THRIFT_DIRECTORY"])

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
        return (
            json.dumps({"thrifts": thrift_manager.list_thrift_services()}),
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
            json.dumps({"thrift": thrift, "service": service, "methods": methods}),
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
            # todo validate post body
            thrift_request = ThriftRequest(
                thrift_file=thrift,
                service_name=service,
                endpoint_name=method.name,
                host=request_json["host"],
                port=request_json["port"],
                protocol=request_json.get("protocol", app.config["DEFAULT_PROTOCOL"]),
                transport=request_json.get(
                    "transport", app.config["DEFAULT_TRANSPORT"]
                ),
                request_body=request_json["request_body"],
            )
            errors = thrift_manager.validate_request(thrift_request)
            print(errors)
            if errors:
                return (
                    json.dumps(
                        {"errors": [error.to_jsonable_dict() for error in errors]}
                    ),
                    400,
                )
            else:
                return (
                    json.dumps(
                        thrift_manager.make_request(thrift_request).to_jsonable_dict()
                    ),
                    200,
                    JSON_CONTENT_TYPE,
                )
        else:
            return (
                json.dumps(
                    ThriftRequest(
                        thrift_file=thrift,
                        service_name=service,
                        endpoint_name=method.name,
                        host="<hostname>",
                        port=9090,
                        protocol=app.config["DEFAULT_PROTOCOL"],
                        transport=app.config["DEFAULT_TRANSPORT"],
                        request_body={},
                    ).to_jsonable_dict()
                ),
                200,
                JSON_CONTENT_TYPE,
            )

    return app
