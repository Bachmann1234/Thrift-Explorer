import pytest

pytestmark = pytest.mark.uses_server


def test_failure():
    assert 1 == 1
