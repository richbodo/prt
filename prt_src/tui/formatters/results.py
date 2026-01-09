"""ResultsFormatter - Format database results for display.

Supports multiple formatting modes:
- numbered_list: [1], [2], [3] with optional selection markers
- table: ASCII table with columns
- card: Detailed multi-line view
- compact: One-line or comma-separated summaries
"""

from typing import Any


class ResultsFormatter:
    """Format database results for display in various modes."""

    def render(
        self,
        items: list[dict[str, Any]] | None,
        result_type: str,
        mode: str = "numbered_list",
        show_selection: bool = False,
        selected_ids: set[int] | None = None,
        pagination: dict[str, int] | None = None,
        max_column_width: int = 30,
        style: str | None = None,
    ) -> str:
        """Render items in the specified format.

        Args:
            items: List of dictionaries representing items to format
            result_type: Type of results ('contacts', 'relationships', 'notes', 'tags')
            mode: Formatting mode ('numbered_list', 'table', 'card', 'compact')
            show_selection: Show selection markers (checkboxes)
            selected_ids: Set of selected item IDs
            pagination: Dict with 'total', 'showing', 'offset' keys
            max_column_width: Maximum width for table columns
            style: Style variant (e.g., 'lines' for compact mode)

        Returns:
            Formatted string

        Raises:
            ValueError: If mode is invalid
        """
        # Handle None or empty input
        if items is None:
            items = []

        if not items:
            return ""

        # Validate mode
        valid_modes = ["numbered_list", "table", "card", "compact"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode '{mode}'. Valid modes: {', '.join(valid_modes)}")

        # Route to appropriate formatter
        if mode == "numbered_list":
            return self._format_numbered_list(
                items, result_type, show_selection, selected_ids, pagination
            )
        elif mode == "table":
            return self._format_table(items, result_type, max_column_width)
        elif mode == "card":
            return self._format_card(items, result_type)
        elif mode == "compact":
            return self._format_compact(items, result_type, style)

        return ""  # Should never reach here

    def _format_numbered_list(
        self,
        items: list[dict[str, Any]],
        result_type: str,
        show_selection: bool,
        selected_ids: set[int] | None,
        pagination: dict[str, int] | None,
    ) -> str:
        """Format items as numbered list."""
        lines = []

        # Add pagination header if provided
        if pagination:
            total = pagination.get("total", len(items))
            showing = pagination.get("showing", len(items))
            offset = pagination.get("offset", 0)
            start = offset + 1
            end = offset + showing
            lines.append(f"Showing {start}-{end} of {total}\n")

        # Format each item
        for idx, item in enumerate(items, start=1):
            # Add selection marker if requested
            if show_selection:
                item_id = item.get("id", idx)
                marker = "[✓]" if selected_ids and item_id in selected_ids else "[ ]"
                prefix = f"{marker} [{idx}]"
            else:
                prefix = f"[{idx}]"

            # Format the item content based on type
            content = self._format_item_one_line(item, result_type)
            lines.append(f"{prefix} {content}")

        return "\n".join(lines)

    def _format_table(
        self,
        items: list[dict[str, Any]],
        result_type: str,
        max_column_width: int,
    ) -> str:
        """Format items as ASCII table."""
        if result_type == "contacts":
            # Define columns for contacts
            headers = ["Name", "Email", "Location"]
            rows = []
            for item in items:
                rows.append(
                    [
                        self._truncate(item.get("name", ""), max_column_width),
                        self._truncate(item.get("email", ""), max_column_width),
                        self._truncate(item.get("location", ""), max_column_width),
                    ]
                )
        elif result_type == "relationships":
            headers = ["From", "To", "Type"]
            rows = []
            for item in items:
                rows.append(
                    [
                        self._truncate(item.get("from_contact", ""), max_column_width),
                        self._truncate(item.get("to_contact", ""), max_column_width),
                        self._truncate(item.get("type", ""), max_column_width),
                    ]
                )
        elif result_type == "notes":
            headers = ["Title", "Date", "Preview"]
            rows = []
            for item in items:
                content_preview = item.get("content", "")[:40]
                rows.append(
                    [
                        self._truncate(item.get("title", ""), max_column_width),
                        self._truncate(item.get("date", ""), max_column_width),
                        self._truncate(content_preview, max_column_width),
                    ]
                )
        else:  # tags or other
            headers = ["ID", "Name", "Label"]
            rows = []
            for item in items:
                rows.append(
                    [
                        str(item.get("id", "")),
                        self._truncate(item.get("name", ""), max_column_width),
                        self._truncate(item.get("label", ""), max_column_width),
                    ]
                )

        # Build table
        return self._build_ascii_table(headers, rows)

    def _build_ascii_table(self, headers: list[str], rows: list[list[str]]) -> str:
        """Build ASCII table from headers and rows."""
        if not rows:
            return ""

        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(cell))

        # Build header row
        header_row = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        separator = "-+-".join("-" * w for w in col_widths)

        # Build data rows
        data_rows = []
        for row in rows:
            data_row = " | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row))
            data_rows.append(data_row)

        # Combine
        return "\n".join([header_row, separator] + data_rows)

    def _format_card(self, items: list[dict[str, Any]], result_type: str) -> str:
        """Format items as detailed cards."""
        cards = []

        for item in items:
            card_lines = []

            if result_type == "contacts":
                # Format contact card
                card_lines.append(f"Name: {item.get('name', 'Unknown')}")
                if "email" in item:
                    card_lines.append(f"Email: {item['email']}")
                if "location" in item:
                    card_lines.append(f"Location: {item['location']}")
                if "phone" in item:
                    card_lines.append(f"Phone: {item['phone']}")
                if "company" in item:
                    card_lines.append(f"Company: {item['company']}")
                if "tags" in item and item["tags"]:
                    tags_str = ", ".join(item["tags"])
                    card_lines.append(f"Tags: {tags_str}")
            elif result_type == "relationships":
                # Format relationship card
                card_lines.append(f"From: {item.get('from_contact', 'Unknown')}")
                card_lines.append(f"To: {item.get('to_contact', 'Unknown')}")
                card_lines.append(f"Type: {item.get('type', 'Unknown')}")
                if "start_date" in item:
                    card_lines.append(f"Started: {item['start_date']}")
                if "end_date" in item:
                    card_lines.append(f"Ended: {item['end_date']}")
            elif result_type == "notes":
                # Format note card
                card_lines.append(f"Title: {item.get('title', 'Untitled')}")
                if "date" in item:
                    card_lines.append(f"Date: {item['date']}")
                if "content" in item:
                    card_lines.append(f"\n{item['content']}")
            else:
                # Generic card
                for key, value in item.items():
                    card_lines.append(f"{key.capitalize()}: {value}")

            cards.append("\n".join(card_lines))

        # Join cards with separator
        return "\n---\n".join(cards)

    def _format_compact(
        self, items: list[dict[str, Any]], result_type: str, style: str | None
    ) -> str:
        """Format items in compact mode."""
        if style == "lines":
            # One line per item
            lines = []
            for item in items:
                lines.append(self._format_item_one_line(item, result_type))
            return "\n".join(lines)
        else:
            # Comma-separated (default compact)
            names = []
            for item in items:
                if result_type == "contacts":
                    names.append(item.get("name", "Unknown"))
                elif result_type == "relationships":
                    names.append(f"{item.get('from_contact', '?')} → {item.get('to_contact', '?')}")
                elif result_type == "notes":
                    names.append(item.get("title", "Untitled"))
                elif result_type == "tags":
                    names.append(item.get("name", "Unknown"))
                else:
                    names.append(str(item.get("name", item.get("id", "?"))))

            return ", ".join(names)

    def _format_item_one_line(self, item: dict[str, Any], result_type: str) -> str:
        """Format single item as one line summary."""
        if result_type == "contacts":
            name = item.get("name", "Unknown")
            email = item.get("email", "")
            location = item.get("location", "")
            parts = [name]
            if email:
                parts.append(f"({email})")
            if location:
                parts.append(f"- {location}")
            return " ".join(parts)
        elif result_type == "relationships":
            from_contact = item.get("from_contact", "?")
            to_contact = item.get("to_contact", "?")
            rel_type = item.get("type", "")
            return f"{from_contact} → {to_contact} ({rel_type})"
        elif result_type == "notes":
            title = item.get("title", "Untitled")
            date = item.get("date", "")
            if date:
                return f"{title} - {date}"
            return title
        elif result_type == "tags":
            name = item.get("name", "Unknown")
            label = item.get("label", "")
            if label and label != name:
                return f"{name} ({label})"
            return name
        else:
            # Generic fallback
            return str(item.get("name", item.get("id", "Item")))

    def _format_contact_one_line(self, contact: dict[str, Any]) -> str:
        """Format contact as one-line summary (helper for testing)."""
        return self._format_item_one_line(contact, "contacts")

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length with ellipsis.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text with "..." if longer than max_length
        """
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."
