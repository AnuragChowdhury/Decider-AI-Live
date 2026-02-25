"""
Migration: Adds is_verified to users and creates registration_otps table.
Safe to re-run.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.database import engine
from sqlalchemy import text, inspect

inspector = inspect(engine)
existing_tables = inspector.get_table_names()
existing_user_cols = {col["name"] for col in inspector.get_columns("users")}

with engine.connect() as conn:
    # 1. Add is_verified to users
    if "is_verified" not in existing_user_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE"))
        # Mark all existing users as verified so they aren't locked out
        conn.execute(text("UPDATE users SET is_verified = TRUE WHERE is_verified IS NULL OR is_verified = FALSE"))
        conn.commit()
        print("[OK] Added users.is_verified (existing users marked verified)")
    else:
        print("[SKIP] users.is_verified already exists")

    # 2. Create registration_otps table
    if "registration_otps" not in existing_tables:
        conn.execute(text("""
            CREATE TABLE registration_otps (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                token VARCHAR(10) NOT NULL,
                expires_at DATETIME NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        conn.commit()
        print("[OK] Created registration_otps table")
    else:
        print("[SKIP] registration_otps already exists")

print("\nMigration complete.")
