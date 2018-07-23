import pytest

from thrift_explorer.thrift_models import TI16, TI32, TI64, TBinary, TDouble, TString


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
