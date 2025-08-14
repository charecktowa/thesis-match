from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Usar localhost cuando no estamos en Docker, database cuando estamos en Docker
host = os.getenv("DB_HOST", "localhost")
SQL_ALCHEMY_DATABASE_URL = f"postgresql://user:password@{host}:5432/thesis_match_db"

engine = create_engine(SQL_ALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
