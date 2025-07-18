from typing import List, Tuple, Dict

def fetch_contacts(config: Dict[str, str]) -> List[Tuple[str, str]]:
    """Return sample contacts instead of calling Google."""
    return [
        ("Alice Example", "alice@example.com"),
        ("Bob Example", "bob@example.com"),
        ("Carol Example", "carol@example.com"),
    ]
