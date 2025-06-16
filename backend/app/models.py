from sqlalchemy import Column, String, Enum, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import uuid
import enum
from datetime import datetime

Base = declarative_base()

class PaymentStatus(enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"

class Patient(Base):
    __tablename__ = "patients"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    location = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ConsultationRequest(Base):
    __tablename__ = "consultation_requests"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"))
    issue = Column(String, nullable=False)
    details = Column(String)
    fee_amount = Column(Integer, default=1000)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    requested_at = Column(DateTime, default=datetime.utcnow)

class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String, ForeignKey("consultation_requests.id"))
    head_doctor_id = Column(String)
    assigned_doctor_id = Column(String)
    assigned_at = Column(DateTime, default=datetime.utcnow)
