import os
from thrift_explorer import thrift_manager
from thrift_explorer.thrift_models import (
    BaseType,
    ServiceEndpoint,
    CollectionType,
    MapType,
    ThriftSpec,
    ThriftService,
    StructType,
    EnumType,
)
from thrift_explorer.thrift_manager import ThriftManager
from testing_utils import load_thrift_from_testdir


def test_basic_thrift_types():
    simple_type_thrift = load_thrift_from_testdir("simpleType.thrift")
    expected = ServiceEndpoint(
        name="returnInt",
        args=[
            ThriftSpec(name="intParameter", type_info=BaseType("I32"), required=False),
            ThriftSpec(
                name="stringParameter", type_info=BaseType("STRING"), required=False
            ),
        ],
        results=[ThriftSpec(name="success", type_info=BaseType("I32"), required=False)],
    )
    assert expected == thrift_manager.parse_thrift_endpoint(
        "simpleType.thrift",
        simple_type_thrift.__thrift_meta__["services"][0],
        "returnInt",
    )


def test_set_list_types():
    collections_thrift = load_thrift_from_testdir("collections.thrift")
    expected = ServiceEndpoint(
        name="setsAndLists",
        args=[
            ThriftSpec(
                name="listOfDoubles",
                type_info=CollectionType(ttype="LIST", value_type=BaseType("DOUBLE")),
                required=False,
            ),
            ThriftSpec(
                name="binarySet",
                type_info=CollectionType(ttype="SET", value_type=BaseType("STRING")),
                required=False,
            ),
        ],
        results=[
            ThriftSpec(
                name="success",
                type_info=CollectionType(ttype="SET", value_type=BaseType("BYTE")),
                required=False,
            )
        ],
    )
    result = thrift_manager.parse_thrift_endpoint(
        "collections.thrift",
        collections_thrift.__thrift_meta__["services"][0],
        "setsAndLists",
    )
    assert expected == result


def test_map_type():
    collections_thrift = load_thrift_from_testdir("collections.thrift")
    expected = ServiceEndpoint(
        name="maps",
        args=[
            ThriftSpec(
                name="mapofI16toI64",
                type_info=MapType(
                    ttype="MAP", key_type=BaseType("I16"), value_type=BaseType("I64")
                ),
                required=False,
            )
        ],
        results=[
            ThriftSpec(
                name="success",
                type_info=MapType(
                    ttype="MAP", key_type=BaseType("BOOL"), value_type=BaseType("BYTE")
                ),
                required=False,
            )
        ],
    )
    result = thrift_manager.parse_thrift_endpoint(
        "collections.thrift", collections_thrift.__thrift_meta__["services"][0], "maps"
    )
    assert expected == result


def test_struct_type():
    struct_thrift = load_thrift_from_testdir("structThrift.thrift")
    my_int_struct = ThriftSpec(
        name="myIntStruct", type_info=BaseType("I64"), required=True
    )
    my_other_struct = ThriftSpec(
        name="myOtherStruct",
        type_info=StructType(
            ttype="STRUCT",
            name="MyOtherStruct",
            fields=[
                ThriftSpec(name="id", type_info=BaseType("STRING"), required=True),
                ThriftSpec(
                    name="ints",
                    type_info=CollectionType(ttype="LIST", value_type=BaseType("I64")),
                    required=True,
                ),
            ],
        ),
        required=False,
    )
    expected = ServiceEndpoint(
        name="getMyStruct",
        args=[],
        results=[
            ThriftSpec(
                name="success",
                type_info=StructType(
                    ttype="STRUCT",
                    name="MyStruct",
                    fields=[my_int_struct, my_other_struct],
                ),
                required=False,
            )
        ],
    )
    result = thrift_manager.parse_thrift_endpoint(
        "structThrift.thrift",
        struct_thrift.__thrift_meta__["services"][0],
        "getMyStruct",
    )
    assert expected == result


def test_enum():
    enum_thrift = load_thrift_from_testdir("enum.thrift")
    superhero_names_to_values = {
        "BATMAN": 0,
        "SUPERMAN": 2,
        "SPIDERMAN": 10,
        "WONDERWOMAN": 11,
    }
    expected = ServiceEndpoint(
        name="getHero",
        args=[],
        results=[
            ThriftSpec(
                name="success",
                type_info=EnumType(
                    ttype="I32",
                    name="Superhero",
                    names_to_values=superhero_names_to_values,
                    values_to_names={
                        value: key for key, value in superhero_names_to_values.items()
                    },
                ),
                required=False,
            )
        ],
    )
    assert expected == thrift_manager.parse_thrift_endpoint(
        "enum.thrift", enum_thrift.__thrift_meta__["services"][0], "getHero"
    )


def test_super_nesting():
    turducken_thrift = load_thrift_from_testdir("turducken.thrift")
    dog_names_to_values = {"GOLDEN": 0, "CORGI": 1, "BASSET": 2}
    dog_enum = EnumType(
        ttype="I32",
        name="DOG",
        names_to_values=dog_names_to_values,
        values_to_names={value: key for key, value in dog_names_to_values.items()},
    )

    outer_value = BaseType("I64")
    inner_value = CollectionType(ttype="LIST", value_type=BaseType("STRING"))
    inner_key = CollectionType(
        ttype="SET", value_type=CollectionType(ttype="LIST", value_type=dog_enum)
    )
    outer_key = MapType(ttype="MAP", key_type=inner_key, value_type=inner_value)

    map_field = MapType(ttype="MAP", key_type=outer_key, value_type=outer_value)

    expected = ServiceEndpoint(
        name="getTheStruct",
        args=[],
        results=[
            ThriftSpec(
                name="success",
                type_info=StructType(
                    ttype="STRUCT",
                    name="TheStruct",
                    fields=[
                        ThriftSpec(
                            name="myInsaneStruct", type_info=map_field, required=True
                        )
                    ],
                ),
                required=False,
            )
        ],
    )

    assert expected == thrift_manager.parse_thrift_endpoint(
        "turducken.thrift",
        turducken_thrift.__thrift_meta__["services"][0],
        "getTheStruct",
    )


def test_void_method():
    simple_type_thrift = load_thrift_from_testdir("simpleType.thrift")
    expected = ServiceEndpoint(name="voidMethod", args=[], results=[])
    assert expected == thrift_manager.parse_thrift_endpoint(
        "simpleType.thrift",
        simple_type_thrift.__thrift_meta__["services"][0],
        "voidMethod",
    )


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
