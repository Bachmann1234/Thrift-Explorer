# Thrift Explorer
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://github.com/Bachmann1234/thrift-explorer/blob/master/LICENSE)
[![Build Status](https://travis-ci.org/Bachmann1234/Thrift-Explorer.svg?branch=master)](https://travis-ci.org/Bachmann1234/Thrift-Explorer)
[![Coverage Status](https://coveralls.io/repos/github/Bachmann1234/Thrift-Explorer/badge.svg?branch=master)](https://coveralls.io/github/Bachmann1234/Thrift-Explorer?branch=master)
[![PyPI version](https://badge.fury.io/py/thrift-explorer.svg)](https://badge.fury.io/py/thrift-explorer)

[Apache Thrift](https://thrift.apache.org/) is a language agnostic framework that enables typed communication between services. 

Thrift explorer is intended to be a tool aimed at developers who use thrift services. Enabling the user to explore their services without having to write or maintain any code. 

# This project is alpha

I am still finding fundemental issues with the implementation and am working though them. Slowly but surely

## How does this work

You place your service thrifts in a directory and configure Thrift Explorer to pull from it. Then make http calls to Thrift Explorer providing information such as host/port and 
it will forward your request to it and return the response.

## Example Usage

Example calls are provided as part of a [Postman Collection](ThriftExplorer.postman_collection.json). However, Lets walk though a basic session.

If you are working on a todo thrift service that you have running on your machine you can use thrift explorer to make calls to it. With the todo server running you 
add the todo thrifts to thrift explorer and start the server. (I will be using [curl](https://curl.haxx.se/) to make requests and [jq](https://stedolan.github.io/jq/) to pretty print the responses)

You can see what services are loaded

```json
curl -Ss localhost:5000 | jq '.'                                                                                                                                                                     
{
  "thrifts": [
    {
      "thrift": "Batman.thrift",
      "service": "BatPuter",
      "methods": [
        "ping",
        "getVillain",
        "addVillain",
        "saveCase"
      ]
    },
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
  ]
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
      "arg_spec": {
                    "name": "taskId",
                    "required": true,
                    "type_info": {"ttype": "string"},
      },
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

## Installation and Running the server

### Installation with pip

If you are comfortable with python environments and python packaging you can install this with pip. I suggest using a virtual environment.

```
pip install thrift-explorer
```

Then you may either use the flask development server or you can install a wsgi server. I am going to use gunicorn

```
pip install gunicorn
```

Then you set the environment variables you will use to configure the server. See [Configuring the server](#configuring-the-server) for details. At a minimum you must set THRIFT_DIRECTORY

```
export THRIFT_DIRECTORY=$(pwd)/example-thrifts/
```

Then start it!

```
gunicorn -b 127.0.0.1:5000 thrift_explorer.wsgi
[2018-10-07 12:01:30 -0400] [7864] [INFO] Starting gunicorn 19.9.0
[2018-10-07 12:01:30 -0400] [7864] [INFO] Listening at: http://127.0.0.1:5000 (7864)
[2018-10-07 12:01:30 -0400] [7864] [INFO] Using worker: sync
[2018-10-07 12:01:30 -0400] [7867] [INFO] Booting worker with pid: 7867
```

### Installation with docker

If you would rather not work with the python directly you can pull down a docker container

```
docker pull bachmann1234/thrift-explorer
```

When running the docker container you are going to need to pass in a directory containing the thrifts the server will load in.
This will be provided via the source parameter. In the example below I pass in the example-thrifts directory in this very repo 

```
docker run --mount type=bind,source=$(pwd)/example-thrifts,target=/thrifts -p 5000:80 bachmann1234/thrift-explorer
```

In english this command is saying "run the thrift-explorer server with example-thrifts as its thrift directory. Make it so that server is accessible to me at port 8000". You can also
pass in other environment variables in this command to configure the server. See [Configuring the server](#configuring-the-server) for details.

For a more detailed explanation of the docker command [consult the docker documentation](https://docs.docker.com/engine/reference/run/)

One gotcha: When using the docker container you need to be mindful of how networking works with docker. For example. If you are running thrift-explorer with the docker container
and you need it to access a service running on your localhost you would use the hostname "host.docker.internal" (at least on docker-for-mac). For example

```json
curl -Ss -X POST \  
                    http://localhost:4000/todo/TodoService/createTask/ \
                    -H 'Content-Type: application/json' \
                    -d '{
                      "host": "host.docker.internal",
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
    "host": "host.docker.internal",
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
    "taskId": "2",
    "description": "task 1",
    "dueDate": "12-12-2012"
  },
  "time_to_make_request": "0:00:00.012562",
  "time_to_connect": "0:00:00.001214"
}
```

### Configuring the server 

The service is configured via environment variables

| Variable                 | Description                                                                   | Default            | Required |
|--------------------------|-------------------------------------------------------------------------------|--------------------|----------|
| THRIFT_DIRECTORY         | The directory where the thrifts you want the server to be aware of are stored |                    | Yes      |
| DEFAULT_THRIFT_PROTOCOL  | What thrift protocol should the server assume if one is not provided          | TBinaryProtocol    | No       |
| DEFAULT_THRIFT_TRANSPORT | What thrift transport should the server assume if one is not provided         | TBufferedTransport | No       |




## Running the example thrift server

This repo contains some example thrifts and one example thrift service. See [Todo Thrift](/example-thrifts/todo.thrift) for a service definition.

To run it just set your pythonpath appropriately (see [My environment](/environment.fish) for how I setup my environment (I use fish shell)). Then run

```
python tests/todoserver/service.py
```

This service is intended as a development/testing aid. It is not required for using thrift explorer