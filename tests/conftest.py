import os
from time import sleep
from multiprocessing import Process
import pytest
from todoserver.service import run_server
from thrift_explorer.thrift_models import ServiceEndpoint


@pytest.fixture()
def example_thrift_directory():
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "..", "example-thrifts"
    )


@pytest.fixture(scope="module")
def todo_server():
    server = Process(target=run_server, args=(6000,))
    server.start()
    sleep(.2)
    yield
    Process.terminate(server)


def pytest_assertrepr_compare(op, left, right):
    output = []
    if (
        isinstance(left, ServiceEndpoint)
        and isinstance(right, ServiceEndpoint)
        and op == "=="
    ):
        if left.name != right.name:
            output.append(_format_for_output("name", left.name, right.name))
        if left.args != right.args:
            output += _compare_list_thrift_spec("args", right.args, left.args)
        if left.results != right.results:
            output += _compare_list_thrift_spec("results", right.results, left.results)
        return output


def _compare_list_thrift_spec(name, right, left):
    output = []
    if len(right) != len(left):
        output.append("Left And Right {} Have different lengths".format(name))
    else:
        for count, args in enumerate(zip(left, right)):
            left_args, right_args = args
            output += _compare_thrift_spec(
                "{}[{}]".format(name, count), left_args, right_args
            )
    return output


def _format_for_output(field, left, right):
    return "{}: {} != {}".format(field, left, right)


def _compare_thrift_spec(field, left, right):
    output = []
    field_format = "{}.{}"
    if left.name != right.name:
        output.append(
            _format_for_output(
                field_format.format(field, "name"), left.name, right.name
            )
        )
    if left.type_info != right.type_info:
        output.append(
            _format_for_output(
                field_format.format(field, "type_info"), left.type_info, right.type_info
            )
        )
    if left.required != right.required:
        output.append(
            _format_for_output(
                field_format.format(field, "required"), left.required, right.required
            )
        )
    return output
