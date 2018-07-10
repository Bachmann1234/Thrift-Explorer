import glob
import os
import thriftpy
from collections import namedtuple
from thriftpy import thrift

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

ttype: str
    Thrift Type the spec is representing
name: str
    Name of the argument/result
type_info: None|StructType|CollectionType|MapType
    If the spec is not a base thrift type this will contain
    info required to specify the complex type
required: bool
    True if the spec is required in a request/response
    False otherwise
"""
ThriftSpec = namedtuple(
    'ThriftSpec',
    ['ttype', 'name', 'type_info', 'required']
)

"""
Spec for a particular Struct
name: str
    Name of the struct
properties: list[ThriftSpec]
    Each property of the struct is its own spec
"""
StructType = namedtuple(
    'StructType',
    ['struct_name', 'properties']
)

"""
Spec for a list or a set type
valueType: ThriftSpec
    Specification for the type the collection contains
"""
CollectionType = namedtuple(
    'CollectionType',
    ['valueType']
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
    ['keyType', 'valueType']
)

def _parse_thrift_endpoint(thrift_file, service, endpoint):
    raise ValueError("Im not implemented yet")

def _parse_thrift_service(thrift_file, service, endpoints):
    return ThriftService(
        thrift_file,
        service.__name__,
        [_parse_thrift_endpoint(thrift_file, service, endpoint) for endpoint in endpoints]
    )

def _load_thrifts(thrift_directory):
        thrifts = {}
        search_path = os.path.join(thrift_directory, "**/*thrift")
        for thrift_path in glob.iglob(search_path, recursive=True):
            thrift_filename = os.path.basename(thrift_path)
            thrifts[thrift_filename] = thriftpy.load(thrift_path)
        return thrifts

def _parse_services(thrifts):
    result = []
    for thrift_file, module in thrifts.items():
        for thrift_service in module.__thrift_meta__['services']:
            result.append(
                _parse_thrift_service(
                    thrift_file,
                    thrift_service,
                    # I'm a bit confused why this is called services and not 'methods' or 'endpoints'
                    thrift_service.thrift_services
                )
            )
    return result

class ThriftManager(object):
    def __init__(self, thrift_directory):
        self.thrift_directory = thrift_directory
        self._thrifts = _load_thrifts(self.thrift_directory)
        self.services = _parse_services(self._thrifts)
