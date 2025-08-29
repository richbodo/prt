#!/usr/bin/env python3
"""
Extract profile images from the test fixture database.

This utility extracts the profile images stored in the test database
and saves them as individual JPEG files for inspection.
"""

import sqlite3
import sys
from pathlib import Path


def extract_profile_images(db_path, output_dir="extracted_images"):
    """Extract profile images from database and save to disk."""

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all contacts with profile images
    cursor.execute(
        """
        SELECT name, profile_image, profile_image_filename 
        FROM contacts 
        WHERE profile_image IS NOT NULL
    """
    )

    results = cursor.fetchall()

    if not results:
        print("No profile images found in database.")
        return

    print(f"Found {len(results)} profile images:")

    for name, image_data, filename in results:
        # Save image to disk
        output_file = output_path / filename
        with open(output_file, "wb") as f:
            f.write(image_data)

        size_kb = len(image_data) / 1024
        print(f"  {name}: {filename} ({size_kb:.1f} KB)")

    conn.close()
    print(f"\nImages extracted to: {output_path.resolve()}")


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)

    # Default to test fixture database
    default_db = Path(__file__).parent.parent / "tests" / "prt_data" / "test_fixtures.db"

    if len(sys.argv) > 1:
        db_path = Path(sys.argv[1])
    else:
        db_path = default_db

    if not db_path.exists():
        print(f"Database not found: {db_path}")
        print("Run 'cd tests && python fixtures.py' to create test database.")
        sys.exit(1)

    print(f"Extracting images from: {db_path}")
    extract_profile_images(db_path)
