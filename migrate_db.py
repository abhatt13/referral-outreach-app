"""Database migration script to add authentication tables and update schema."""

import sqlite3
import os

def migrate_database():
    """Migrate existing database to new schema with authentication."""
    db_path = 'data/outreach.db'

    if not os.path.exists(db_path):
        print("No existing database found. New database will be created on first run.")
        return

    print("Migrating database to new schema...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        users_exists = cursor.fetchone() is not None

        if not users_exists:
            print("Creating users table...")
            cursor.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    email VARCHAR(200) NOT NULL UNIQUE,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    password_hash VARCHAR(200) NOT NULL,
                    tier VARCHAR(50) DEFAULT 'FREE',
                    emails_sent_count INTEGER DEFAULT 0,
                    campaigns_count INTEGER DEFAULT 0,
                    stripe_customer_id VARCHAR(200),
                    subscription_active BOOLEAN DEFAULT 0,
                    subscription_ends_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME
                )
            """)
            print("✅ Users table created")
        else:
            print("✅ Users table already exists")

        # Check if user_id column exists in email_campaigns
        cursor.execute("PRAGMA table_info(email_campaigns)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'user_id' not in columns:
            print("Adding user_id column to email_campaigns...")
            # SQLite doesn't support adding foreign keys to existing tables easily
            # We'll add the column without the foreign key constraint
            cursor.execute("ALTER TABLE email_campaigns ADD COLUMN user_id INTEGER")
            print("✅ user_id column added to email_campaigns")
        else:
            print("✅ user_id column already exists in email_campaigns")

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
