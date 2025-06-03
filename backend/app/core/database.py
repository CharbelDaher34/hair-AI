from sqlmodel import create_engine, SQLModel
from sqlalchemy import inspect
from models.models import target_metadata  # Import metadata to ensure all models are registered
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_SERVER')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
print(DATABASE_URL)
engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    target_metadata.drop_all(engine)
    target_metadata.create_all(engine)

def check_db_tables():
    """
    Checks if all tables defined in SQLModel metadata exist in the database.
    Returns a tuple: (all_exist: bool, missing_tables: list)
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    expected_tables = set(target_metadata.tables.keys())
    missing_tables = list(expected_tables - existing_tables)
    all_exist = len(missing_tables) == 0
    return all_exist, missing_tables

def get_session():
    from sqlmodel import Session
    with Session(engine) as session:
        yield session
