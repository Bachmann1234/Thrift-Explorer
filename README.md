# Thrift Explorer
This repo is not 100% sure what it wants to be. But let me walk you though my intentions

[Apache Thrift](https://thrift.apache.org/) is a language agnostic framework that enables typed communication between services. 

Working with thrifts and the thrift compiler is fairly easy. Write a thrift file, generate your server and implement your buisness logic as a "handler" that your server uses.

To communicate with a thrift based service simple use that same compiler to generate your thrift and you are off to the races.

I began writing this project because I wanted a quick and easy way to make thrift requests on the fly for when I am experimenting or debugging a thrift service. There are tools that allow you to do this but the ones I have played with felt cumbersome and made assumptions about your workflow (such as your protocol/transport choise).

I wanted to see if I could build something I liked better.

I plan to start with a CLI. I would consider this a sort of proof of concept. Ultimately I think working with thrifts this way is better suited to a gui tool. Even simple requests have a lot of arguments. 



