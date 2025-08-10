from pathlib import Path
import sys
from dotenv import load_dotenv
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()


class FakeKeyring:
    def __init__(self):
        self.store = {}

    def set_password(self, service, name, value):
        self.store[(service, name)] = value

    def get_password(self, service, name):
        return self.store.get((service, name))

    def delete_password(self, service, name):
        self.store.pop((service, name), None)


@pytest.fixture
def fake_keyring(monkeypatch):
    from utils import credentials

    fk = FakeKeyring()
    monkeypatch.setattr(credentials, "keyring", fk)
    return fk
