import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest  # noqa: E402


@pytest.fixture
def m():
    from cadkit.tools import Model
    return Model()
