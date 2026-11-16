import pytest

from app.db import connect, migrate


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "test.db")
    migrate(c)
    yield c
    c.close()


from pathlib import Path

from app.ddragon import load as load_ddragon

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def dd():
    return load_ddragon(FIXTURES / "ddragon")
