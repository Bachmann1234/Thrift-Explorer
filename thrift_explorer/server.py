import json
import os

from flask import Flask, request

from thrift_explorer.thrift_manager import ThriftManager


def create_app(test_config=None):
    app = Flask(__name__)
    if test_config is None:
        app.config["THRIFT_DIRECTORY"] = os.environ["THRIFT_DIRECTORY"]
        app.config["DEFAULT_TRANSPORT"] = os.environ["THRIFT_DIRECTORY"]
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
        if not thrift_manager.thrift_loaded(thrift):
            return "Thrift '{}' not found".format(thrift), 404
        if service and not thrift_manager.service_in_thrift(thrift, service):
            return "Service '{}' not found".format(service), 404
        if method and not thrift_manager.method_in_service(thrift, service, method):
            return "Method '{}' not found".format(method), 404
        return None

    @app.route("/", methods=["GET"])
    def list_services():
        return json.dumps({"thrifts": thrift_manager.list_thrift_services()})

    @app.route("/<thrift>", methods=["GET"])
    def get_thrift_definition(thrift):
        thrift = _add_extension_if_needed(thrift)
        error = _validate_args(thrift)
        if error:
            return error
        return thrift_manager.thrift_definition(thrift)

    @app.route("/<thrift>/<service>", methods=["GET"])
    def get_service_info(thrift, service):
        thrift = _add_extension_if_needed(thrift)
        error = _validate_args(thrift, service)
        if error:
            return error
        methods = thrift_manager.list_methods(thrift, service)
        return json.dumps({"thrift": thrift, "service": service, "methods": methods})

    @app.route("/<thrift>/<service>/<method>", methods=["GET", "POST"])
    def service_method(thrift, service, method):
        thrift = _add_extension_if_needed(thrift)
        error = _validate_args(thrift, service, method)
        if error:
            return error
        if request.method == "POST":
            return "I ran a service command"
        else:
            return "Here is an empty body"

    return app
