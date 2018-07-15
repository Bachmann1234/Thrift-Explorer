"""
Not directly related to the thrift explorer.
However, I like to have some confidence in the dummy
server logic since I use it for internal testing
"""
import os
import pytest
import thriftpy
from thriftpy.rpc import make_client

pytestmark = pytest.mark.uses_server

todo_thrift = thriftpy.load(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "..",
        "example-thrifts",
        "todo.thrift",
    )
)


def clear_all_tasks(client):
    for task in client.listTasks():
        client.completeTask(task.taskId)


def test_todo_service(todo_server):
    client = make_client(todo_thrift.TodoService, "127.0.0.1", 6000)
    print("Clear tasks")
    clear_all_tasks(client)
    assert not client.listTasks()
    print("Create task one")
    task = client.createTask("test todo server", "12-12-2012")
    assert task.description == "test todo server"
    assert task.dueDate == "12-12-2012"
    print("try grabbing task")
    grabbed_task = client.getTask(task.taskId)
    print(grabbed_task)
    assert task == grabbed_task
    print("Create task two")
    second_task = client.createTask("Complete testing", "1-1-2018")
    print(second_task)
    print("list tasks")
    tasks = client.listTasks()
    print(tasks)
    assert [task, second_task] == tasks
    clear_all_tasks(client)
