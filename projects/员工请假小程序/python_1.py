from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base

class LeaveRequest(Base):
    __tablename__ = 'leave_requests'
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey('users.id'))
    reason = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String, default='pending')  # ['pending', 'approved', 'rejected']

    employee = relationship("User", back_populates="leave_requests")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    role = Column(String)  # ['employee', 'manager', 'admin']
    
    leave_requests = relationship("LeaveRequest", back_populates="employee")
