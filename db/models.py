from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Students(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    time = Column(DateTime, default=func.now())

    feedback = relationship("Feedback", back_populates="student")

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    category = Column(String)
    message = Column(String)
    time = Column(DateTime, default=func.now())

    student = relationship("Students", back_populates="feedback")