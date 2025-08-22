from pathlib import Path
import sys
import types
from unittest import mock

import pytest


def test_credentials_use_client_secret(tmp_path, monkeypatch):
    modules: dict[str, types.ModuleType] = {}

    # Stub googleapiclient package
    gapiclient = types.ModuleType("googleapiclient")
    gapiclient.__path__ = []  # Mark as package
    modules["googleapiclient"] = gapiclient
    discovery = types.ModuleType("discovery")
    discovery.build = lambda *a, **k: None
    modules["googleapiclient.discovery"] = discovery
    errors = types.ModuleType("errors")
    errors.HttpError = Exception
    modules["googleapiclient.errors"] = errors

    # Stub google.auth related packages
    google_mod = types.ModuleType("google")
    google_mod.__path__ = []
    modules["google"] = google_mod
    auth_mod = types.ModuleType("auth")
    auth_mod.__path__ = []
    modules["google.auth"] = auth_mod
    transport_mod = types.ModuleType("transport")
    transport_mod.__path__ = []
    modules["google.auth.transport"] = transport_mod
    requests_mod = types.ModuleType("requests")
    requests_mod.Request = object
    modules["google.auth.transport.requests"] = requests_mod
    oauth2_mod = types.ModuleType("oauth2")
    oauth2_mod.__path__ = []
    modules["google.oauth2"] = oauth2_mod

    class DummyCreds:
        valid = True
        expired = False
        refresh_token = None

        @classmethod
        def from_authorized_user_file(cls, path, scopes):
            return cls()

        def refresh(self, request):
            pass

        def to_json(self):
            return '{"token": "dummy"}'

    creds_mod = types.ModuleType("credentials")
    creds_mod.Credentials = DummyCreds
    modules["google.oauth2.credentials"] = creds_mod

    # Stub google_auth_oauthlib.flow
    gaol_mod = types.ModuleType("google_auth_oauthlib")
    gaol_mod.__path__ = []
    modules["google_auth_oauthlib"] = gaol_mod
    flow_mod = types.ModuleType("flow")

    class DummyFlow:
        def run_local_server(self, *args, **kwargs):
            return DummyCreds()

    def fake_from_client_secrets_file(path, scopes):
        fake_from_client_secrets_file.called_path = Path(path)
        return DummyFlow()

    flow_mod.InstalledAppFlow = type(
        "InstalledAppFlow", (), {"from_client_secrets_file": staticmethod(fake_from_client_secrets_file)}
    )
    modules["google_auth_oauthlib.flow"] = flow_mod

    dummy_secret = tmp_path / "client_secret.json"
    dummy_secret.write_text("{}")

    with mock.patch.dict(sys.modules, modules):
        import prt_src.google_contacts as gc

        token_file = tmp_path / "token.json"
        monkeypatch.setattr(gc, "data_dir", lambda: tmp_path)
        monkeypatch.setattr(gc, "_secrets_file", lambda: dummy_secret)

        creds = gc._credentials()

    assert fake_from_client_secrets_file.called_path == dummy_secret
    assert token_file.exists()
    assert creds.valid

