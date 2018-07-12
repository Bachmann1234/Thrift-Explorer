import os
from thrift_explorer import thrift_manager
from thrift_explorer.thrift_models import (
    BaseType,
    ServiceEndpoint,
    ThriftSpec,
    ThriftService,
)
from thrift_explorer.thrift_manager import ThriftManager
from testing_utils import load_thrift_from_testdir


def test_basic_thrift_types():
    simple_type_thrift = load_thrift_from_testdir("simpleType.thrift")
    expected = ServiceEndpoint(
        name="returnInt",
        args=[
            ThriftSpec(
                name="intParameter",
                type_info=BaseType("I32"),
                required=False,
            ),
            ThriftSpec(
                name="stringParameter",
                type_info=BaseType("STRING"),
                required=False,
            ),
        ],
        results=[
            ThriftSpec(
                name="success", type_info=BaseType("I32"), required=False
            )
        ],
    )
    assert expected == thrift_manager.parse_thrift_endpoint(
        "simpleType.thrift",
        simple_type_thrift.__thrift_meta__["services"][0],
        "returnInt",
    )


def test_set_list_types():
    collections_thrift = load_thrift_from_testdir("collections.thrift")
    expected = None
    result = thrift_manager.parse_thrift_endpoint(
        "setList.thrift",
        collections_thrift.__thrift_meta__["services"][0],
        "setsAndLists",
    )
    assert expected == result


def test_list_modules(example_thrift_directory):
    manager = ThriftManager(example_thrift_directory)
    expected = [
        ThriftService(
            "Batman.thrift",
            "BatPuter",
            ["ping", "getVillain", "addVillain", "saveCase"],
        ),
        ThriftService(
            "todo.thrift",
            "TodoService",
            ["listTasks", "getTask", "createTask", "completeTask"],
        ),
    ]
    actual = manager.services
    assert expected == actual
