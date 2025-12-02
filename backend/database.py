from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector
from datetime import datetime
from config import DATABASE_URL, EMBEDDING_DIMENSION

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class WebPage(Base):
    """Model to store scraped web page content and embeddings"""
    __tablename__ = "web_pages"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), unique=True, nullable=False, index=True)
    title = Column(String(512))
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIMENSION))
    scraped_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WebPage(id={self.id}, url={self.url[:50]}...)>"


def init_db():
    """Initialize the database and create tables"""
    # Create pgvector extension if it doesn't exist
    with engine.connect() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
