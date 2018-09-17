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

    @app.route("/", methods=["GET"])
    def list_services():
        return json.dumps({"thrifts": thrift_manager.list_thrift_services()})

    @app.route("/<thrift>/<service>", methods=["GET"])
    def get_service_info(thrift, service):
        if not thrift.endswith(".thrift"):
            thrift = "{}.thrift".format(thrift)
        try:
            methods = thrift_manager.list_methods(thrift, service)
        except KeyError as e:
            return e.args[0], 404
        return json.dumps({"thrift": thrift, "service": service, "methods": methods})

    @app.route("/<thrift>/<service>/<method>", methods=["GET", "POST"])
    def service_method(thrift, service, method):
        if request.method == "POST":
            return "I ran a service command"
        else:
            return "Here is an empty body"

    return app
