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

# User schemas (for superusers only)
class SuperuserCreate(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    phone: str
    password: str

class SuperuserOut(BaseModel):
    id: str
    name: Optional[str]
    email: EmailStr
    phone: str
    is_verified: bool
    created_at: datetime
    class Config:
        orm_mode = True

# Patient signup schemas
class PatientSignup(BaseModel):
    name: str
    email: EmailStr
    phone: str
    gender: Optional[str] = None
    location: Optional[str] = None
    password: str

class PatientLogin(BaseModel):
    email: EmailStr
    password: str

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

class DoctorCertificateOut(BaseModel):
    id: str
    title: str
    file_path: str
    uploaded_at: datetime
    class Config:
        orm_mode = True

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
    certificates: list[DoctorCertificateOut] = []
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

# Add a unified login response schema
class LoginResponse(BaseModel):
    role: str  # 'superuser', 'doctor', 'patient'
    token: str
    user: dict  # PatientOut, DoctorOut, or SuperuserOut

class UserOut(BaseModel):
    id: str
    name: Optional[str]
    email: EmailStr
    phone: str
    is_verified: bool
    role: str
    created_at: datetime
    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    phone: str
    password: str
    role: str = "patient"  # 'superuser', 'doctor', 'patient'

# Payment schemas
class AppointmentPaymentRequest(BaseModel):
    appointment_id: str
    phone_number: str

class NotificationOut(BaseModel):
    id: str
    user_id: Optional[str]
    message: str
    type: Optional[str]
    is_read: bool
    created_at: datetime
    class Config:
        orm_mode = True

class NotificationCreate(BaseModel):
    user_id: Optional[str] = None
    message: str
    type: Optional[str] = None
