"""
app.py - Main Flask application for the Placement Portal.

Role-Based Access Control (RBAC):
  - Admin  : Approves/rejects companies & drives; blacklists users; views all stats.
  - Company: Manages own profile; creates drives (only if Approved); manages applicants.
  - Student: Browses open drives; applies; views application history.

Run:
    pip install flask flask-sqlalchemy
    python app.py          # First run auto-seeds the admin account and creates all tables.
"""

import os
from datetime import date, datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort
)
from models import db, User, CompanyProfile, StudentProfile, PlacementDrive, Application

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = "placement_portal_secret_2024"       # Change in production

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'placement.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# ---------------------------------------------------------------------------
# RBAC decorators
# ---------------------------------------------------------------------------


def login_required(f):
    """Redirect to login if no active session exists."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """Restrict a route to users whose role is in *roles."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get("role") not in roles:
                flash("Access denied.", "danger")
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def get_current_user():
    """Return the User ORM object for the logged-in session user."""
    return User.query.get(session["user_id"])


# ---------------------------------------------------------------------------
# Authentication routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    """Landing page – redirect to dashboard if already logged in."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Login handler.
    On success, sets session variables and redirects to the role-specific dashboard.
    """
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if not user or user.password != password:
            flash("Invalid username or password.", "danger")
        elif not user.is_active:
            flash("Your account has been deactivated. Contact the admin.", "danger")
        else:
            # Successful login – populate session
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Registration for Student and Company roles only.
    Admin accounts are pre-seeded and cannot be self-registered.
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "")

        if role not in ("Student", "Company"):
            flash("Invalid role selected.", "danger")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "warning")
            return render_template("register.html")

        # Create base User record
        user = User(username=username, password=password, role=role)
        db.session.add(user)
        db.session.flush()      # get user.id before commit

        # Create corresponding profile stub
        if role == "Company":
            company_name = request.form.get("company_name", "").strip()
            hr_contact = request.form.get("hr_contact", "").strip()
            website = request.form.get("website", "").strip()
            profile = CompanyProfile(
                user_id=user.id,
                company_name=company_name,
                hr_contact=hr_contact,
                website=website,
                approval_status="Pending"
            )
            db.session.add(profile)

        elif role == "Student":
            full_name = request.form.get("full_name", "").strip()
            roll_number = request.form.get("roll_number", "").strip()
            skills = request.form.get("skills", "").strip()

            if StudentProfile.query.filter_by(roll_number=roll_number).first():
                db.session.rollback()
                flash("Roll number already registered.", "warning")
                return render_template("register.html")

            profile = StudentProfile(
                user_id=user.id,
                full_name=full_name,
                roll_number=roll_number,
                skills=skills
            )
            db.session.add(profile)

        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Generic dashboard dispatcher
# ---------------------------------------------------------------------------


@app.route("/dashboard")
@login_required
def dashboard():
    """Route user to their role-specific dashboard."""
    role = session.get("role")
    if role == "Admin":
        return redirect(url_for("admin_dashboard"))
    elif role == "Company":
        return redirect(url_for("company_dashboard"))
    elif role == "Student":
        return redirect(url_for("student_dashboard"))
    abort(403)


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------


@app.route("/admin")
@login_required
@role_required("Admin")
def admin_dashboard():
    """
    Admin home: summary statistics + search/filter controls for students & companies.
    """
    # Search / filter parameters
    student_q = request.args.get("student_q", "").strip()
    company_q = request.args.get("company_q", "").strip()
    company_status_filter = request.args.get("company_status", "")

    # Statistics
    total_students = StudentProfile.query.count()
    total_companies = CompanyProfile.query.count()
    total_drives = PlacementDrive.query.count()
    pending_companies = CompanyProfile.query.filter_by(approval_status="Pending").count()
    pending_drives = PlacementDrive.query.filter_by(status="Pending").count()

    # Student list (with optional search)
    students_query = StudentProfile.query
    if student_q:
        students_query = students_query.filter(
            (StudentProfile.full_name.ilike(f"%{student_q}%")) |
            (StudentProfile.roll_number.ilike(f"%{student_q}%"))
        )
    students = students_query.all()

    # Company list (with optional search + status filter)
    companies_query = CompanyProfile.query
    if company_q:
        companies_query = companies_query.filter(
            CompanyProfile.company_name.ilike(f"%{company_q}%")
        )
    if company_status_filter:
        companies_query = companies_query.filter_by(approval_status=company_status_filter)
    companies = companies_query.all()

    # All placement drives
    drives = PlacementDrive.query.all()

    return render_template(
        "admin_dash.html",
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        pending_companies=pending_companies,
        pending_drives=pending_drives,
        students=students,
        companies=companies,
        drives=drives,
        student_q=student_q,
        company_q=company_q,
        company_status_filter=company_status_filter,
    )


@app.route("/admin/company/<int:company_id>/status", methods=["POST"])
@login_required
@role_required("Admin")
def toggle_company_status(company_id):
    """Admin: approve or reject a company registration."""
    company = CompanyProfile.query.get_or_404(company_id)
    new_status = request.form.get("status")
    if new_status in ("Approved", "Rejected", "Pending"):
        company.approval_status = new_status
        db.session.commit()
        flash(f"Company '{company.company_name}' status set to {new_status}.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/drive/<int:drive_id>/status", methods=["POST"])
@login_required
@role_required("Admin")
def toggle_drive_status(drive_id):
    """Admin: approve, reject, or close a placement drive."""
    drive = PlacementDrive.query.get_or_404(drive_id)
    new_status = request.form.get("status")
    if new_status in ("Approved", "Pending", "Closed"):
        drive.status = new_status
        db.session.commit()
        flash(f"Drive '{drive.job_title}' status set to {new_status}.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/user/<int:user_id>/blacklist", methods=["POST"])
@login_required
@role_required("Admin")
def toggle_blacklist(user_id):
    """Admin: toggle the is_active flag (blacklist / reinstate) for any non-admin user."""
    user = User.query.get_or_404(user_id)
    if user.role == "Admin":
        flash("Cannot deactivate an admin account.", "warning")
        return redirect(url_for("admin_dashboard"))
    user.is_active = not user.is_active
    db.session.commit()
    state = "activated" if user.is_active else "blacklisted"
    flash(f"User '{user.username}' has been {state}.", "info")
    return redirect(url_for("admin_dashboard"))


# ---------------------------------------------------------------------------
# Company routes
# ---------------------------------------------------------------------------


@app.route("/company")
@login_required
@role_required("Company")
def company_dashboard():
    """
    Company home: shows own profile, drives, and applicants.
    Posting new drives is only allowed when approval_status == 'Approved'.
    """
    user = get_current_user()
    profile = user.company_profile

    if not profile:
        flash("Company profile not found.", "danger")
        return redirect(url_for("logout"))

    drives = profile.drives.all()

    # Gather applicants grouped by drive
    drive_applicants = {}
    for drive in drives:
        drive_applicants[drive.id] = drive.applications.all()

    return render_template(
        "company_dash.html",
        profile=profile,
        drives=drives,
        drive_applicants=drive_applicants,
    )


@app.route("/company/drive/new", methods=["POST"])
@login_required
@role_required("Company")
def create_drive():
    """
    Company: create a new placement drive.
    Only allowed when the company profile is 'Approved'.
    New drives start with status='Pending' and await admin approval.
    """
    user = get_current_user()
    profile = user.company_profile

    # RBAC check: company must be approved
    if profile.approval_status != "Approved":
        flash("Your company must be approved before posting drives.", "warning")
        return redirect(url_for("company_dashboard"))

    job_title = request.form.get("job_title", "").strip()
    description = request.form.get("description", "").strip()
    eligibility = request.form.get("eligibility", "").strip()
    deadline_str = request.form.get("deadline", "")

    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid deadline date format.", "danger")
        return redirect(url_for("company_dashboard"))

    drive = PlacementDrive(
        company_id=profile.id,
        job_title=job_title,
        description=description,
        eligibility=eligibility,
        deadline=deadline,
        status="Pending"        # Admin must approve before students see it
    )
    db.session.add(drive)
    db.session.commit()
    flash(f"Drive '{job_title}' submitted for admin approval.", "success")
    return redirect(url_for("company_dashboard"))


@app.route("/company/application/<int:app_id>/status", methods=["POST"])
@login_required
@role_required("Company")
def update_application_status(app_id):
    """
    Company: shortlist, select, or reject an applicant.
    Only the drive's owning company can update its applications.
    """
    application = Application.query.get_or_404(app_id)
    user = get_current_user()

    # Ensure this application belongs to a drive owned by this company
    if application.drive.company.user_id != user.id:
        abort(403)

    new_status = request.form.get("status")
    if new_status in ("Applied", "Shortlisted", "Selected", "Rejected"):
        application.status = new_status
        db.session.commit()
        flash(f"Application status updated to '{new_status}'.", "success")

    return redirect(url_for("company_dashboard"))


# ---------------------------------------------------------------------------
# Student routes
# ---------------------------------------------------------------------------


@app.route("/student")
@login_required
@role_required("Student")
def student_dashboard():
    """
    Student home: lists open & approved drives; shows application history.
    """
    user = get_current_user()
    profile = user.student_profile

    if not profile:
        flash("Student profile not found.", "danger")
        return redirect(url_for("logout"))

    today = date.today()

    # Only show approved drives that have not passed their deadline
    open_drives = (
        PlacementDrive.query
        .filter_by(status="Approved")
        .filter(PlacementDrive.deadline >= today)
        .all()
    )

    # IDs of drives the student has already applied to (for duplicate prevention)
    applied_drive_ids = {
        app.drive_id for app in profile.applications.all()
    }

    # Full application history
    applications = (
        profile.applications
        .order_by(Application.date.desc())
        .all()
    )

    return render_template(
        "student_dash.html",
        profile=profile,
        open_drives=open_drives,
        applied_drive_ids=applied_drive_ids,
        applications=applications,
    )


@app.route("/student/apply/<int:drive_id>", methods=["POST"])
@login_required
@role_required("Student")
def apply_to_drive(drive_id):
    """
    Student: one-click application.
    Duplicate applications (same student + drive) are blocked by DB constraint + pre-check.
    """
    user = get_current_user()
    profile = user.student_profile
    drive = PlacementDrive.query.get_or_404(drive_id)

    # Verify drive is still open
    if drive.status != "Approved" or drive.deadline < date.today():
        flash("This drive is no longer accepting applications.", "warning")
        return redirect(url_for("student_dashboard"))

    # Prevent duplicates
    existing = Application.query.filter_by(
        student_id=profile.id, drive_id=drive_id
    ).first()
    if existing:
        flash("You have already applied to this drive.", "info")
        return redirect(url_for("student_dashboard"))

    application = Application(
        student_id=profile.id,
        drive_id=drive_id,
        status="Applied"
    )
    db.session.add(application)
    db.session.commit()
    flash(f"Successfully applied to '{drive.job_title}'!", "success")
    return redirect(url_for("student_dashboard"))


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------


@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# ---------------------------------------------------------------------------
# Database initialisation & seed
# ---------------------------------------------------------------------------


def seed_admin():
    """Create the pre-seeded admin account if it does not already exist."""
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password="admin123", role="Admin", is_active=True)
        db.session.add(admin)
        db.session.commit()
        print("[SEED] Admin account created (username: admin, password: admin123)")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()         # Creates all tables from SQLAlchemy models
        seed_admin()
    app.run(debug=True)
