import pytest
from unittest.mock import MagicMock

from prt_src.cli_operations import PRTCLI


@pytest.fixture
def cli(monkeypatch):
    def fake_init(self):
        self.api = MagicMock()
    monkeypatch.setattr(PRTCLI, "__init__", fake_init)
    return PRTCLI()


def _contact(idx: int):
    return {
        "id": idx,
        "name": f"John {idx}",
        "email": "",
        "relationship_info": {"tags": [], "notes": []},
    }


def test_search_contacts_preview(monkeypatch, cli):
    prompt_mock = MagicMock(return_value="John")
    confirm_mock = MagicMock(return_value=False)
    print_mock = MagicMock()
    api_mock = MagicMock()
    contacts = [_contact(i) for i in range(1, 5)]
    api_mock.search_contacts.return_value = contacts

    monkeypatch.setattr("prt_src.cli_operations.Prompt.ask", prompt_mock)
    monkeypatch.setattr("prt_src.cli_operations.Confirm.ask", confirm_mock)
    monkeypatch.setattr("prt_src.cli_operations.console.print", print_mock)
    cli.display_contacts = MagicMock()
    cli.handle_contact_selection = MagicMock()
    cli.api = api_mock

    cli.search_contacts()

    api_mock.search_contacts.assert_called_once_with("John")
    confirm_mock.assert_called_once()
    print_mock.assert_any_call("\nFound 4 contacts matching 'John':", style="bold blue")
    cli.display_contacts.assert_not_called()


def test_search_tags_preview(monkeypatch, cli):
    prompt_mock = MagicMock(return_value="family")
    confirm_mock = MagicMock(return_value=False)
    print_mock = MagicMock()
    api_mock = MagicMock()
    tags = [{"id": 1, "name": "family", "contact_count": 4}]
    contacts = [_contact(i) for i in range(1, 5)]
    api_mock.search_tags.return_value = tags
    api_mock.get_contacts_by_tag.return_value = contacts

    monkeypatch.setattr("prt_src.cli_operations.Prompt.ask", prompt_mock)
    monkeypatch.setattr("prt_src.cli_operations.Confirm.ask", confirm_mock)
    monkeypatch.setattr("prt_src.cli_operations.console.print", print_mock)
    cli.display_contacts = MagicMock()
    cli.handle_contact_selection = MagicMock()
    cli.api = api_mock

    cli.search_tags()

    api_mock.search_tags.assert_called_once_with("family")
    api_mock.get_contacts_by_tag.assert_called_once_with("family")
    confirm_mock.assert_called_once()
    print_mock.assert_any_call("Tag: family (4 contacts)", style="bold blue")
    cli.display_contacts.assert_not_called()


def test_import_contacts_success(tmp_path, monkeypatch, cli):
    csv_file = tmp_path / "contacts.csv"
    csv_file.write_text("dummy,content")

    def fake_data_dir():
        return tmp_path

    contacts = [{"first": "John", "last": "Doe", "emails": ["j@example.com"], "phones": []}]

    api_mock = MagicMock()
    api_mock.import_contacts.return_value = True
    cli.api = api_mock

    monkeypatch.setattr("prt_src.config.data_dir", fake_data_dir)
    monkeypatch.setattr("utils.google_contacts_summary.parse_contacts", lambda path: contacts)
    prompt_mock = MagicMock(return_value="1")
    confirm_mock = MagicMock(return_value=True)
    print_mock = MagicMock()
    monkeypatch.setattr("prt_src.cli_operations.Prompt.ask", prompt_mock)
    monkeypatch.setattr("prt_src.cli_operations.Confirm.ask", confirm_mock)
    monkeypatch.setattr("prt_src.cli_operations.console.print", print_mock)

    cli.import_contacts()

    api_mock.import_contacts.assert_called_once_with(contacts)
    confirm_mock.assert_called_once()
    print_mock.assert_any_call("Successfully imported 1 contacts.", style="green")
