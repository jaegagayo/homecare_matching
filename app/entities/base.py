from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional
from datetime import datetime, date
from enum import Enum
import re

# Enum 정의들
class UserRole(str, Enum):
    ROLE_CONSUMER = "ROLE_CONSUMER"
    ROLE_CAREGIVER = "ROLE_CAREGIVER"
    ROLE_CENTER = "ROLE_CENTER"
    ROLE_ADMIN = "ROLE_ADMIN"

class ServiceType(str, Enum):
    VISITING_CARE = "방문요양"
    VISITING_BATH = "방문목욕"
    VISITING_NURSING = "방문간호"
    DAY_NIGHT_CARE = "주야간보호"
    RESPITE_CARE = "단기보호"

class ServiceRequestStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    COMPLETED = "COMPLETED"

class DayOfWeek(str, Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"

class PersonalityType(str, Enum):
    GENTLE = "GENTLE"    # 온화한
    CALM = "CALM"        # 차분한  
    CHEERFUL = "CHEERFUL" # 명랑한
    ACTIVE = "ACTIVE"    # 활동적인