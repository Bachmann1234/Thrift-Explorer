include "basethrifts/Exceptions.thrift"

struct Task {
    1: optional string taskId;
    2: optional string description;
    3: optional string dueDate;
}

service TodoService {
    void ping()
    list<Task> listTasks()
    Task getTask(1: string taskId) throws (1: Exceptions.NotFound notfound)
    Task createTask(1: string description, 2: string dueDate)
    void completeTask(1: string taskId) throws (1: Exceptions.NotFound notfound)
}