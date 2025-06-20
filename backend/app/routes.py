from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from . import schemas, models, utils, daraja
from .__init__ import SessionLocal, init_db
from datetime import datetime, timedelta
from typing import List, Optional
import os
from fastapi.responses import FileResponse
from .models import Notification

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
        password_hash=utils.get_password_hash(user.password),
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
@router.get("/profile")
def get_profile(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # If doctor, include doctor profile and profile_incomplete flag
    if current_user.role == models.UserRole.doctor:
        doctor = db.query(models.Doctor).filter(models.Doctor.email == current_user.email).first()
        profile_incomplete = not (doctor and doctor.qualifications and doctor.kmpdc_license and doctor.evidence_url and doctor.is_approved)
        return {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "phone": current_user.phone,
            "is_verified": current_user.is_verified,
            "role": current_user.role.value,
            "created_at": current_user.created_at,
            "doctor_profile": doctor,
            "profile_incomplete": profile_incomplete
        }
    # If superuser, just return user info and role
    elif current_user.role == models.UserRole.superuser:
        return {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "phone": current_user.phone,
            "is_verified": current_user.is_verified,
            "role": current_user.role.value,
            "created_at": current_user.created_at
        }
    # Default: patient
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone,
        "is_verified": current_user.is_verified,
        "role": current_user.role.value,
        "created_at": current_user.created_at
    }

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

    # Notify doctor and all superusers
    doctor = db.query(models.Doctor).filter(models.Doctor.id == app.doctor_id).first()
    if doctor:
        utils.send_notification_email(
            doctor.email,
            "New Appointment Booked",
            f"You have a new appointment from {current_user.name or current_user.email}. Symptoms: {app.symptoms}\nDetails: {app.details}"
        )
    superusers = db.query(models.User).filter(models.User.role == models.UserRole.superuser).all()
    for su in superusers:
        utils.send_notification_email(
            su.email,
            "New Appointment Booked",
            f"A new appointment has been booked for Dr. {doctor.name if doctor else app.doctor_id} by {current_user.name or current_user.email}."
        )
    return db_app

@router.get("/appointments", response_model=list[schemas.AppointmentOut])
def list_appointments(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Appointment).filter(models.Appointment.user_id == current_user.id).all()

@router.post("/appointments/payment")
def appointment_payment(req: schemas.AppointmentPaymentRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    app = db.query(models.Appointment).filter(models.Appointment.id == req.appointment_id, models.Appointment.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Appointment not found")
    # Initiate Daraja STK Push
    stk_response = daraja.initiate_stk_push(req.phone_number, 1000)
    if stk_response.get("ResponseCode") == "0":
        app.payment_status = "paid"
        db.commit()
        return {"message": "Payment initiated. Check your phone to complete the payment.", "stk_response": stk_response}
    else:
        return {"status": "error", "message": stk_response.get("message", "Failed to initiate payment."), "stk_response": stk_response}

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
def admin_doctor_signup(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    gender: str = Form(...),
    specialty: str = Form(...),
    certificates: List[UploadFile] = File([]),
    certificate_titles: List[str] = Form([]),
    db: Session = Depends(get_db)
):
    # Check for existing doctor
    if db.query(models.Doctor).filter((models.Doctor.email == email) | (models.Doctor.phone == phone)).first():
        raise HTTPException(status_code=400, detail="Email or phone already registered")
    db_doctor = models.Doctor(
        name=name,
        email=email,
        phone=phone,
        gender=gender,
        specialty=specialty,
        is_approved=False
    )
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)

    # Save certificates
    cert_dir = os.path.join(os.path.dirname(__file__), "../certificates")
    os.makedirs(cert_dir, exist_ok=True)
    cert_objs = []
    for idx, file in enumerate(certificates):
        if file and file.filename:
            title = certificate_titles[idx] if idx < len(certificate_titles) else f"Certificate {idx+1}"
            ext = os.path.splitext(file.filename)[1]
            fname = f"{db_doctor.id}_{idx}{ext}"
            fpath = os.path.join(cert_dir, fname)
            file_bytes = file.file.read()
            with open(fpath, "wb") as f:
                f.write(file_bytes)
            cert = models.DoctorCertificate(
                doctor_id=db_doctor.id,
                title=title,
                file_path=f"certificates/{fname}"
            )
            db.add(cert)
            cert_objs.append(cert)
    db.commit()
    # DO NOT manually assign db_doctor.certificates = cert_objs
    # Instead, reload the doctor from the DB so the certificates relationship is clean
    doctor_out = db.query(models.Doctor).filter(models.Doctor.id == db_doctor.id).first()
    return doctor_out

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
def list_doctors(service: Optional[str] = None, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Superusers see all doctors, others see only approved
    if current_user.role == models.UserRole.superuser:
        q = db.query(models.Doctor)
    else:
        q = db.query(models.Doctor).filter(models.Doctor.is_approved == True)
    if service:
        q = q.filter(models.Doctor.specialty == service)
    return q.all()

@router.post("/auth/doctor-signup", response_model=schemas.UserOut)
def doctor_signup(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    gender: str = Form(...),
    specialty: str = Form(...),
    certificates: List[UploadFile] = File([]),
    certificate_titles: List[str] = Form([]),
    db: Session = Depends(get_db)
):
    # Check if user or doctor already exists
    if db.query(models.User).filter((models.User.email == email) | (models.User.phone == phone)).first() or \
       db.query(models.Doctor).filter((models.Doctor.email == email) | (models.Doctor.phone == phone)).first():
        raise HTTPException(status_code=400, detail="Email or phone already registered")
    # Create user with doctor role
    db_user = models.User(
        name=name,
        email=email,
        phone=phone,
        password_hash=utils.get_password_hash(password),
        is_verified=False,
        role=models.UserRole.doctor,
        created_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # Create doctor profile
    db_doctor = models.Doctor(
        name=name,
        email=email,
        phone=phone,
        gender=gender,
        specialty=specialty,
        is_approved=False,
        created_at=datetime.utcnow()
    )
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    # Save certificates
    cert_dir = os.path.join(os.path.dirname(__file__), "../certificates")
    os.makedirs(cert_dir, exist_ok=True)
    for idx, file in enumerate(certificates):
        if file and file.filename:
            title = certificate_titles[idx] if idx < len(certificate_titles) else f"Certificate {idx+1}"
            ext = os.path.splitext(file.filename)[1]
            fname = f"{db_doctor.id}_{idx}{ext}"
            fpath = os.path.join(cert_dir, fname)
            file_bytes = file.file.read()
            with open(fpath, "wb") as f:
                f.write(file_bytes)
            cert = models.DoctorCertificate(
                doctor_id=db_doctor.id,
                title=title,
                file_path=f"certificates/{fname}"
            )
            db.add(cert)
    db.commit()
    return db_user

@router.post("/doctor/profile-completion", response_model=schemas.DoctorOut)
def doctor_profile_completion(
    qualifications: str = Form(...),
    kmpdc_license: str = Form(...),
    evidence_file: UploadFile = File(None),
    evidence_url: str = Form(None),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = db.query(models.User).filter(models.User.id == utils.decode_access_token(token).get("sub")).first()
    doctor = db.query(models.Doctor).filter(models.Doctor.email == user.email).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor.qualifications = qualifications
    doctor.kmpdc_license = kmpdc_license
    # Handle evidence file upload
    if evidence_file and evidence_file.filename:
        evidence_dir = os.path.join(os.path.dirname(__file__), "../evidence")
        os.makedirs(evidence_dir, exist_ok=True)
        ext = os.path.splitext(evidence_file.filename)[1]
        fname = f"{doctor.id}_evidence{ext}"
        fpath = os.path.join(evidence_dir, fname)
        with open(fpath, "wb") as f:
            f.write(evidence_file.file.read())
        doctor.evidence_url = f"evidence/{fname}"
    elif evidence_url:
        doctor.evidence_url = evidence_url
    else:
        raise HTTPException(status_code=400, detail="Evidence file or URL required")
    doctor.approval_status = "pending"
    doctor.is_approved = False
    db.commit()
    db.refresh(doctor)
    # Notify all superusers
    superusers = db.query(models.User).filter(models.User.role == models.UserRole.superuser).all()
    for su in superusers:
        db.add(Notification(
            user_id=su.id,
            message=f"New doctor profile submitted: {doctor.name} ({doctor.email}) is awaiting approval.",
            type="doctor_approval"
        ))
    db.commit()
    return db.query(models.Doctor).filter(models.Doctor.id == doctor.id).first()

@router.get("/certificates/{certificate_id}/download")
def download_doctor_certificate(certificate_id: str, db: Session = Depends(get_db)):
    cert = db.query(models.DoctorCertificate).filter(models.DoctorCertificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    # The file_path is relative to the backend/app directory
    abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), f"../{cert.file_path}"))
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found")
    filename = os.path.basename(abs_path)
    return FileResponse(abs_path, filename=filename)

from fastapi import Request

@router.post("/daraja/callback")
async def daraja_callback(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    # Optionally, log or process the callback data
    # Example: update payment status in DB based on CheckoutRequestID or ResultCode
    # You can expand this logic as needed for your app
    return {"status": "received", "data": data}

# Notification endpoints
@router.post("/notifications/", response_model=schemas.NotificationOut)
def create_notification(notification: schemas.NotificationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_notification = Notification(
        user_id=notification.user_id,
        message=notification.message,
        type=notification.type
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

@router.get("/notifications/", response_model=List[schemas.NotificationOut])
def get_notifications(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Fetch notifications for the current user and broadcast (user_id is None)
    return db.query(Notification).filter((Notification.user_id == current_user.id) | (Notification.user_id == None)).order_by(Notification.created_at.desc()).all()

@router.put("/notifications/{notification_id}/read", response_model=schemas.NotificationOut)
def mark_notification_read(notification_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification or (notification.user_id and notification.user_id != current_user.id):
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
