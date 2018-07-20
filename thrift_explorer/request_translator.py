from thrift_explorer.thrift_models import BaseType


def _translate_arg(arg_spec, raw_arg):
    """
    translate the raw args into ones the client can handle.
    Basically this means turning parts of a dictionary into
    the correct objects for thrift. This is most relevant when 
    structs are introduced.
    """
    if isinstance(arg_spec.type_info, BaseType):
        return raw_arg
    else:
        raise ValueError("OMG")  # I will rethink this


def translate_request_body(endpoint, request_body):
    """
    Translate the request dictionary into whatever arguments
    are required to make the call with the thrift client

    endpoint: The endpoint spec as parsed by ThriftManager 

    request_dict: dictionary containing the args that should match
    the service. The values should have been validated before hitting 
    this method
    """
    processed_args = {}
    for arg_spec in endpoint.args:
        processed_args[arg_spec.name] = _translate_arg(
            arg_spec, request_body[arg_spec.name]
        )
    return processed_args
