"""
This module is to hold the funcitonality
that converts a thirft service given to us by
thriftpy to our thrift service specification
"""
from collections import defaultdict

from thriftpy.thrift import TType

from thrift_explorer.thrift_models import (
    TI16,
    TI32,
    TI64,
    ServiceEndpoint,
    TBool,
    TByte,
    TDouble,
    TEnum,
    ThriftService,
    ThriftSpec,
    TList,
    TMap,
    TSet,
    TString,
    TStruct,
)

_BASIC_TYPE_MAP = {
    "string": TString,
    "i16": TI16,
    "i32": TI32,
    "i64": TI64,
    "byte": TByte,
    "bool": TBool,
    "double": TDouble,
}


def _parse_type(type_info):
    try:
        ttype_code, nested_type_info = type_info
    except TypeError:
        ttype_code = type_info
        nested_type_info = None

    ttype = TType._VALUES_TO_NAMES[ttype_code].lower()
    if nested_type_info is None:
        return _BASIC_TYPE_MAP[ttype]()
    elif ttype == "list":
        return TList(value_type=_parse_type(nested_type_info))
    elif ttype == "set":
        return TSet(value_type=_parse_type(nested_type_info))
    elif ttype == "map":
        key, value = nested_type_info
        return TMap(key_type=_parse_type(key), value_type=_parse_type(value))
    elif ttype == "struct":
        return TStruct(
            name=nested_type_info.__name__,
            fields=[
                _parse_arg(field_id, result)
                for field_id, result in nested_type_info.thrift_spec.items()
            ],
        )
    # Its a basic type but has defined nested type info. its probably an enum
    return TEnum(
        name=nested_type_info.__name__,
        names_to_values=nested_type_info._NAMES_TO_VALUES,
        values_to_names=nested_type_info._VALUES_TO_NAMES,
    )


def _parse_arg(field_id, thrift_arg):  # Consider renaming?
    try:
        ttype_code, name, required = thrift_arg
        type_info = None
    except ValueError:
        ttype_code, name, type_info, required = thrift_arg
    return ThriftSpec(
        field_id=field_id,
        name=name,
        type_info=_parse_type((ttype_code, type_info)),
        required=required,
    )


def _parse_thrift_endpoint(service, endpoint):
    endpoint_args = getattr(service, "{}_args".format(endpoint))
    endpoint_results = getattr(service, "{}_result".format(endpoint))
    return ServiceEndpoint(
        name=endpoint,
        args=[
            _parse_arg(field_id, arg)
            for field_id, arg in endpoint_args.thrift_spec.items()
        ],
        results=[
            _parse_arg(field_id, result)
            for field_id, result in endpoint_results.thrift_spec.items()
        ],
    )


def _parse_thrift_service(thrift_file, service, endpoints):
    return ThriftService(
        thrift_file,
        service.__name__,
        {endpoint: _parse_thrift_endpoint(service, endpoint) for endpoint in endpoints},
    )


def parse_service_specs(thrifts):
    result = defaultdict(dict)
    for thrift_file, module in thrifts.items():
        for thrift_service in module.__thrift_meta__["services"]:
            result[thrift_file][thrift_service.__name__] = _parse_thrift_service(
                thrift_file,
                thrift_service,
                # I'm a bit confused why this is called services and not 'methods' or 'endpoints'
                thrift_service.thrift_services,
            )
    # Return a standard dict so we can more easily tell when a thrift is not loaded
    return dict(result)
