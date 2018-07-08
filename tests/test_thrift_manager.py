from thrift_explorer.thrift_manager import ThriftManager, ThriftService

def test_list_modules(thrift_directory):
    manager = ThriftManager(thrift_directory)
    assert [
        ThriftService(
            'Batman.thrift',
            'BatPuter',
            ['ping', 'getVillain', 'addVillian', 'saveCase']
        ), 
        ThriftService(
            'todo.thrift',
            'TodoService',
            ['listTasks', 'getTask', 'createTask', 'completeTask']
        )
    ] == manager.list_services()
