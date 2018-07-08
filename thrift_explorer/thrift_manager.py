import glob
import os
import thriftpy
from collections import namedtuple

ThriftService = namedtuple(
    'ThriftService', 
    ['thrift_file', 'service_name', 'endpoints']
)

class ThriftManager(object):
    def __init__(self, thrift_directory):
        self.thrift_directory = thrift_directory
        self._thrifts = {}
        self._load_thrifts()
        
    def _load_thrifts(self):
        for thrift_path in glob.iglob("**/*thrift", recursive=True):
            thrift_filename = os.path.basename(thrift_path)
            self._thrifts[thrift_filename] = thriftpy.load(thrift_path)

    def list_services(self):
        result = []
        for thrift_file, module in self._thrifts.items():
            for thrift_service in module.__thrift_meta__['services']:
                result.append(
                    ThriftService(
                        thrift_file,
                        thrift_service.__name__,
                        # I'm a bit confused why this is called services and not 'methods' or 'endpoints'
                        thrift_service.thrift_services 
                    )
                )
        return result
