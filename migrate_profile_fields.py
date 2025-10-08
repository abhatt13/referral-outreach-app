#!/usr/bin/env python3
"""Database migration to add profile fields to users table."""

import sqlite3
import os

def migrate_database():
    """Add profile fields to users table."""
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

        # Add profile_completed column if it doesn't exist
        if 'profile_completed' not in columns:
            print("Adding profile_completed column...")
            cursor.execute("ALTER TABLE users ADD COLUMN profile_completed BOOLEAN DEFAULT 0")
            print("✅ Added profile_completed column")
        else:
            print("⏭️  profile_completed column already exists")

        # Add profile_name column if it doesn't exist
        if 'profile_name' not in columns:
            print("Adding profile_name column...")
            cursor.execute("ALTER TABLE users ADD COLUMN profile_name VARCHAR(200)")
            print("✅ Added profile_name column")
        else:
            print("⏭️  profile_name column already exists")

        # Add profile_email column if it doesn't exist
        if 'profile_email' not in columns:
            print("Adding profile_email column...")
            cursor.execute("ALTER TABLE users ADD COLUMN profile_email VARCHAR(200)")
            print("✅ Added profile_email column")
        else:
            print("⏭️  profile_email column already exists")

        # Add profile_linkedin column if it doesn't exist
        if 'profile_linkedin' not in columns:
            print("Adding profile_linkedin column...")
            cursor.execute("ALTER TABLE users ADD COLUMN profile_linkedin VARCHAR(500)")
            print("✅ Added profile_linkedin column")
        else:
            print("⏭️  profile_linkedin column already exists")

        conn.commit()
        print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
