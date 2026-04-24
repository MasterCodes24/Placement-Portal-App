"""
models.py - SQLAlchemy database models for the Placement Portal.
Defines all tables: User, CompanyProfile, StudentProfile, PlacementDrive, Application.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    """
    Central user table. Role determines which dashboard is shown after login.
    is_active=False means the admin has blacklisted this account.
    """
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)          # stored as plain text (demo only)
    role = db.Column(db.String(20), nullable=False)               # 'Admin', 'Company', 'Student'
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships – each user may own one profile
    company_profile = db.relationship("CompanyProfile", back_populates="user", uselist=False)
    student_profile = db.relationship("StudentProfile", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User {self.username} [{self.role}]>"


class CompanyProfile(db.Model):
    """
    Extended profile for Company-role users.
    approval_status gates drive creation: only 'Approved' companies may post drives.
    """
    __tablename__ = "company_profile"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    hr_contact = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(200))
    approval_status = db.Column(db.String(20), default="Pending")  # Pending / Approved / Rejected

    user = db.relationship("User", back_populates="company_profile")
    drives = db.relationship("PlacementDrive", back_populates="company", lazy="dynamic")

    def __repr__(self):
        return f"<CompanyProfile {self.company_name} [{self.approval_status}]>"


class StudentProfile(db.Model):
    """
    Extended profile for Student-role users.
    resume_path stores the server-side path to the uploaded PDF/doc.
    """
    __tablename__ = "student_profile"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    roll_number = db.Column(db.String(50), unique=True, nullable=False)
    resume_path = db.Column(db.String(300))
    skills = db.Column(db.Text)                                   # comma-separated skill tags

    user = db.relationship("User", back_populates="student_profile")
    applications = db.relationship("Application", back_populates="student", lazy="dynamic")

    def __repr__(self):
        return f"<StudentProfile {self.full_name} [{self.roll_number}]>"


class PlacementDrive(db.Model):
    """
    A job drive posted by a company.
    Students can only apply when status='Approved' and deadline has not passed.
    """
    __tablename__ = "placement_drive"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company_profile.id"), nullable=False)
    job_title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    eligibility = db.Column(db.Text)
    deadline = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="Pending")          # Pending / Approved / Closed

    company = db.relationship("CompanyProfile", back_populates="drives")
    applications = db.relationship("Application", back_populates="drive", lazy="dynamic")

    def __repr__(self):
        return f"<PlacementDrive {self.job_title} [{self.status}]>"


class Application(db.Model):
    """
    A student's application for a specific drive.
    Unique constraint on (student_id, drive_id) prevents duplicate applications.
    """
    __tablename__ = "application"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profile.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drive.id"), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default="Applied")          # Applied / Shortlisted / Selected / Rejected

    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id", name="uq_student_drive"),
    )

    student = db.relationship("StudentProfile", back_populates="applications")
    drive = db.relationship("PlacementDrive", back_populates="applications")

    def __repr__(self):
        return f"<Application student={self.student_id} drive={self.drive_id} [{self.status}]>"
