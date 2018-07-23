import pytest

from thrift_explorer.thrift_models import TI16, TI32, TI64, TDouble, TString


def test_base_type_translate_int():
    assert 4 == TI64().format_arg_for_thrift(4, None)


def test_base_type_translate_float():
    assert float(1) == TDouble().format_arg_for_thrift(1.0, None)


def test_translate_string():
    assert "Dog" == TString().format_arg_for_thrift("Dog", None)
