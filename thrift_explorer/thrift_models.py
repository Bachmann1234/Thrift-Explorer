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
    """

    ttype = attr.ib()
    struct_name = attr.ib()
    fields = attr.ib()


@attr.s(frozen=True)
class CollectionType(object):
    """
    Spec for a list or a set type
    value_type: ThriftSpec
        Specification for the type the collection contains
    """

    ttype = attr.ib()
    value_type = attr.ib()


@attr.s(frozen=True)
class MapType(object):
    """
    Spec for a map type
    key_type: ThriftSpec
        Specification for the type of the key of the map
    value_type: ThriftSpec
        Specification for the type of the value of the map
    """

    ttype = attr.ib()
    key_type = attr.ib()
    value_type = attr.ib()


"""
Spec for one of thrifts 'base types'
"""


@attr.s(frozen=True)
class BaseType(object):
    ttype = attr.ib()
