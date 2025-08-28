from pathlib import Path

import pytest

from prt_src.google_contacts import _credentials


class DummyCreds:
    valid = True

    def to_json(self):
        return '{"token": "dummy"}'


class DummyFlow:
    def run_local_server(self, *args, **kwargs):
        return DummyCreds()


def test_credentials_use_client_secret(tmp_path, monkeypatch):
    secrets_dir = Path(__file__).resolve().parents[1] / "prt" / "secrets"
    secrets_file = secrets_dir / "client_secret.json"
    if not secrets_file.exists():
        pytest.skip("client_secret.json missing")

    token_file = tmp_path / "token.json"
    monkeypatch.setattr("prt.google_contacts.data_dir", lambda: tmp_path)

    def fake_from_client_secrets_file(path, scopes):
        fake_from_client_secrets_file.called_path = Path(path)
        return DummyFlow()

    monkeypatch.setattr(
        "google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file",
        fake_from_client_secrets_file,
    )

    creds = _credentials()

    assert fake_from_client_secrets_file.called_path == secrets_file
    assert token_file.exists()
    assert creds.valid
