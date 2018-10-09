include "basethrifts/Exceptions.thrift"

struct Task {
    1: optional string taskId;
    2: optional string description;
    3: optional string dueDate;
}

service TodoService {
    void ping();
    list<Task> listTasks();
    i64 numTasks();
    Task getTask(1: string taskId) throws (1: Exceptions.NotFound notfound);
    Task createTask(1: string description, 2: string dueDate);
    Task createTaskWithObject(1: Task task);
    void completeTask(1: required string taskId) throws (1: Exceptions.NotFound notfound);
    void fancyNewMethod(); // Not implemented by the server to simulate that kind of error
}