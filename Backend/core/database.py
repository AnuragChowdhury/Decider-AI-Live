from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "decider_ai")

# 1. Database Initialization with fallback
def initialize_engine():
    SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    ROOT_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
    
    # Try MySQL first with a short timeout
    try:
        print(">>> [DB] Attempting MySQL connection...", flush=True)
        # Check/Create DB
        temp_engine = create_engine(ROOT_URL, connect_args={"connect_timeout": 5})
        with temp_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
        temp_engine.dispose()
        
        # Main Engine
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20,
            connect_args={"connect_timeout": 5}
        )
        # Verify connection
        with engine.connect() as conn:
            print(">>> [DB] MySQL Connected.", flush=True)
            return engine, False # engine, is_sqlite
            
    except Exception as e:
        print(f"!!! [DB] MySQL connection failed: {e}. Falling back to SQLite.", flush=True)
        SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
        return engine, True

engine, is_sqlite = initialize_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
