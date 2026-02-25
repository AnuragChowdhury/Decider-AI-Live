import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

# Load from specific backend .env to be sure
load_dotenv(dotenv_path="e:\\Decider AI\\Backend\\.env")

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3306")

print(f"Connecting to {DB_HOST}...")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("SUCCESS: Connected to database.")
    print(f"Tables found: {tables}")
    
    if "sessions" in tables and "chat_messages" in tables:
        print("VERIFICATION PASSED: Core tables exist.")
    else:
        print("VERIFICATION FAILED: Core tables missing.")

except Exception as e:
    print(f"CONNECTION ERROR: {e}")
