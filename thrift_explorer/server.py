import json
import os

from flask import Flask, request

from thrift_explorer.thrift_manager import ThriftManager


def create_app(test_config=None):
    app = Flask(__name__)
    if test_config is None:
        app.config["THRIFT_DIRECTORY"] = os.environ["THRIFT_DIRECTORY"]
    else:
        app.config.from_mapping(test_config)

    thrift_manager = ThriftManager(app.config["THRIFT_DIRECTORY"])

    @app.route("/", methods=["GET"])
    def list_services():
        return json.dumps({"thrifts": thrift_manager.list_thrift_services()})

    @app.route("/<thrift>/<service>", methods=["GET"])
    def get_service_info():
        return "Here is some service info"

    @app.route("/<thrift>/<service>/<method>", methods=["GET", "POST"])
    def service_method(thrift, service, method):
        if request.method == "POST":
            return "I ran a service command"
        else:
            return "Here is an empty body"

    return app
