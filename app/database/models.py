"""
SQLAlchemy 데이터베이스 모델 정의
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .connection import Base
from ..entities.base import UserRole, ServiceType, ServiceRequestStatus, DayOfWeek, PersonalityType
import enum

# User 모델
class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), unique=True, index=True, nullable=False)  # UUID
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=False)
    birth_date = Column(String(10), nullable=True)  # YYYY-MM-DD
    user_role = Column(SQLEnum(UserRole), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    service_requests = relationship("ServiceRequestModel", back_populates="user")
    caregiver = relationship("CaregiverModel", back_populates="user", uselist=False)

# Center 모델
class CenterModel(Base):
    __tablename__ = "centers"
    
    id = Column(Integer, primary_key=True, index=True)
    center_id = Column(String(36), unique=True, index=True, nullable=False)  # UUID
    name = Column(String(200), nullable=False)
    address = Column(String(500), nullable=True)
    location = Column(JSON, nullable=True)  # [latitude, longitude]
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    caregivers = relationship("CaregiverModel", back_populates="center")

# Caregiver 모델
class CaregiverModel(Base):
    __tablename__ = "caregivers"
    
    id = Column(Integer, primary_key=True, index=True)
    caregiver_id = Column(String(36), unique=True, index=True, nullable=False)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    center_id = Column(Integer, ForeignKey("centers.id"), nullable=True)
    available_start_time = Column(String(5), nullable=True)  # HH:MM
    available_end_time = Column(String(5), nullable=True)   # HH:MM
    address = Column(String(500), nullable=True)
    location = Column(JSON, nullable=True)  # [latitude, longitude]
    service_types = Column(JSON, nullable=True)  # List[ServiceType]
    days_off = Column(JSON, nullable=True)  # List[DayOfWeek]
    personality_type = Column(SQLEnum(PersonalityType), nullable=True)
    career_years = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    user = relationship("UserModel", back_populates="caregiver")
    center = relationship("CenterModel", back_populates="caregivers")

# ServiceRequest 모델
class ServiceRequestModel(Base):
    __tablename__ = "service_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    service_request_id = Column(String(36), unique=True, index=True, nullable=False)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    address = Column(String(500), nullable=False)
    location = Column(JSON, nullable=False)  # [latitude, longitude]
    preferred_time_start = Column(DateTime(timezone=True), nullable=True)
    preferred_time_end = Column(DateTime(timezone=True), nullable=True)
    service_type = Column(String(50), nullable=False)  # ServiceType as string
    status = Column(SQLEnum(ServiceRequestStatus), nullable=False)
    personality_type = Column(String(50), nullable=False)  # PersonalityType as string
    requested_days = Column(JSON, nullable=False)  # List[int] (1-7)
    additional_information = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    user = relationship("UserModel", back_populates="service_requests")