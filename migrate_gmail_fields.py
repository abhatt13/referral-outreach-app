"""Database migration script to add Gmail authentication fields."""

import sqlite3
import os

def migrate_database():
    """Add Gmail authentication fields to users table."""
    db_path = 'data/outreach.db'

    if not os.path.exists(db_path):
        print("No existing database found.")
        return

    print("Migrating database to add Gmail authentication fields...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if gmail_token column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'gmail_token' not in columns:
            print("Adding gmail_token column...")
            cursor.execute("ALTER TABLE users ADD COLUMN gmail_token TEXT")
            print("✅ gmail_token column added")
        else:
            print("✅ gmail_token column already exists")

        if 'gmail_authenticated' not in columns:
            print("Adding gmail_authenticated column...")
            cursor.execute("ALTER TABLE users ADD COLUMN gmail_authenticated BOOLEAN DEFAULT 0")
            print("✅ gmail_authenticated column added")
        else:
            print("✅ gmail_authenticated column already exists")

        conn.commit()
        print("\n✅ Database migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error during migration: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
