"""
Not directly related to the thrift explorer.
However, I like to have some confidence in the dummy
server logic since I use it for internal testing
"""
import pytest

pytestmark = pytest.mark.uses_server


def clear_all_tasks(todo_client):
    for task in todo_client.listTasks():
        todo_client.completeTask(task.taskId)


def test_todo_service(todo_server, todo_client):
    todo_client.ping()
    print("Clear tasks")
    clear_all_tasks(todo_client)
    assert not todo_client.listTasks()
    print("Create task one")
    task = todo_client.createTask("test todo server", "12-12-2012")
    assert task.description == "test todo server"
    assert task.dueDate == "12-12-2012"
    print("try grabbing task")
    grabbed_task = todo_client.getTask(task.taskId)
    print(grabbed_task)
    assert task == grabbed_task
    print("Create task two")
    second_task = todo_client.createTask("Complete testing", "1-1-2018")
    print(second_task)
    print("list tasks")
    tasks = todo_client.listTasks()
    print(tasks)
    assert [task, second_task] == tasks
    print("count tasks")
    assert 2 == todo_client.numTasks()
    clear_all_tasks(todo_client)
