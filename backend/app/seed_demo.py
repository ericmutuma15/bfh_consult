import os
from app.models import Service, Doctor
from app.__init__ import SessionLocal, init_db
from datetime import datetime

def seed_services():
    services = [
        {"name": "General Consultation", "description": "Consult with a general practitioner for any health concern.", "price": 1000},
        {"name": "Pediatrics", "description": "Specialized care for children and infants.", "price": 1200},
        {"name": "Dermatology", "description": "Skin, hair, and nail care and treatment.", "price": 1500},
        {"name": "Dental", "description": "Dental checkups, cleaning, and treatment.", "price": 2000},
        {"name": "Mental Health", "description": "Counseling and mental health support.", "price": 1800},
        {"name": "Gynecology", "description": "Women's health and reproductive care.", "price": 1700},
        {"name": "Cardiology", "description": "Heart and blood vessel care.", "price": 2500},
        {"name": "Orthopedics", "description": "Bone, joint, and muscle care.", "price": 2200},
    ]
    db = SessionLocal()
    for s in services:
        if not db.query(Service).filter(Service.name == s["name"]).first():
            db.add(Service(name=s["name"], description=s["description"], price=s["price"], created_at=datetime.utcnow()))
    db.commit()
    db.close()

def seed_doctors():
    doctors = [
        {"name": "Dr. Jane Doe", "email": "jane@hospital.com", "phone": "0712345678", "gender": "female", "specialty": "General Consultation", "is_approved": True},
        {"name": "Dr. John Smith", "email": "john@hospital.com", "phone": "0723456789", "gender": "male", "specialty": "Pediatrics", "is_approved": True},
        {"name": "Dr. Alice Kim", "email": "alice@hospital.com", "phone": "0734567890", "gender": "female", "specialty": "Dermatology", "is_approved": True},
    ]
    db = SessionLocal()
    for d in doctors:
        if not db.query(Doctor).filter(Doctor.email == d["email"]).first():
            db.add(Doctor(name=d["name"], email=d["email"], phone=d["phone"], gender=d["gender"], specialty=d["specialty"], is_approved=d["is_approved"], created_at=datetime.utcnow()))
    db.commit()
    db.close()

if __name__ == "__main__":
    init_db()
    seed_services()
    seed_doctors()
    print("Seeding complete.")
