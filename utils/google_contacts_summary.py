#!/usr/bin/env python3
"""Summarize Google Contacts CSV exports.

This script reads an exported Google Contacts CSV file, counts the
number of contacts, and prints each contact's name along with any
associated email addresses and phone numbers.

Usage:
    python google_contacts_summary.py contacts.csv

If no file path is provided as an argument, the script will notify the
user to supply one.
"""

from __future__ import annotations

import csv
import sys
from typing import Dict, List


def _extract_fields(row: Dict[str, str], prefix: str) -> List[str]:
    """Return list of label/value pairs for a given contact field prefix.

    Parameters
    ----------
    row: Dict[str, str]
        A contact row from ``csv.DictReader``.
    prefix: str
        ``"E-mail"`` or ``"Phone"``.
    """
    results: List[str] = []
    for key, value in row.items():
        if key.startswith(prefix) and key.endswith("Value"):
            val = value.strip()
            if not val:
                continue
            label_key = key.replace("Value", "Label")
            label = row.get(label_key, "").strip()
            results.append(f"{label}: {val}" if label else val)
    return results


def parse_contacts(csv_path: str) -> List[Dict[str, List[str]]]:
    """Parse contacts from a Google Contacts CSV export."""
    contacts: List[Dict[str, List[str]]] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip completely empty rows
            if not any(field.strip() for field in row.values()):
                continue
            first = row.get("First Name", "").strip()
            last = row.get("Last Name", "").strip()
            contact = {
                "first": first,
                "last": last,
                "emails": _extract_fields(row, "E-mail"),
                "phones": _extract_fields(row, "Phone"),
            }
            contacts.append(contact)
    return contacts


def main() -> None:
    if len(sys.argv) < 2:
        print("Please provide the path to a Google Contacts CSV file.")
        return

    csv_path = sys.argv[1]
    try:
        contacts = parse_contacts(csv_path)
    except FileNotFoundError:
        print(f"File not found: {csv_path}")
        return

    print(f"Number of contacts: {len(contacts)}")
    for contact in contacts:
        name = f"{contact['first']} {contact['last']}".strip()
        if not name:
            name = "(No name)"
        print(f"Contact: {name}")
        if contact["emails"]:
            print("  Emails:")
            for email in contact["emails"]:
                print(f"    {email}")
        if contact["phones"]:
            print("  Phones:")
            for phone in contact["phones"]:
                print(f"    {phone}")


if __name__ == "__main__":
    main()
