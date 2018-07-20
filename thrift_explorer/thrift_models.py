import attr


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
    name: str
        Name of the argument/result
    type_info: BaseType|StructType|CollectionType|MapType
        If the spec is not a base thrift type this will contain
        info required to specify the complex type
    required: bool
        True if the spec is required in a request/response
        False otherwise
    """

    name = attr.ib()
    type_info = attr.ib()
    required = attr.ib()


@attr.s(frozen=True)
class StructType(object):
    """
    Spec for a particular Struct
    name: str
        Name of the struct
    fields: list[ThriftSpec]
        Each property of the struct is its own spec
    ttype: str
        Ttype of the object (always STRUCT)
    """

    name = attr.ib()
    fields = attr.ib()
    ttype = attr.ib(default="STRUCT")


@attr.s(frozen=True)
class CollectionType(object):
    """
    Spec for a list or a set type
    value_type: BaseType|MapType|CollectionType|StructType|EnumType 
        Specification for the type the collection contains
    ttype: the type, (always SET or LIST)
    """

    value_type = attr.ib()
    ttype = attr.ib()


@attr.s(frozen=True)
class MapType(object):
    """
    Spec for a map type
    key_type: BaseType|MapType|CollectionType|StructType|EnumType
        Specification for the type of the key of the map
    value_type: BaseType|MapType|CollectionType|StructType|EnumType
        Specification for the type of the value of the map
    ttype:
        the type (always MAP)
    """

    key_type = attr.ib()
    value_type = attr.ib()
    ttype = attr.ib(default="MAP")


@attr.s(frozen=True)
class EnumType(object):
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
    ttype = attr.ib(default="I32")


@attr.s(frozen=True)
class BaseType(object):
    """
    Spec for one of thrifts 'base types'
    ttype:
        String representing the underlying thrift type
    """

    # Thriftpy lists more types then the thrift docs
    # The thrift docs can be be out of date but
    # I think I am going to defer to them
    string_types = {"STRING"}
    int_types = {"I16", "I32", "i64"}
    float_types = {"DOUBLE"}
    boolean_types = {"BOOL"}
    byte_types = {"BYTE", "BINARY"}

    ttype = attr.ib()
