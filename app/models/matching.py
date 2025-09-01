"""
SQLAlchemy ORM 모델 정의 - 읽기 전용

⚠️  중요: 책임 분리
- 이 파일은 읽기 전용 데이터베이스 모델만 포함합니다.
- 초기화 마이그레이션 및 쓰기 작업은 matching-backend (Spring Boot)에서 처리합니다.
- DB 스키마는 Spring Boot의 엔티티를 기준으로 하며, 아직 수정 중이기 때문에 ERD를 기반으로 작성되었습니다. (2025-09-01 기준)

참고사항:
- model에 맞춰 실제 DB 데이터를 조회하는 작업은 `caregiver_repository.py`에 작성되어야 합니다.
"""

from sqlalchemy import Column, String, Integer, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID

# SQLAlchemy Base 모델
Base = declarative_base()

class Caregiver(Base):
    """
    요양보호사 ORM 모델 - ERD 스키마에 맞춘 버전
    실제 ERD와 달라지는 부분: UUID 외에 숫자 ID도 primary key로 존재
    """
    __tablename__ = "caregiver"
    
    id = Column(Integer, primary_key=True)  # 실제 DB의 primary key (ERD에는 없지만 존재)
    caregiver_id = Column(UUID(as_uuid=True), nullable=False)  # ERD의 UUID 필드
    user_id = Column(Integer, nullable=False)  # ERD: user_id
    address = Column(String, nullable=True)  # ERD: address
    career = Column(Integer, nullable=True)  # ERD: career
    korean_proficiency = Column(String, nullable=True)  # ERD: korean_proficiency
    is_accompany_outing = Column(Boolean, nullable=True)  # ERD: is_accompany_outing
    self_introduction = Column(String, nullable=True)  # ERD: self_introduction
    verified_status = Column(String, nullable=False, default="PENDING")  # ERD: verified_status
    
    # 관계 설정
    preferences = relationship("CaregiverPreference", back_populates="caregiver", uselist=False)

class CaregiverPreference(Base):
    """
    요양보호사 선호도 ORM 모델 - ERD 스키마에 맞춘 버전
    실제 ERD와 달라지는 부분: UUID 외에 숫자 ID도 primary key로 존재
    """
    __tablename__ = "caregiver_preference"
    
    id = Column(Integer, primary_key=True)  # 실제 DB의 primary key (ERD에는 없지만 존재)
    caregiver_preference_id = Column(UUID(as_uuid=True), nullable=False)  # ERD의 UUID 필드
    caregiver_id = Column(Integer, ForeignKey("caregiver.id"), nullable=False)  # caregiver.id 참조
    day_of_week = Column(String, nullable=True)  # JSON 문자열로 저장됨
    work_start_time = Column(String, nullable=True)  # time 타입을 String으로 처리
    work_end_time = Column(String, nullable=True)  # time 타입을 String으로 처리
    work_min_time = Column(Integer, nullable=True)
    work_max_time = Column(Integer, nullable=True)
    available_time = Column(Integer, nullable=True)
    work_area = Column(String, nullable=True)
    address_type = Column(String, nullable=True)  # ERD에 정의된 필드
    location = Column(String, nullable=True)  # ERD의 위치 정보 "latitude,longitude"
    transportation = Column(String, nullable=True)
    lunch_break = Column(Integer, nullable=True)
    buffer_time = Column(Integer, nullable=True)  # 방문일정 사이 버퍼 간격
    supported_conditions = Column(String, nullable=True)  # 치매, 와상 두 종류
    preferred_min_age = Column(Integer, nullable=True)
    preferred_max_age = Column(Integer, nullable=True)
    preferred_gender = Column(String, nullable=True)
    service_types = Column(String, nullable=True)  # JSON 문자열로 저장됨
    
    # 관계 설정 (caregiver.id를 참조)
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