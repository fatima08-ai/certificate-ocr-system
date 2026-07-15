from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./certificates.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class CertificateRecord(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    candidate_name = Column(String, nullable=True)
    certificate_title = Column(String, nullable=True)
    organization = Column(String, nullable=True)
    issue_date = Column(String, nullable=True)
    certificate_number = Column(String, nullable=True)
    confidence = Column(String, nullable=True)
    raw_text = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()