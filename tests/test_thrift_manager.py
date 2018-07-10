from thrift_explorer.thrift_manager import ThriftManager, ThriftService

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
