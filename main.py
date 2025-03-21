from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "sqlite:///./logs.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

API_KEYS = {"your-secure-api-key"}  # Replace with a secure storage method

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")

class LogEntry(Base):
    __tablename__ = "logs"
    id = Column(String, primary_key=True, index=True)
    level = Column(String, index=True)
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class LogEntryCreate(BaseModel):
    level: str
    message: str
    timestamp: datetime = datetime.utcnow()

@app.post("/logs/")
def post_log(entry: LogEntryCreate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    log = LogEntry(level=entry.level, message=entry.message, timestamp=entry.timestamp)
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"message": "Log saved", "log": log}

@app.get("/logs/", response_model=List[LogEntryCreate])
def get_logs(db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    return db.query(LogEntry).all()

@app.get("/logs/{level}", response_model=List[LogEntryCreate])
def get_logs_by_level(level: str, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    filtered_logs = db.query(LogEntry).filter(LogEntry.level == level).all()
    if not filtered_logs:
        raise HTTPException(status_code=404, detail="No logs found for this level")
    return filtered_logs
