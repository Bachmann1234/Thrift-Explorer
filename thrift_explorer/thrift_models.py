from collections import namedtuple
"""
Container for a thrift service
thrift_file: str
    Name of the thrift file this service came from
name: str
    Name of the service
endpoints: list[ServiceEndpoint]
    What endpoints can be called on this service
"""
ThriftService = namedtuple(
    'ThriftService', 
    ['thrift_file', 'name', 'endpoints']
)

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
ServiceEndpoint = namedtuple(
    'ServiceEndpoint',
    ['name', 'args', 'results']
)

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
ThriftSpec = namedtuple(
    'ThriftSpec',
    ['name', 'type_info', 'required']
)

"""
Spec for a particular Struct
name: str
    Name of the struct
fields: list[ThriftSpec]
    Each property of the struct is its own spec
"""
StructType = namedtuple(
    'StructType',
    ['ttype', 'struct_name', 'fields']
)

"""
Spec for a list or a set type
valueType: ThriftSpec
    Specification for the type the collection contains
"""
CollectionType = namedtuple(
    'CollectionType',
    ['ttype', 'valueType']
)

"""
Spec for a map type
keyType: ThriftSpec
    Specification for the type of the key of the map
keyType: ThriftSpec
    Specification for the type of the value of the map
"""
MapType = namedtuple(
    'MapType',
    ['ttype', 'keyType', 'valueType']
)

"""
Spec for one of thrifts 'base types' I kept it as a
named tuple so there would always be a first element.
The first element should inform how to handle the rest
"""
BaseType = namedtuple(
    'BaseType',
    ['ttype']
)