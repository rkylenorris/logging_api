from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import secrets
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "sqlite:///./logs.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

class APIKey(Base):
    __tablename__ = "api_keys"
    key = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now())

class LogEntry(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    process_name = Column(String, index=True)
    level = Column(String, index=True)
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.now())
    
    def __init__(self, process_name: str, level: str, message: str, timestamp: datetime = datetime.now()):
        self.process_name = process_name
        self.level = level
        self.message = message
        self.timestamp = timestamp
    
    def __repr__(self):
        return f"<LogEntry(process_name={self.process_name}, level={self.level}, message={self.message}, timestamp={self.timestamp})>"

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_api_key(x_api_key: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not x_api_key or not db.query(APIKey).filter(APIKey.key == x_api_key).first():
        raise HTTPException(status_code=401, detail="Invalid API key")

class LogEntryCreate(BaseModel):
    process_name: str
    level: str
    message: str
    timestamp: datetime = datetime.now()

class APIKeyResponse(BaseModel):
    key: str

@app.post("/keys/", response_model=APIKeyResponse)
def create_api_key(db: Session = Depends(get_db)):
    new_key = secrets.token_hex(32)
    api_key = APIKey(key=new_key)
    db.add(api_key)
    db.commit()
    return {"key": new_key}

@app.post("/logs/")
def post_log(entry: LogEntryCreate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    log = LogEntry(process_name=entry.process_name, level=entry.level, message=entry.message, timestamp=entry.timestamp)
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


@app.get("/logs/process/{process_name}", response_model=List[LogEntryCreate])
def get_logs_by_process_name(process_name: str, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    filtered_logs = db.query(LogEntry).filter(LogEntry.process_name == process_name).all()
    if not filtered_logs:
        raise HTTPException(status_code=404, detail="No logs found for this process name")
    return filtered_logs


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)