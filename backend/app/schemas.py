from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PatientCreate(BaseModel):
    name: str
    email: str | None = None
    gender: str | None = None
    location: str | None = None

class PatientOut(PatientCreate):
    id: str
    created_at: datetime

class ConsultationRequestCreate(BaseModel):
    patient_id: str
    issue: str
    details: str

class ConsultationRequestOut(ConsultationRequestCreate):
    id: str
    fee_amount: int
    payment_status: str
    requested_at: datetime

class AssignmentCreate(BaseModel):
    request_id: str
    head_doctor_id: str
    assigned_doctor_id: str

class AssignmentOut(AssignmentCreate):
    id: str
    assigned_at: datetime
