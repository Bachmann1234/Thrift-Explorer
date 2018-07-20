import os

import thriftpy


def load_thrift_from_testdir(thrift_file):
    return thriftpy.load(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "test-thrifts", thrift_file
        )
    )
