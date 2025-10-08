#!/usr/bin/env python3
"""Database migration to add custom template fields to users table."""

import sqlite3
import os

def migrate_database():
    """Add custom template fields to users table."""
    db_path = 'data/outreach.db'

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]

        # Add custom_initial_template column if it doesn't exist
        if 'custom_initial_template' not in columns:
            print("Adding custom_initial_template column...")
            cursor.execute("ALTER TABLE users ADD COLUMN custom_initial_template TEXT")
            print("✅ Added custom_initial_template column")
        else:
            print("⏭️  custom_initial_template column already exists")

        # Add custom_followup_template column if it doesn't exist
        if 'custom_followup_template' not in columns:
            print("Adding custom_followup_template column...")
            cursor.execute("ALTER TABLE users ADD COLUMN custom_followup_template TEXT")
            print("✅ Added custom_followup_template column")
        else:
            print("⏭️  custom_followup_template column already exists")

        # Add use_custom_templates column if it doesn't exist
        if 'use_custom_templates' not in columns:
            print("Adding use_custom_templates column...")
            cursor.execute("ALTER TABLE users ADD COLUMN use_custom_templates BOOLEAN DEFAULT 0")
            print("✅ Added use_custom_templates column")
        else:
            print("⏭️  use_custom_templates column already exists")

        conn.commit()
        print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
