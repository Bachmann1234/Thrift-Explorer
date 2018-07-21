import pytest

from thrift_explorer.thrift_models import BaseType


def test_base_type_translate_int():
    assert 4 == BaseType("I16").format_arg_for_thrift("4", None)
    assert 4 == BaseType("I32").format_arg_for_thrift("4", None)
    assert 4 == BaseType("I64").format_arg_for_thrift("4", None)
    assert 4 == BaseType("I64").format_arg_for_thrift(4, None)


def test_base_type_translate_float():
    assert float(1) == BaseType("DOUBLE").format_arg_for_thrift(1, None)
    assert float(1) == BaseType("DOUBLE").format_arg_for_thrift("1", None)


def test_translate_string():
    assert "Dog" == BaseType("STRING").format_arg_for_thrift("Dog", None)
