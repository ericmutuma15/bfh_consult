from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Patient schemas
class PatientCreate(BaseModel):
    name: str
    email: str | None = None
    gender: str | None = None
    location: str | None = None

class PatientOut(PatientCreate):
    id: str
    created_at: datetime

# Consultation Request schemas
class ConsultationRequestCreate(BaseModel):
    patient_id: str
    issue: str
    details: str

class ConsultationRequestOut(ConsultationRequestCreate):
    id: str
    fee_amount: int
    payment_status: str
    requested_at: datetime

# Assignment schemas
class AssignmentCreate(BaseModel):
    request_id: str
    head_doctor_id: str
    assigned_doctor_id: str

class AssignmentOut(AssignmentCreate):
    id: str
    assigned_at: datetime

# User schemas
class UserCreate(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    phone: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    name: Optional[str]
    email: EmailStr
    phone: str
    is_verified: bool
    created_at: datetime
    class Config:
        orm_mode = True

# OTP schemas
class OTPRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    type: str  # 'email' or 'phone'

class OTPVerify(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    code: str
    type: str

# Service schemas
class ServiceOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    price: int
    created_at: datetime
    class Config:
        from_attributes = True

# Doctor schemas
class DoctorSignup(BaseModel):
    name: str
    email: EmailStr
    phone: str
    gender: str
    specialty: str

class DoctorProfileUpdate(BaseModel):
    qualifications: str
    evidence_url: str
    kmpdc_license: str

class DoctorApproval(BaseModel):
    doctor_id: str
    approval_status: str  # 'approved' or 'rejected'
    approval_notes: str = ''

class DoctorOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: str
    gender: str
    specialty: str
    qualifications: str | None = None
    evidence_url: str | None = None
    kmpdc_license: str | None = None
    approval_status: str
    approval_notes: str | None = None
    is_approved: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Appointment schemas (updated)
class AppointmentCreate(BaseModel):
    doctor_id: str
    service_id: str
    gender: str
    symptoms: str
    details: str

class AppointmentOut(BaseModel):
    id: str
    user_id: str
    doctor_id: str
    service_id: str
    gender: str
    symptoms: str
    details: str
    status: str
    payment_status: str
    created_at: datetime
    class Config:
        from_attributes = True
