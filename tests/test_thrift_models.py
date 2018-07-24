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
    assert TString().validate_arg(b"Batman") == "Provided argument is not a string"
    assert TString().validate_arg(4) == "Provided argument is not a string"


def test_valid_binary():
    assert TBinary().validate_arg(b"Batman") is None


def test_invalid_binary():
    assert TBinary().validate_arg("Batman") == "Provided argument is not binary data"
    assert TBinary().validate_arg(4) == "Provided argument is not binary data"


def test_valid_double():
    assert TDouble().validate_arg(4.0) is None


def test_invalid_double():
    assert TDouble().validate_arg(4) == "Provided argument is not a float"
    assert TDouble().validate_arg("4.0") == "Provided argument is not a float"


def test_valid_ti64():
    assert TI64().validate_arg(9223372036854775807) is None
    assert TI64().validate_arg(-9223372036854775808) is None


def test_invalid_ti64():
    assert (
        TI64().validate_arg(9223372036854775808)
        == "9223372036854775808 is too large to be a 64 bit integer"
    )
    assert (
        TI64().validate_arg(-9223372036854775809)
        == "-9223372036854775809 is too small to be a 64 bit integer"
    )


def test_valid_ti32():
    assert TI32().validate_arg(2147483647) is None
    assert TI32().validate_arg(-2147483648) is None


def test_invalid_ti32():
    assert (
        TI32().validate_arg(2147483648)
        == "2147483648 is too large to be a 32 bit integer"
    )
    assert (
        TI32().validate_arg(-2147483649)
        == "-2147483649 is too small to be a 32 bit integer"
    )


def test_valid_ti16():
    assert TI16().validate_arg(32767) is None
    assert TI16().validate_arg(-32768) is None


def test_invalid_ti16():
    assert TI16().validate_arg(32768) == "32768 is too large to be a 16 bit integer"
    assert TI16().validate_arg(-32769) == "-32769 is too small to be a 16 bit integer"


def test_valid_tbyte():
    assert TByte().validate_arg(127) is None
    assert TByte().validate_arg(-128) is None


def test_invalid_tbyte():
    assert TByte().validate_arg(128) == "128 is too large to be a byte"
    assert TByte().validate_arg(-129) == "-129 is too small to be a byte"


def test_valid_tbool():
    assert TBool().validate_arg(True) is None
    assert TBool().validate_arg(False) is None


def test_invalid_tbool():
    assert TBool().validate_arg("true") == "Provided argument is not a boolean"
    assert TBool().validate_arg(8) == "Provided argument is not a boolean"


def test_valid_t_enum(animal_enum):
    assert animal_enum.validate_arg("bird") is None
    assert animal_enum.validate_arg(1) is None


def test_invalid_enum(animal_enum):
    assert (
        animal_enum.validate_arg("bat")
        == "Provided value 'bat' is not in enum 'Animals'"
    )
    assert animal_enum.validate_arg(8) == "Provided value '8' is not in enum 'Animals'"
