"""
SQLAlchemy ORM 모델 정의
Spring Boot 데이터베이스 스키마에 맞는 읽기 전용 모델
"""

from sqlalchemy import Column, String, Integer, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID

# SQLAlchemy Base 모델
Base = declarative_base()

class Caregiver(Base):
    """
    요양보호사 ORM 모델
    Spring Boot의 caregiver 테이블 스키마에 맞춤
    """
    __tablename__ = "caregiver"
    
    caregiver_id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String, nullable=True)
    address = Column(String, nullable=True)
    address_type = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    career = Column(Integer, nullable=True)
    korean_proficiency = Column(String, nullable=True)
    is_accompany_outing = Column(Boolean, nullable=True)
    self_introduction = Column(String, nullable=True)
    verified_status = Column(String, nullable=False, default="PENDING")
    service_type = Column(String, nullable=True)
    
    # 관계 설정
    preferences = relationship("CaregiverPreference", back_populates="caregiver", uselist=False)

class CaregiverPreference(Base):
    """
    요양보호사 선호도 ORM 모델
    Spring Boot의 caregiver_preference 테이블 스키마에 맞춤
    """
    __tablename__ = "caregiver_preference"
    
    caregiver_preference_id = Column(UUID(as_uuid=True), primary_key=True)
    caregiver_id = Column(UUID(as_uuid=True), ForeignKey("caregiver.caregiver_id"), nullable=False)
    day_of_week = Column(String, nullable=True)  # JSON 문자열로 저장됨
    work_start_time = Column(String, nullable=True)
    work_end_time = Column(String, nullable=True)
    work_min_time = Column(Integer, nullable=True)
    work_max_time = Column(Integer, nullable=True)
    available_time = Column(String, nullable=True)
    work_area = Column(String, nullable=True)
    transportation = Column(String, nullable=True)
    lunch_break = Column(String, nullable=True)
    buffer_time = Column(String, nullable=True)
    supported_conditions = Column(String, nullable=True)  # JSON 문자열로 저장됨
    preferred_min_age = Column(Integer, nullable=True)
    preferred_max_age = Column(Integer, nullable=True)
    preferred_gender = Column(String, nullable=True)
    service_types = Column(String, nullable=True)  # JSON 문자열로 저장됨
    
    # 관계 설정
    caregiver = relationship("Caregiver", back_populates="preferences")

class ServiceRequest(Base):
    """
    서비스 요청 ORM 모델
    Spring Boot의 service_request 테이블 스키마에 맞춤
    """
    __tablename__ = "service_request"
    
    service_request_id = Column(UUID(as_uuid=True), primary_key=True)
    consumer_id = Column(UUID(as_uuid=True), nullable=False)
    service_address = Column(String, nullable=False)
    address_type = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    preferred_start_time = Column(String, nullable=True)
    preferred_end_time = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)
    service_type = Column(String, nullable=True)
    request_status = Column(String, nullable=True)
    request_date = Column(String, nullable=True)
    additional_information = Column(String, nullable=True)

class ServiceMatch(Base):
    """
    서비스 매칭 ORM 모델
    Spring Boot의 service_match 테이블 스키마에 맞춤
    """
    __tablename__ = "service_match"
    
    service_match_id = Column(UUID(as_uuid=True), primary_key=True)
    service_request_id = Column(UUID(as_uuid=True), ForeignKey("service_request.service_request_id"), nullable=False)
    caregiver_id = Column(UUID(as_uuid=True), ForeignKey("caregiver.caregiver_id"), nullable=False)
    match_status = Column(String, nullable=True)
    service_time = Column(String, nullable=True)
    service_date = Column(String, nullable=True)