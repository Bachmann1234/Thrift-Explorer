import os
import pytest
from thrift_explorer import create_app

@pytest.fixture
def client():
    app = create_app(test_config={
        "SECRET_KEY": "test",
        "TESTING": True
    })
    yield app.test_client()

@pytest.fixture()
def example_thrift_directory():
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "..",
        "example-thrifts",
    )