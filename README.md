# Thrift Explorer
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://github.com/Bachmann1234/thriftExplorer/blob/master/LICENSE)
[![Build Status](https://travis-ci.org/Bachmann1234/thriftExplorer.svg?branch=master)](https://travis-ci.org/Bachmann1234/thriftExplorer)
[![Coverage Status](https://coveralls.io/repos/github/Bachmann1234/thriftExplorer/badge.svg?branch=master)](https://coveralls.io/github/Bachmann1234/thriftExplorer?branch=master)
[![PyPI version](https://badge.fury.io/py/thriftexplorer.svg)](https://badge.fury.io/py/thriftexplorer)

[Apache Thrift](https://thrift.apache.org/) is a language agnostic framework that enables typed communication between services. 

Thrift explorer is intended to be a tool aimed at developers who use thrift services. Enabling the user to explore thrift services they
have access to without having to write or maintain any code. If the required thrifts are loaded into Thrift Explorer developers are enabled to access thrift apis with the same toolset they use for HTTP apis.

Right now the primary method for doing this is the the flask server. However, i'm thinking the tools here could be used to make cli's/gui's. For now if I invest more time in this I will be spending it
on refining the workflow that already exists rather than providing more workflows

## Example Usage

Example calls are provided as part of a [Postman Collection](ThriftExplorer.postman_collection.json). However. Lets walk though a basic session.

If you are working on a todo thrift service that you have running on your machine you can use thrift explorer to make calls to it. With the todo server running you 
add the todo thrifts to thrift explorer and start the server. (I will be using [curl](https://curl.haxx.se/) to make requests and [jq](https://stedolan.github.io/jq/) to pretty print the responses)

You can see what services are loaded

```json
curl -Ss localhost:5000 | jq '.'                                                                                                                                                                     
{
  "thrifts": {
    "Batman.thrift": [
      "BatPuter"
    ],
    "todo.thrift": [
      "TodoService"
    ]
  }
}
```

List the methods of a particular service

```json
curl -Ss localhost:5000/todo/TodoService/ | jq '.'                                                                                                                                                   
{
  "thrift": "todo.thrift",
  "service": "TodoService",
  "methods": [
    "ping",
    "listTasks",
    "numTasks",
    "getTask",
    "createTask",
    "completeTask",
    "fancyNewMethod"
  ]
}
```

Make a call to one of the methods of that service (the response is in the "data" field of the response body)

```json
curl -Ss -X POST \                                                                                                                                                                                   
           http://localhost:5000/todo/TodoService/createTask/ \
           -H 'Content-Type: application/json' \
           -d '{
             "host": "localhost",
             "port": 6000,
             "protocol": "tbinaryprotocol",
             "transport": "tbufferedtransport",
             "request_body": {"description": "task 1", "dueDate": "12-12-2012"}
         }' | jq "."
{
  "status": "Success",
  "request": {
    "thrift_file": "todo.thrift",
    "service_name": "TodoService",
    "endpoint_name": "createTask",
    "host": "localhost",
    "port": 6000,
    "protocol": "tbinaryprotocol",
    "transport": "tbufferedtransport",
    "request_body": {
      "description": "task 1",
      "dueDate": "12-12-2012"
    }
  },
  "data": {
    "__thrift_struct_class__": "Task",
    "taskId": "1",
    "description": "task 1",
    "dueDate": "12-12-2012"
  },
  "time_to_make_request": "0:00:00.008794",
  "time_to_connect": "0:00:00.001502"
}
```

and just for fun we will make another call

```json
curl -Ss -X POST \                                                                                                                                                                                   
               http://localhost:5000/todo/TodoService/getTask/ \
               -H 'Content-Type: application/json' \
               -d '{
                 "host": "localhost",
                 "port": 6000,
                 "protocol": "tbinaryprotocol",
                 "transport": "tbufferedtransport",
                 "request_body": {"taskId": "1"}
             }' | jq "."
{
  "status": "Success",
  "request": {
    "thrift_file": "todo.thrift",
    "service_name": "TodoService",
    "endpoint_name": "getTask",
    "host": "localhost",
    "port": 6000,
    "protocol": "tbinaryprotocol",
    "transport": "tbufferedtransport",
    "request_body": {
      "taskId": "1"
    }
  },
  "data": {
    "__thrift_struct_class__": "Task",
    "taskId": "1",
    "description": "task 1",
    "dueDate": "12-12-2012"
  },
  "time_to_make_request": "0:00:00.001283",
  "time_to_connect": "0:00:00.000554"
}
```

If you make a mistake making a request thrift explorer tries to be helpful telling you the mistake you made

```json
curl -sS -X POST \ 
              http://localhost:5000/todo/TodoService/completeTask/ \
              -d '{
                "host": "localhost",
                "port": 6000,
                "protocol": "tbinaryprotocol",
                "transport": "tbufferedtransport",
                "request_body": {"description": "task 1"}
            }' | jq '.'
{
  "errors": [
    {
      "code": "ErrorCode.REQUIRED_FIELD_MISSING",
      "message": "Required Field 'taskId' not found",
      "arg_spec": null
    }
  ]
}
```


and if you just want to get the thrift itself you can do that to

```java
curl -Ss localhost:5000/todo/
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
    void completeTask(1: required string taskId) throws (1: Exceptions.NotFound notfound);
    void fancyNewMethod(); // Not implemented by the server to simulate that kind of error
}
```

## Running the flask server

The service is configured via environment variables

| Variable                 | Description                                                                   | Default            | Required |
|--------------------------|-------------------------------------------------------------------------------|--------------------|----------|
| THRIFT_DIRECTORY         | The directory where the thrifts you want the server to be aware of are stored |                    | Yes      |
| DEFAULT_THRIFT_PROTOCOL  | What thrift protocol should the server assume if one is not provided          | TBinaryProtocol    | No       |
| DEFAULT_THRIFT_TRANSPORT | What thrift transport should the server assume if one is not provided         | TBufferedTransport | No       |

One you have configured the server you can run the flask development server or use your favorite WIGI HTTP server to run the service

## Running the example thrift server

This repo contains some example thrifts and one example thrift service. See [Todo Thrift](/example-thrifts/todo.thrift) for a service definition.

To run it just set your pythonpath appropriately (see [My environment](/environment.fish) for how I setup my environment (I use fish sell). Then run

```
python tests/todoserver/service.py
```

