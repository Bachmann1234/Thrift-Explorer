import pytest

from thrift_explorer.thrift_models import (
    TI16,
    TI32,
    TI64,
    TBinary,
    TBool,
    TByte,
    TDouble,
    TEnum,
    TList,
    TMap,
    TSet,
    TString,
)


@pytest.fixture
def animal_enum():
    names_to_values = {"bird": 1, "dog": 2, "cat": 3, "elephant": 4}
    return TEnum(
        name="Animals",
        names_to_values=names_to_values,
        values_to_names={value: key for key, value in names_to_values.items()},
    )


def test_base_type_translate_int():
    assert 4 == TI64().format_arg_for_thrift(4, None)


def test_base_type_translate_float():
    assert float(1) == TDouble().format_arg_for_thrift(1.0, None)


def test_translate_string():
    assert "Dog" == TString().format_arg_for_thrift("Dog", None)


def test_valid_string():
    assert TString().validate_arg("Batman") is None


def test_invalid_string():
    assert TString().validate_arg(b"Batman") == "Expected str but got bytes"
    assert TString().validate_arg(4) == "Expected str but got int"


def test_valid_binary():
    assert TBinary().validate_arg(b"Batman") is None


def test_invalid_binary():
    assert TBinary().validate_arg("Batman") == "Expected bytes but got str"
    assert TBinary().validate_arg(4) == "Expected bytes but got int"


def test_valid_double():
    assert TDouble().validate_arg(4) is None
    assert TDouble().validate_arg(4.0) is None


def test_invalid_double():
    assert TDouble().validate_arg("4.0") == "Expected float but got str"


def test_valid_ti64():
    assert TI64().validate_arg(9223372036854775807) is None
    assert TI64().validate_arg(-9223372036854775808) is None


def test_invalid_ti64():
    assert (
        TI64().validate_arg(9223372036854775808)
        == "Value is too large to be a 64 bit integer"
    )
    assert (
        TI64().validate_arg(-9223372036854775809)
        == "Value is too small to be a 64 bit integer"
    )


def test_valid_ti32():
    assert TI32().validate_arg(2147483647) is None
    assert TI32().validate_arg(-2147483648) is None


def test_invalid_ti32():
    assert (
        TI32().validate_arg(2147483648) == "Value is too large to be a 32 bit integer"
    )
    assert (
        TI32().validate_arg(-2147483649) == "Value is too small to be a 32 bit integer"
    )


def test_valid_ti16():
    assert TI16().validate_arg(32767) is None
    assert TI16().validate_arg(-32768) is None


def test_invalid_ti16():
    assert TI16().validate_arg(32768) == "Value is too large to be a 16 bit integer"
    assert TI16().validate_arg(-32769) == "Value is too small to be a 16 bit integer"


def test_valid_tbyte():
    assert TByte().validate_arg(127) is None
    assert TByte().validate_arg(-128) is None


def test_invalid_tbyte():
    assert TByte().validate_arg(128) == "Value is too large to be a byte"
    assert TByte().validate_arg(-129) == "Value is too small to be a byte"


def test_valid_tbool():
    assert TBool().validate_arg(True) is None
    assert TBool().validate_arg(False) is None


def test_invalid_tbool():
    assert TBool().validate_arg("true") == "Expected bool but got str"
    assert TBool().validate_arg(8) == "Expected bool but got int"


def test_valid_t_enum(animal_enum):
    assert animal_enum.validate_arg("bird") is None
    assert animal_enum.validate_arg(1) is None


def test_invalid_enum(animal_enum):
    assert animal_enum.validate_arg("bat") == "Value is not in enum 'Animals'"
    assert animal_enum.validate_arg(8) == "Value is not in enum 'Animals'"


def test_valid_map():
    tmap = TMap(key_type=TI32(), value_type=TString())
    assert tmap.validate_arg({}) is None
    assert tmap.validate_arg({3: "dog", 4: "cat"}) is None
    nested_tmap = TMap(
        key_type=TI32(), value_type=TMap(key_type=TString(), value_type=TI32())
    )
    assert nested_tmap.validate_arg({3: {"test": 4}, 1: {"map": 3231}}) is None


def test_invalid_map():
    tmap = TMap(key_type=TI32(), value_type=TString())
    assert tmap.validate_arg({3: 4, 5: 2}) == [
        "Value for key '3' in map invalid: 'Expected str but got int'",
        "Value for key '5' in map invalid: 'Expected str but got int'",
    ]
    assert tmap.validate_arg({"3": 4, 5: "2"}) == [
        "Key '3' in map invalid: 'Expected int but got str'",
        "Value for key '3' in map invalid: 'Expected str but got int'",
    ]


def test_valid_list():
    assert TList(value_type=TString()).validate_arg(["1", "2", "3"]) is None
    assert TList(value_type=TString()).validate_arg([]) is None
    assert (
        TList(value_type=TList(value_type=TI32())).validate_arg([[1, 2], [4, 4]])
        is None
    )


def test_invalid_list():
    assert TList(value_type=TString()).validate_arg(set()) == [
        "Expected list but got set"
    ]
    assert TList(value_type=TString()).validate_arg([4]) == [
        "Index 0: Expected str but got int"
    ]


def test_valid_set():
    assert TSet(value_type=TString()).validate_arg({"1", "2", "3"}) is None
    assert TSet(value_type=TString()).validate_arg(set()) is None


def test_invalid_set():
    assert TSet(value_type=TString()).validate_arg([]) == ["Expected set but got list"]
    assert TSet(value_type=TString()).validate_arg({4}) == [
        "Invalid value in set: Expected str but got int"
    ]
