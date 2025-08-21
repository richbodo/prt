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
    dummy_secret = tmp_path / 'client_secret.json'
    dummy_secret.write_text('{}')

    token_file = tmp_path / 'token.json'
    monkeypatch.setattr('prt_src.google_contacts.data_dir', lambda: tmp_path)
    monkeypatch.setattr('prt_src.google_contacts._secrets_file', lambda: dummy_secret)

    def fake_from_client_secrets_file(path, scopes):
        fake_from_client_secrets_file.called_path = Path(path)
        return DummyFlow()

    monkeypatch.setattr(
        'google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file',
        fake_from_client_secrets_file,
    )

    creds = _credentials()

    assert fake_from_client_secrets_file.called_path == dummy_secret
    assert token_file.exists()
    assert creds.valid
