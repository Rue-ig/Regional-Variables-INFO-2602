# PATH: app/database.py
import logging
from sqlmodel import SQLModel, Session, create_engine
from app.config import get_settings
from contextlib import contextmanager

logger = logging.getLogger(__name__)

uri = get_settings().database_uri
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    uri,
    echo=get_settings().env.lower() in ["dev", "development", "test", "testing", "staging"],
    pool_size=get_settings().db_pool_size,
    max_overflow=get_settings().db_additional_overflow,
    pool_timeout=get_settings().db_pool_timeout,
    pool_recycle=get_settings().db_pool_recycle,
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def drop_all():
    SQLModel.metadata.drop_all(bind=engine)

def get_session():
    with Session(engine) as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()


@contextmanager
def get_cli_session():
    with Session(engine) as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()