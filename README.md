# PlaceHub – Placement Management System

A full-stack placement portal built with **Flask**, **SQLAlchemy**, and **SQLite**. Designed for educational institutions to manage recruitment drives and student placements with role-based access control.

---

## 📋 About the Project

**PlaceHub** is a web application that streamlines the college placement process by providing:

- **Admin Dashboard**: Approve/reject companies and drives; manage user access; view comprehensive statistics
- **Company Portal**: Post placement drives; review applicants; shortlist/select candidates
- **Student Dashboard**: Browse open drives; apply with one click; track application history

The system enforces **Role-Based Access Control (RBAC)** with three distinct user types:
- **Admin**: Full system oversight and moderation
- **Company/Recruiter**: Drive posting and applicant management
- **Student**: Job browsing and application tracking

### Key Features

✅ **Secure Authentication** – Login/registration with role-based routing  
✅ **Approval Workflow** – Drives and companies require admin approval before going live  
✅ **Duplicate Prevention** – Students cannot apply twice to the same drive  
✅ **Status Tracking** – Real-time application status updates (Applied → Shortlisted → Selected)  
✅ **User Blacklisting** – Admin can deactivate accounts to prevent access  
✅ **Search & Filter** – Find students and companies by name or status  
✅ **Clean PEP 8 Code** – Production-ready, well-documented Python  
✅ **Bootstrap 5 UI** – Responsive, modern interface with no JavaScript dependencies for core features

---

## 🗂️ File Structure

```
placement_portal/
│
├── app.py                          # Main Flask application (all routes & RBAC logic)
├── models.py                       # SQLAlchemy ORM models (5 database tables)
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
└── templates/
    ├── layout.html                 # Base template (navbar, flash messages, styling)
    ├── login.html                  # Login form & authentication page
    ├── register.html               # Student/Company registration form
    ├── admin_dash.html             # Admin dashboard (Companies, Drives, Students tabs)
    ├── company_dash.html           # Company dashboard (profile, drive creation, applicants)
    ├── student_dash.html           # Student dashboard (browse drives, application history)
    ├── 403.html                    # Access denied error page
    └── 404.html                    # Page not found error page
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- pip (Python package manager)

### Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**
   ```bash
   python app.py
   ```

   On first run:
   - Database (`placement.db`) is auto-created
   - All 5 tables are initialized via SQLAlchemy
   - Admin account is seeded with credentials: `admin` / `admin123`

3. **Open in browser**
   ```
   http://127.0.0.1:5000
   ```

---

## 🔐 Pre-Seeded Account

The following admin account is automatically created on first startup:

| Field | Value |
|---|---|
| **Username** | `admin` |
| **Password** | `admin123` |
| **Role** | Admin |

Use these credentials to log in immediately and start approving companies.

---

## 📖 How to Use the App – Step by Step

### Scenario: Company posts a drive → Students apply → Company shortlists

---

### **Step 1: Register a Company Account**

1. Go to **Register** page
2. Select role: **"Company / Recruiter"**
3. Fill in details:
   - **Username**: `tcs_hr`
   - **Password**: `company123`
   - **Company Name**: `Tata Consultancy Services`
   - **HR Contact**: `hr@tcs.com`
   - **Website**: `https://tcs.com`
4. Click **Create Account**

Status: Company account created with `approval_status = "Pending"`

---

### **Step 2: Admin Approves the Company**

1. Log out and login as **`admin`** / **`admin123`**
2. On **Admin Dashboard**, go to **Companies** tab
3. Find "Tata Consultancy Services" with status **Pending**
4. Click **Approve** button

Status: Company is now **Approved** and can post drives

---

### **Step 3: Company Posts a Placement Drive**

1. Log out and login as **`tcs_hr`** / **`company123`**
2. On **Company Dashboard**, fill the **Post New Drive** form (left panel):
   - **Job Title**: `Software Engineer`
   - **Description**: `Full-stack development role for fresh graduates. Build scalable systems using Python and React.`
   - **Eligibility**: `CGPA ≥ 7.0, CSE/IT/ECE branches`
   - **Deadline**: `2025-12-31`
3. Click **Submit for Approval**

Status: Drive created with `status = "Pending"`, awaiting admin approval

---

### **Step 4: Admin Approves the Drive**

1. Log out and login as **`admin`** / **`admin123`**
2. Go to **Drives** tab
3. Find "Software Engineer – TCS" with status **Pending**
4. Click **Approve** button

Status: Drive is now **Approved** and visible to all students

---

### **Step 5: Register a Student Account**

1. Go to **Register** page
2. Select role: **"Student"**
3. Fill in details:
   - **Username**: `john_doe`
   - **Password**: `student123`
   - **Full Name**: `John Doe`
   - **Roll Number**: `CS2021001`
   - **Skills**: `Python, Java, SQL, React`
4. Click **Create Account**

Status: Student account created and ready to browse drives

---

### **Step 6: Student Applies to the Drive**

1. Log out and login as **`john_doe`** / **`student123`**
2. On **Student Dashboard**, see the left panel with open drives
3. Find "Software Engineer" under TCS
4. Click **Apply Now**

Status: Application created with `status = "Applied"`  
Duplicate prevention: Button now shows **"Already Applied"** (cannot apply again)

---

### **Step 7: View Application History**

Right panel shows **Application History** table:

| Drive | Company | Applied | Status |
|---|---|---|---|
| Software Engineer | TCS | 15 Nov | **Applied** |

---

### **Step 8: Company Reviews Applicants**

1. Log out and login as **`tcs_hr`** / **`company123`**
2. On **Company Dashboard**, find the "Software Engineer" drive card
3. In the **Applicants** table, find "John Doe"
4. Dropdown shows: `Applied`, `Shortlisted`, `Selected`, `Rejected`
5. Select **Shortlisted** and click **Set**

Status: Application updated to **Shortlisted**

---

### **Step 9: Student Sees Updated Status**

1. Log out and login as **`john_doe`**
2. Application History now shows:

| Drive | Company | Applied | Status |
|---|---|---|---|
| Software Engineer | TCS | 15 Nov | **Shortlisted** ✨ |

---

### **Step 10 (Optional): Admin Blacklists a User**

1. Log out and login as **`admin`**
2. Go to **Students** tab
3. Find "John Doe"
4. Click **Block**

Status: User's `is_active = False`  
Result: "John Doe" cannot log in; gets message: *"Your account has been deactivated"*

To restore, click **Restore** in the same Students tab.

---

## 🔄 Complete Status Workflows

### Company Approval Workflow
```
Register → Pending → [Admin: Approve/Reject] → Approved/Rejected
```
- **Pending**: Cannot post drives yet
- **Approved**: Can post drives
- **Rejected**: Permanently unable to post drives

### Drive Status Workflow
```
[Company posts] → Pending → [Admin: Approve/Reject/Close] → Approved/Closed
```
- **Pending**: Hidden from students; awaiting admin review
- **Approved**: Visible to students; open for applications
- **Closed**: Hidden from students; no new applications accepted

### Application Status Workflow
```
[Student applies] → Applied → Shortlisted → Selected / Rejected
                    ↓          ↓
                [Company controls via dropdown]
```
- **Applied**: Initial state when student submits application
- **Shortlisted**: Company marks student for interview round
- **Selected**: Student has been offered the job
- **Rejected**: Application rejected by company

---

## 🔑 Role-Based Access Control (RBAC)

### Admin Permissions
- ✅ View dashboard stats (total students, companies, drives)
- ✅ Search/filter all companies and students
- ✅ Approve or reject company registrations
- ✅ Approve, reject, or close placement drives
- ✅ Blacklist (deactivate) any non-admin user
- ✅ Restore deactivated users

### Company Permissions
- ✅ View and edit own company profile
- ✅ **Post drives** (only if approved by admin)
- ✅ View all applicants for own drives
- ✅ Update applicant status (Shortlisted, Selected, Rejected)
- ❌ Cannot view other companies' drives or applicants
- ❌ Cannot approve their own company or drives

### Student Permissions
- ✅ Browse all approved & open drives
- ✅ Apply to drives (one click)
- ✅ View application history with status
- ✅ See which drives they've already applied to
- ❌ Cannot apply twice to the same drive (prevented at DB + app level)
- ❌ Cannot see other students' applications
- ❌ Cannot see pending or closed drives


---

## ⚡ Quick Test Checklist

Run through this to verify everything works:

- [ ] Start app → admin account auto-seeded
- [ ] Login as admin → see stats dashboard
- [ ] Register company → status shows "Pending"
- [ ] Admin approves company → status shows "Approved"
- [ ] Company posts drive → appears in Admin's Drives tab as "Pending"
- [ ] Admin approves drive → drive visible to students
- [ ] Register student → login successful
- [ ] Student sees open drives
- [ ] Student applies → button changes to "Already Applied"
- [ ] Try applying again → blocked (no duplicate)
- [ ] Company updates applicant to "Selected" → student sees "Selected" in history
- [ ] Admin blacklists student → student cannot log in
- [ ] Admin restores student → student can log in again

---

