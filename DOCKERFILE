FROM python:3.7.0
COPY . /app
WORKDIR /app
# Install the wsgi server and cython. Installing cython first works around a bug in thrift py.
# I need to consider switching to ThriftPy2
RUN pip install --trusted-host pypi.python.org gunicorn Cython 
RUN pip install --trusted-host pypi.python.org .
RUN mkdir /thrifts
ENV THRIFT_DIRECTORY /thrifts
EXPOSE 80
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:80", "thrift_explorer.wsgi"]
