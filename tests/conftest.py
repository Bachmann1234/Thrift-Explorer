import os
from multiprocessing import Process
from time import sleep

import pytest
import thriftpy
from thriftpy.rpc import make_client

from thrift_explorer.thrift_manager import ThriftManager
from thrift_explorer.thrift_models import ServiceEndpoint
from todoserver.service import run_server


@pytest.fixture(scope="session")
def example_thrift_directory():
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "..", "example-thrifts"
    )


@pytest.fixture(scope="session")
def test_thrift_directory():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "test-thrifts")


@pytest.fixture(scope="session")
def todo_thrift():
    return thriftpy.load(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "..",
            "example-thrifts",
            "todo.thrift",
        )
    )


@pytest.fixture()
def todo_client(todo_thrift):
    client = make_client(todo_thrift.TodoService, "127.0.0.1", 6000)
    yield client
    client.close()


@pytest.fixture(scope="session")
def example_thrift_manager(example_thrift_directory):
    return ThriftManager(example_thrift_directory)


@pytest.fixture(scope="session")
def test_thrift_manager(test_thrift_directory):
    return ThriftManager(test_thrift_directory)


@pytest.fixture(scope="module")
def todo_server():
    server = Process(target=run_server, args=(6000,))
    server.start()
    sleep(.2)
    yield
    Process.terminate(server)


@pytest.fixture()
def batman_thrift_text():
    return """include "basethrifts/Core.thrift"

enum CrimeType {
    MURDER,
    ROBBERY,
    OTHER
}

struct Villain {
    1: required i32 villainId;
    2: required string name;
    3: required string description;
    5: optional Core.Location hideoutLocation;
}

struct Case {
    2: required string caseName;
    3: required CrimeType CrimeType;
    4: optional Villain mainSuspect;
    5: optional list<string> notes;
}

service BatPuter {
   void ping(),
   Villain getVillain(1: i32 villainId)
   Villain addVillain(
       1: string name, 
       2: string description, 
       3: Core.Location hideoutLocation
   )
   bool saveCase(1: Case caseToSave)
}"""


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
