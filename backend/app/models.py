from sqlalchemy import Column, String, Enum, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime

Base = declarative_base()

class PaymentStatus(enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"

class OTPType(enum.Enum):
    email = "email"
    phone = "phone"

class UserRole(enum.Enum):
    patient = "patient"
    doctor = "doctor"
    superuser = "superuser"

class Patient(Base):
    __tablename__ = "patients"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    location = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

class ConsultationRequest(Base):
    __tablename__ = "consultation_requests"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"))
    issue = Column(String, nullable=False)
    details = Column(String)
    fee_amount = Column(Integer, default=1000)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    requested_at = Column(DateTime, default=lambda: datetime.utcnow())

class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String, ForeignKey("consultation_requests.id"))
    head_doctor_id = Column(String)
    assigned_doctor_id = Column(String)
    assigned_at = Column(DateTime, default=lambda: datetime.utcnow())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.patient)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    appointments = relationship("Appointment", back_populates="user")

class OTP(Base):
    __tablename__ = "otps"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    code = Column(String, nullable=False)
    type = Column(Enum(OTPType), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)

class Service(Base):
    __tablename__ = "services"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    gender = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    qualifications = Column(String, nullable=True)
    evidence_url = Column(String, nullable=True)
    kmpdc_license = Column(String, nullable=True)
    approval_status = Column(String, default="pending")  # pending/approved/rejected
    approval_notes = Column(String, nullable=True)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    doctor_id = Column(String, ForeignKey("doctors.id"))
    service_id = Column(String, ForeignKey("services.id"))
    gender = Column(String, nullable=True)
    symptoms = Column(String, nullable=True)
    details = Column(String, nullable=True)
    status = Column(String, default="pending")
    payment_status = Column(String, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    user = relationship("User", back_populates="appointments")
