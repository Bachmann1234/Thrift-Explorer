import os

import thriftpy2


def load_thrift_from_testdir(thrift_file):
    return thriftpy2.load(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "test-thrifts", thrift_file
        )
    )
