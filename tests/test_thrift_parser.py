from testing_utils import load_thrift_from_testdir
from thrift_explorer import thrift_parser
from thrift_explorer.thrift_models import (
    TI16,
    TI32,
    TI64,
    ServiceEndpoint,
    TBool,
    TByte,
    TDouble,
    TEnum,
    ThriftSpec,
    TList,
    TMap,
    TSet,
    TString,
    TStruct,
)


def test_basic_thrift_types():
    simple_type_thrift = load_thrift_from_testdir("simpleType.thrift")
    expected = ServiceEndpoint(
        name="returnInt",
        args=[
            ThriftSpec(
                field_id=1, name="intParameter", type_info=TI32(), required=False
            ),
            ThriftSpec(
                field_id=2, name="stringParameter", type_info=TString(), required=False
            ),
        ],
        results=[
            ThriftSpec(field_id=0, name="success", type_info=TI32(), required=False)
        ],
    )
    assert expected == thrift_parser._parse_thrift_endpoint(
        simple_type_thrift.__thrift_meta__["services"][0], "returnInt"
    )


def test_set_list_types():
    collections_thrift = load_thrift_from_testdir("collections.thrift")
    expected = ServiceEndpoint(
        name="setsAndLists",
        args=[
            ThriftSpec(
                field_id=1,
                name="listOfDoubles",
                type_info=TList(value_type=TDouble()),
                required=False,
            ),
            ThriftSpec(
                field_id=2,
                name="binarySet",
                type_info=TSet(value_type=TString()),
                required=False,
            ),
        ],
        results=[
            ThriftSpec(
                field_id=0,
                name="success",
                type_info=TSet(value_type=TByte()),
                required=False,
            )
        ],
    )
    result = thrift_parser._parse_thrift_endpoint(
        collections_thrift.__thrift_meta__["services"][0], "setsAndLists"
    )
    assert expected == result


def test_map_type():
    collections_thrift = load_thrift_from_testdir("collections.thrift")
    expected = ServiceEndpoint(
        name="maps",
        args=[
            ThriftSpec(
                field_id=1,
                name="mapofI16toI64",
                type_info=TMap(key_type=TI16(), value_type=TI64()),
                required=False,
            )
        ],
        results=[
            ThriftSpec(
                field_id=0,
                name="success",
                type_info=TMap(key_type=TBool(), value_type=TByte()),
                required=False,
            )
        ],
    )
    result = thrift_parser._parse_thrift_endpoint(
        collections_thrift.__thrift_meta__["services"][0], "maps"
    )
    assert expected == result


def test_struct_type():
    struct_thrift = load_thrift_from_testdir("structThrift.thrift")
    my_int_struct = ThriftSpec(
        field_id=1, name="myIntStruct", type_info=TI64(), required=True
    )
    my_other_struct = ThriftSpec(
        field_id=2,
        name="myOtherStruct",
        type_info=TStruct(
            name="MyOtherStruct",
            fields=[
                ThriftSpec(field_id=1, name="id", type_info=TString(), required=True),
                ThriftSpec(
                    field_id=2,
                    name="ints",
                    type_info=TList(value_type=TI64()),
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
                field_id=0,
                name="success",
                type_info=TStruct(
                    name="MyStruct", fields=[my_int_struct, my_other_struct]
                ),
                required=False,
            )
        ],
    )
    result = thrift_parser._parse_thrift_endpoint(
        struct_thrift.__thrift_meta__["services"][0], "getMyStruct"
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
                field_id=0,
                name="success",
                type_info=TEnum(
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
    assert expected == thrift_parser._parse_thrift_endpoint(
        enum_thrift.__thrift_meta__["services"][0], "getHero"
    )


def test_super_nesting():
    turducken_thrift = load_thrift_from_testdir("turducken.thrift")
    dog_names_to_values = {"GOLDEN": 0, "CORGI": 1, "BASSET": 2}
    dog_enum = TEnum(
        name="DOG",
        names_to_values=dog_names_to_values,
        values_to_names={value: key for key, value in dog_names_to_values.items()},
    )

    outer_value = TI64()
    inner_value = TList(value_type=TString())
    inner_key = TSet(value_type=TList(value_type=dog_enum))
    outer_key = TMap(key_type=inner_key, value_type=inner_value)

    map_field = TMap(key_type=outer_key, value_type=outer_value)

    expected = ServiceEndpoint(
        name="getTheStruct",
        args=[],
        results=[
            ThriftSpec(
                field_id=0,
                name="success",
                type_info=TStruct(
                    name="TheStruct",
                    fields=[
                        ThriftSpec(
                            field_id=1,
                            name="myInsaneStruct",
                            type_info=map_field,
                            required=True,
                        )
                    ],
                ),
                required=False,
            )
        ],
    )

    assert expected == thrift_parser._parse_thrift_endpoint(
        turducken_thrift.__thrift_meta__["services"][0], "getTheStruct"
    )


def test_void_method():
    simple_type_thrift = load_thrift_from_testdir("simpleType.thrift")
    expected = ServiceEndpoint(name="voidMethod", args=[], results=[])
    assert expected == thrift_parser._parse_thrift_endpoint(
        simple_type_thrift.__thrift_meta__["services"][0], "voidMethod"
    )


def test_exception():
    exceptional_thrift = load_thrift_from_testdir("exceptional.thrift")
    expected = ServiceEndpoint(
        name="ping",
        args=[],
        results=[
            ThriftSpec(
                field_id=1,
                name="omg",
                type_info=TStruct(
                    name="OMGException",
                    fields=[
                        ThriftSpec(
                            field_id=1,
                            name="description",
                            type_info=TString(),
                            required=True,
                        )
                    ],
                ),
                required=False,
            )
        ],
    )
    assert expected == thrift_parser._parse_thrift_endpoint(
        exceptional_thrift.__thrift_meta__["services"][0], "ping"
    )
