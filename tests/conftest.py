import pytest
from thrift_explorer import create_app

@pytest.fixture
def client():
    app = create_app(test_config={
        "SECRET_KEY": "test",
        "TESTING": True
    })
    yield app.test_client()