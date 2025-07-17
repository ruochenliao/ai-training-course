# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define the database URL. Uses SQLite for simplicity.
# In a real application, use environment variables for sensitive data.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecommerce.db")

# Create the SQLAlchemy engine
# connect_args is specific to SQLite for allowing multithreaded access
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    """
    Dependency function that provides a database session per request.
    Ensures the session is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db # Provide the session to the route
    finally:
        db.close() # Close the session
