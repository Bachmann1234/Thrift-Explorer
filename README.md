# Thrift Explorer
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://github.com/Bachmann1234/thriftExplorer/blob/master/LICENSE)
[![Build Status](https://travis-ci.org/Bachmann1234/thriftExplorer.svg?branch=master)](https://travis-ci.org/Bachmann1234/thriftExplorer)
[![Coverage Status](https://coveralls.io/repos/github/Bachmann1234/thriftExplorer/badge.svg?branch=master)](https://coveralls.io/github/Bachmann1234/thriftExplorer?branch=master)
[![PyPI version](https://badge.fury.io/py/thriftexplorer.svg)](https://badge.fury.io/py/thriftexplorer)

[Apache Thrift](https://thrift.apache.org/) is a language agnostic framework that enables typed communication between services. 

Thrift explorer is intended to be a tool aimed at developers who use thrift services. Enabling the user to explore thrift services they
have access to without having to write or maintain any code. If the required thrifts are loaded into Thrift Explorer you can go ahead
and make requests.

The goal of the project is to provide the simple pick up and play aspects of http apis. If the thrifts are loaded in here you can call your thrift services without generating
a client or loading up an environment. Just make a curl call. I think it is most helpful when trying a service out for the first time or doing some basic testing of a service.

Right now the primary method for doing this is the the flask server. However, i'm thinking the tools here could be used to make cli's/gui's. For now if I invest more time in this I will be spending it
on refining the workflow that already exists rather than providing more workflows

[Server Postman Collection](ThriftExplorer.postman_collection)

## Running the flask server

The server requires one environment variable be set "THRIFT_DIRECTORY" this should point to a directory with all the thrift files you want the server to be able to access. Make sure all dependencies are included.

In addition you can set DEFAULT_PROTOCOL (TBinaryProtocol if not defined) and DEFAULT_TRANSPORT (TBufferedTransport if not defined)

One you have configured the server you can run the flask development server our use your favorite WIGI HTTP server to run the service

## Running the example thrift server

This repo contains some example thrifts and one example thrift service. See [Todo Thrift](/example-thrifts/todo.thrift) for a service definition.

To run it just set your pythonpath appropriately (see [My environment](/environment.fish) for how I setup my environment (I use fish sell). Then run

```
python tests/todoserver/service.py
```

