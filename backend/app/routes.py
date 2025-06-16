from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import schemas, daraja, models
from .__init__ import SessionLocal, init_db
from datetime import datetime

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.on_event("startup")
def on_startup():
    init_db()

@router.post("/patients/", response_model=schemas.PatientOut)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    db_patient = models.Patient(
        name=patient.name,
        email=patient.email,
        gender=patient.gender,
        location=patient.location,
        created_at=datetime.utcnow()
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@router.post("/consultations/", response_model=schemas.ConsultationRequestOut)
def create_consultation(req: schemas.ConsultationRequestCreate, db: Session = Depends(get_db)):
    db_consult = models.ConsultationRequest(
        patient_id=req.patient_id,
        issue=req.issue,
        details=req.details,
        requested_at=datetime.utcnow()
    )
    db.add(db_consult)
    db.commit()
    db.refresh(db_consult)
    return db_consult

@router.post("/payments/stkpush/")
def pay(phone_number: str, amount: int):
    return daraja.initiate_stk_push(phone_number, amount)

@router.post("/assignments/", response_model=schemas.AssignmentOut)
def assign_doctor(assignment: schemas.AssignmentCreate, db: Session = Depends(get_db)):
    db_assignment = models.Assignment(
        request_id=assignment.request_id,
        head_doctor_id=assignment.head_doctor_id,
        assigned_doctor_id=assignment.assigned_doctor_id,
        assigned_at=datetime.utcnow()
    )
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment
