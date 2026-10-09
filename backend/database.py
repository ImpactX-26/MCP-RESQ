"""MCP-ResQ — Consolidated Database Module.

Handles SQLite connection, SQLAlchemy session management, table lifecycle, and utilities.
"""

import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Database path configuration
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "mcp_resq.db"))
DATABASE_URL = f"sqlite:///{DB_PATH}"

# SQLAlchemy Engine & Session
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base for ORM Models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database sessions with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(force: bool = False) -> None:
    """Initialize database tables. Drops existing tables if force=True."""
    if force:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
