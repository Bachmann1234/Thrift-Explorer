import sys
from abc import ABC, abstractmethod

import attr


def _validate_basic_type(expected_type, raw_value):
    if isinstance(raw_value, expected_type):
        return None
    return "Expected {0} but got {1}".format(
        expected_type.__name__, type(raw_value).__name__
    )


class ThriftType(ABC):
    def format_arg_for_thrift(self, raw_arg, thrift_module):
        return raw_arg

    @abstractmethod
    def validate_arg(self, raw_arg):
        raise NotImplementedError


@attr.s(frozen=True)
class ThriftService(object):
    """
    Container for a thrift service
    thrift_file: str
        Name of the thrift file this service came from
    name: str
        Name of the service
    endpoints: list[ServiceEndpoint]
        What endpoints can be called on this service
    """

    thrift_file = attr.ib()
    name = attr.ib()
    endpoints = attr.ib()


@attr.s(frozen=True)
class ServiceEndpoint(object):
    """
    Container representing a specific thrift service endpoint
    name: str
        Name of the endpoint
    args: list[ThriftSpec]
        Arguments this service takes in
    results: list[ThriftSpec]
        The result of the method. Its a list because a thrift endpoint
        can have a return value (labeled success) and possibly an exception
        (labeled by the exception name)
    """

    name = attr.ib()
    args = attr.ib()
    results = attr.ib()


@attr.s(frozen=True)
class ThriftSpec(object):
    """
    Container for the specification of an argument
    or a result.
    name: field_id 
        the id of the spec field
    name: str
        Name of the argument/result
    type_info: ThriftType
        If the spec is not a base thrift type this will contain
        info required to specify the complex type
    required: bool
        True if the spec is required in a request/response
        False otherwise
    """

    field_id = attr.ib()
    name = attr.ib()
    type_info = attr.ib()
    required = attr.ib()


@attr.s(frozen=True)
class TStruct(ThriftType):
    """
    Spec for a particular Struct
    name: str
        Name of the struct
    fields: list[ThriftSpec]
        Each property of the struct is its own spec
    ttype: str
        Ttype of the object (always 'struct')
    """

    name = attr.ib()
    fields = attr.ib()
    ttype = attr.ib(default="struct")

    def format_arg_for_thrift(self, raw_arg, clazz):
        class_args = {}
        for field in self.fields:
            thrift_arg = clazz.thrift_spec[field.field_id]
            try:
                ttype_code, name, required = thrift_arg
                type_info = None
            except ValueError:
                ttype_code, name, type_info, required = thrift_arg
            try:
                class_args[field.name] = field.type_info.format_arg_for_thrift(
                    raw_arg[field.name], type_info
                )
            except KeyError:
                continue  # we assume this is already validated. So the arg must be optional
        return clazz(**class_args)

    def validate_arg(self, raw_arg):
        if not isinstance(raw_arg, dict):
            return [
                "Structs expect a dictionary but got {0}".format(type(raw_arg).__name__)
            ]
        errors = []
        for field in self.fields:
            try:
                value = raw_arg[field.name]
                field_validation = field.type_info.validate_arg(value)
                if field_validation:
                    errors.append(
                        "Error with field '{}': '{}'".format(
                            field.name, field_validation
                        )
                    )
            except KeyError:
                if field.required:
                    errors.append("Required field '{}' missing".format(field.name))
        return errors if errors else None


def _validate_collection(collection_class, raw_arg, value_type):
    errors = _validate_basic_type(collection_class, raw_arg)
    if errors:
        return [errors]
    errors = []
    for index, value in enumerate(raw_arg):
        error = value_type.validate_arg(value)
        if error:
            if collection_class == set:
                errors.append("Invalid value in set: {0}".format(error))
            else:
                errors.append("Index {0}: {1}".format(index, error))
    return errors if errors else None


@attr.s(frozen=True)
class TList(ThriftType):
    """
    Spec for a list or a set type
    value_type: ThriftType
        Specification for the type the collection contains
    """

    value_type = attr.ib()
    ttype = attr.ib(default="list")

    def format_arg_for_thrift(self, raw_arg, thrift_module):
        return [
            self.value_type.format_arg_for_thrift(arg, thrift_module) for arg in raw_arg
        ]

    def validate_arg(self, raw_arg):
        return _validate_collection(list, raw_arg, self.value_type)


@attr.s(frozen=True)
class TSet(ThriftType):
    """
    Spec for a list or a set type
    value_type: ThriftType
        Specification for the type the collection contains
    """

    value_type = attr.ib()
    ttype = attr.ib(default="set")

    def format_arg_for_thrift(self, raw_arg, thrift_module):
        return {
            self.value_type.format_arg_for_thrift(arg, thrift_module) for arg in raw_arg
        }

    def validate_arg(self, raw_arg):
        return _validate_collection(set, raw_arg, self.value_type)


@attr.s(frozen=True)
class TMap(ThriftType):
    """
    Spec for a map type
    key_type: ThriftType
        Specification for the type of the key of the map
    value_type: ThriftType
        Specification for the type of the value of the map
    ttype:
        the type (always 'map')
    """

    key_type = attr.ib()
    value_type = attr.ib()
    ttype = attr.ib(default="map")

    def format_arg_for_thrift(self, raw_arg, thrift_module):
        return {
            self.key_type.format_arg_for_thrift(
                key, thrift_module
            ): self.value_type.format_arg_for_thrift(value, thrift_module)
            for key, value in raw_arg.items()
        }

    def validate_arg(self, raw_arg):
        errors = _validate_basic_type(dict, raw_arg)
        if errors:
            return [errors]
        errors = []
        for key, value in raw_arg.items():
            key_validation = self.key_type.validate_arg(key)
            value_validation = self.value_type.validate_arg(value)
            if key_validation:
                errors.append(
                    "Key '{0}' in map invalid: '{1}'".format(key, key_validation)
                )
            if value_validation:
                errors.append(
                    "Value for key '{0}' in map invalid: '{1}'".format(
                        key, value_validation
                    )
                )
        return errors if errors else None


@attr.s(frozen=True)
class TEnum(ThriftType):
    """
    Enums in thrift are a type that holds
    an i32 value that is expected to be one
    of a set of pre_defined values. These
    values each have name associated with them

    name:
        the name of this enum
    names_to_values:
        dict mapping the acceptable names (strings) of this enum
        to their corresponding i32 value
    values_to_names:
        dict mapping the acceptable values (i32s) of this enum
        to their corresponding string value
    ttype:
        the type (always i32)
    """

    name = attr.ib()
    names_to_values = attr.ib()
    values_to_names = attr.ib()
    ttype = attr.ib(default="i32")

    def format_arg_for_thrift(self, raw_arg, _):
        """
        When making the reqeust we want to send the
        int value. If you pass an int we will just return it
        otherwise we will translate the name to its int value.
        """
        try:
            return int(raw_arg)
        except ValueError:
            return self.names_to_values[raw_arg]

    def validate_arg(self, raw_arg):
        if self.names_to_values.get(raw_arg) or self.values_to_names.get(raw_arg):
            return None
        else:
            return "Value is not in enum '{}'".format(self.name)


@attr.s(frozen=True)
class TBool(ThriftType):
    ttype = attr.ib(default="bool")

    def validate_arg(self, raw_arg):
        return _validate_basic_type(bool, raw_arg)


def _numeric_validation(
    raw_arg, python_type, thrift_type_description, min_value, max_value
):
    error = _validate_basic_type(int, raw_arg)
    if error:
        return error
    else:
        if raw_arg > max_value:
            return "Value is too large to be a {}".format(thrift_type_description)
        elif raw_arg < min_value:
            return "Value is too small to be a {}".format(thrift_type_description)
        else:
            return None


@attr.s(frozen=True)
class TByte(ThriftType):
    MIN_VALUE = -128
    MAX_VALUE = 127
    ttype = attr.ib(default="byte")

    def validate_arg(self, raw_arg):
        return _numeric_validation(
            raw_arg, int, "byte", TByte.MIN_VALUE, TByte.MAX_VALUE
        )


@attr.s(frozen=True)
class TI16(ThriftType):
    MIN_VALUE = -32768
    MAX_VALUE = 32767
    ttype = attr.ib(default="i16")

    def validate_arg(self, raw_arg):
        return _numeric_validation(
            raw_arg, int, "16 bit integer", TI16.MIN_VALUE, TI16.MAX_VALUE
        )


@attr.s(frozen=True)
class TI32(ThriftType):
    MIN_VALUE = -2147483648
    MAX_VALUE = 2147483647
    ttype = attr.ib(default="i32")

    def validate_arg(self, raw_arg):
        return _numeric_validation(
            raw_arg, int, "32 bit integer", TI32.MIN_VALUE, TI32.MAX_VALUE
        )


@attr.s(frozen=True)
class TI64(ThriftType):
    MIN_VALUE = -9223372036854775808
    MAX_VALUE = 9223372036854775807
    ttype = attr.ib(default="i64")

    def validate_arg(self, raw_arg):
        return _numeric_validation(
            raw_arg, int, "64 bit integer", TI64.MIN_VALUE, TI64.MAX_VALUE
        )


@attr.s(frozen=True)
class TDouble(ThriftType):
    ttype = attr.ib(default="double")
    # this may bite me some day. sys.float_info implementation dependent.
    # In thrift its 64 bit signed float. That being said if python
    # cant represent the float I dont see what you can dol
    # CPython is always 64 bit, pypy is the same
    MIN_VALUE = sys.float_info.min
    MIN_VALUE = sys.float_info.max

    def validate_arg(self, raw_arg):
        if isinstance(raw_arg, int):
            return None
        return _validate_basic_type(float, raw_arg)


@attr.s(frozen=True)
class TBinary(ThriftType):
    ttype = attr.ib(default="binary")

    def validate_arg(self, raw_arg):
        return _validate_basic_type(bytes, raw_arg)


@attr.s(frozen=True)
class TString(ThriftType):
    ttype = attr.ib(default="string")

    def validate_arg(self, raw_arg):
        return _validate_basic_type(str, raw_arg)
