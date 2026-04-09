from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    version = Column(Integer)
    filepath = Column(String)
    student_name = Column(String) 
    comment = Column(String)  
    uploaded_at = Column(DateTime, default=datetime.utcnow)