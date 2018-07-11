import os
from thrift_explorer import thrift_manager
from thrift_explorer.thrift_manager import ThriftManager, ThriftService
import thriftpy

def test_basic_thrift_service(test_thrift_directory):
    simple_type_thrift = thriftpy.load(
        os.path.join(
            test_thrift_directory,
            'simpleType.thrift'
        )
    )
    expected = thrift_manager.ServiceEndpoint(
        name='returnInt',
        args=[
           thrift_manager.ThriftSpec(
                ttype='I32',
                name="intParameter",
                type_info=None,
                required=False
            ),
            thrift_manager.ThriftSpec(
                ttype='STRING',
                name="stringParameter",
                type_info=None,
                required=False
            ) 
        ],
        results=[
            thrift_manager.ThriftSpec(
                ttype='I32', 
                name='success', 
                type_info=None,
                required=False
            )
        ]
    )
    assert expected == thrift_manager.parse_thrift_endpoint(
        'simpleType.thrift',
        simple_type_thrift.__thrift_meta__['services'][0],
        'returnInt'
    )

def test_list_modules(example_thrift_directory):
    manager = ThriftManager(example_thrift_directory)
    expected = [
        ThriftService(
            'Batman.thrift',
            'BatPuter',
            ['ping', 'getVillain', 'addVillain', 'saveCase']
        ), 
        ThriftService(
            'todo.thrift',
            'TodoService',
            ['listTasks', 'getTask', 'createTask', 'completeTask']
        )
    ]
    actual = manager.services
    assert expected == actual
