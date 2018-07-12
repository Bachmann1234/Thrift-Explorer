import glob
import os
from collections import namedtuple
import thriftpy
from thriftpy import thrift
from thriftpy.thrift import TType
from thrift_explorer.thrift_models import (
    BaseType,
    CollectionType,
    ThriftService,
    ThriftSpec,
    ServiceEndpoint,
)


def _parse_type(ttype_code, type_info):
    ttype = TType._VALUES_TO_NAMES[ttype_code]
    if type_info == None:
        return BaseType(ttype)
    elif ttype in set(["SET", "LIST"]):
        return CollectionType(ttype=ttype, valueType=_parse_type(type_info, None))
    elif ttype == "MAP":
        pass
    elif ttype == "STRUCT":
        pass
    else:
        raise ValueError("I dont know how to parse {}".format(ttype))


def _parse_arg(thrift_arg):  # Consider renaming?
    try:
        ttype_code, name, required = thrift_arg
        type_info = None
    except ValueError:
        ttype_code, name, type_info, required = thrift_arg
    return ThriftSpec(
        name=name, type_info=_parse_type(ttype_code, type_info), required=required
    )


def parse_thrift_endpoint(thrift_file, service, endpoint):
    endpoint_args = getattr(service, "{}_args".format(endpoint))
    endpoint_results = getattr(service, "{}_result".format(endpoint))
    return ServiceEndpoint(
        name=endpoint,
        args=[_parse_arg(arg) for arg in endpoint_args.thrift_spec.values()],
        results=[
            _parse_arg(result) for result in endpoint_results.thrift_spec.values()
        ],
    )


def parse_thrift_service(thrift_file, service, endpoints):
    return ThriftService(
        thrift_file,
        service.__name__,
        [
            parse_thrift_endpoint(thrift_file, service, endpoint)
            for endpoint in endpoints
        ],
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
        for thrift_service in module.__thrift_meta__["services"]:
            result.append(
                parse_thrift_service(
                    thrift_file,
                    thrift_service,
                    # I'm a bit confused why this is called services and not 'methods' or 'endpoints'
                    thrift_service.thrift_services,
                )
            )
    return result


class ThriftManager(object):
    def __init__(self, thrift_directory):
        self.thrift_directory = thrift_directory
        self._thrifts = _load_thrifts(self.thrift_directory)
        self.services = _parse_services(self._thrifts)
