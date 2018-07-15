import os
import sqlite3
import thriftpy
from thriftpy.rpc import make_server

todo_thrift = thriftpy.load(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "..",
        "..",
        "example-thrifts",
        "todo.thrift",
    ),
    module_name="todo_thrift",
)


def _get_db():
    db = sqlite3.connect("todo.sqlite3")
    with db:
        db.execute(
            "create table if not exists task (id integer primary key, description varchar, duedate varchar);"
        )
    return db


def _create_task(db_row):
    task_id, description, due_date = db_row
    return todo_thrift.Task(
        taskId=str(task_id), description=description, dueDate=due_date
    )


class Dispatcher(object):
    def listTasks(self):
        cursor = _get_db().cursor()
        cursor.execute("select * from task;")
        return [_create_task(row) for row in cursor]

    def getTask(self, task_id):
        cursor = _get_db().cursor()
        cursor.execute("select * from task where id=?", (task_id,))
        result = cursor.fetchone()
        if not result:
            raise todo_thrift.Exceptions.NotFound()

        return _create_task(result)

    def createTask(self, description, due_date):
        with _get_db() as db:
            cursor = db.cursor()
            cursor.execute(
                "insert into task (description, duedate) values(?, ?)",
                (description, due_date),
            )
        return self.getTask(cursor.lastrowid)

    def completeTask(self, task_id):
        with _get_db() as db:
            cursor = db.cursor()
            cursor.execute("delete from task where id = ?", (task_id,))
        if not cursor.rowcount:
            raise todo_thrift.Exceptions.NotFound()


def run_server(port):
    make_server(todo_thrift.TodoService, Dispatcher(), "127.0.0.1", port).serve()


if __name__ == "__main__":
    run_server(6000)
