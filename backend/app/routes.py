from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from . import schemas, models, utils, daraja
from .__init__ import SessionLocal, init_db
from datetime import datetime, timedelta
from typing import List, Optional

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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = utils.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(models.User).filter(models.User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Auth endpoints
@router.post("/auth/signup", response_model=schemas.UserOut)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter((models.User.email == user.email) | (models.User.phone == user.phone)).first():
        raise HTTPException(status_code=400, detail="Email or phone already registered")
    role = models.UserRole.superuser if user.email == "ericmutuma15@gmail.com" else models.UserRole.patient
    db_user = models.User(
        name=user.name,
        email=user.email,
        phone=user.phone,
        password_hash=utils.hash_password(user.password),
        is_verified=False,
        role=role,
        created_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not utils.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = utils.create_access_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/auth/send-otp")
def send_otp(req: schemas.OTPRequest, db: Session = Depends(get_db)):
    user = None
    if req.email:
        user = db.query(models.User).filter(models.User.email == req.email).first()
    elif req.phone:
        user = db.query(models.User).filter(models.User.phone == req.phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    code = utils.generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    otp = models.OTP(user_id=user.id, code=code, type=req.type, expires_at=expires_at, is_used=False)
    db.add(otp)
    db.commit()
    utils.send_otp_stub(req.email or req.phone, code, req.type)
    return {"message": "OTP sent"}

@router.post("/auth/verify-otp")
def verify_otp(req: schemas.OTPVerify, db: Session = Depends(get_db)):
    user = None
    if req.email:
        user = db.query(models.User).filter(models.User.email == req.email).first()
    elif req.phone:
        user = db.query(models.User).filter(models.User.phone == req.phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    otp = db.query(models.OTP).filter(
        models.OTP.user_id == user.id,
        models.OTP.code == req.code,
        models.OTP.type == req.type,
        models.OTP.is_used == False,
        models.OTP.expires_at > datetime.utcnow()
    ).first()
    if not otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    otp.is_used = True
    user.is_verified = True
    db.commit()
    # Return JWT token for immediate login after verification
    token = utils.create_access_token({"sub": user.id})
    return {"message": "OTP verified", "access_token": token, "token_type": "bearer", "role": user.role.value}

# Profile endpoints
@router.get("/profile", response_model=schemas.UserOut)
def get_profile(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=schemas.UserOut)
def update_profile(update: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    current_user.name = update.name
    current_user.email = update.email
    current_user.phone = update.phone
    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/doctor/profile", response_model=schemas.DoctorOut)
def update_doctor_profile(update: schemas.DoctorProfileUpdate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # Find doctor by user email (assuming user is logged in as doctor)
    user = db.query(models.User).filter(models.User.id == utils.decode_access_token(token).get("sub")).first()
    doctor = db.query(models.Doctor).filter(models.Doctor.email == user.email).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor.qualifications = update.qualifications
    doctor.evidence_url = update.evidence_url
    doctor.kmpdc_license = update.kmpdc_license
    db.commit()
    db.refresh(doctor)
    return doctor

# Appointment endpoints
@router.post("/appointments", response_model=schemas.AppointmentOut)
def create_appointment(app: schemas.AppointmentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_app = models.Appointment(
        user_id=current_user.id,
        doctor_id=app.doctor_id,
        service_id=app.service_id,
        gender=app.gender,
        symptoms=app.symptoms,
        details=app.details,
        status="pending",
        payment_status="pending"
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app

@router.get("/appointments", response_model=list[schemas.AppointmentOut])
def list_appointments(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Appointment).filter(models.Appointment.user_id == current_user.id).all()

@router.post("/appointments/payment")
def appointment_payment(appointment_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    app = db.query(models.Appointment).filter(models.Appointment.id == appointment_id, models.Appointment.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Appointment not found")
    app.payment_status = "paid"
    db.commit()
    return {"message": "Payment processed (stub)"}

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

# Doctor/admin endpoints
@router.get("/admin/patients")
def get_patients(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.UserRole.doctor:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.User).filter(models.User.role == models.UserRole.patient).all()

@router.get("/admin/appointments")
def get_all_appointments(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.UserRole.doctor:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.Appointment).all()

@router.get("/services", response_model=List[schemas.ServiceOut])
def list_services(db: Session = Depends(get_db)):
    return db.query(models.Service).all()

@router.post("/admin/doctor-signup", response_model=schemas.DoctorOut)
def admin_doctor_signup(doctor: schemas.DoctorSignup, db: Session = Depends(get_db)):
    db_doctor = models.Doctor(
        name=doctor.name,
        email=doctor.email,
        phone=doctor.phone,
        gender=doctor.gender,
        specialty=doctor.specialty,
        is_approved=False
    )
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor

@router.get("/admin/pending-doctors", response_model=List[schemas.DoctorOut])
def list_pending_doctors(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.UserRole.superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.Doctor).filter(models.Doctor.approval_status == "pending").all()

@router.post("/admin/approve-doctor", response_model=schemas.DoctorOut)
def approve_doctor(data: schemas.DoctorApproval, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.UserRole.superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    doctor = db.query(models.Doctor).filter(models.Doctor.id == data.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor.approval_status = data.approval_status
    doctor.approval_notes = data.approval_notes
    doctor.is_approved = data.approval_status == "approved"
    db.commit()
    db.refresh(doctor)
    return doctor

@router.get("/doctor/profile", response_model=schemas.DoctorOut)
def get_doctor_profile(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = db.query(models.User).filter(models.User.id == utils.decode_access_token(token).get("sub")).first()
    doctor = db.query(models.Doctor).filter(models.Doctor.email == user.email).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@router.get("/patient/profile", response_model=schemas.UserOut)
def get_patient_profile(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.post("/admin/create-superuser")
def create_superuser(password: str, db: Session = Depends(SessionLocal), token: str = Depends(oauth2_scheme)):
    user = db.query(models.User).filter(models.User.email == "ericmutuma15@gmail.com").first()
    if user:
        raise HTTPException(status_code=400, detail="Superuser already exists.")
    # Only allow if the current user is ericmutuma15@gmail.com
    payload = utils.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    current_user = db.query(models.User).filter(models.User.id == payload.get("sub")).first()
    if not current_user or current_user.email != "ericmutuma15@gmail.com":
        raise HTTPException(status_code=403, detail="Not authorized")
    superuser = models.User(
        name="Superuser",
        email="ericmutuma15@gmail.com",
        phone="0700000000",
        password_hash=utils.hash_password(password),
        is_verified=True,
        role=models.UserRole.superuser,
        created_at=datetime.utcnow()
    )
    db.add(superuser)
    db.commit()
    return {"message": "Superuser created!"}

@router.get("/doctors", response_model=List[schemas.DoctorOut])
def list_doctors(service: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Doctor).filter(models.Doctor.is_approved == True)
    if service:
        q = q.filter(models.Doctor.specialty == service)
    return q.all()
