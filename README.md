# Swifty - Gymkhana Automation System

> **A centralized web application digitizing the administrative lifecycle for IIT Kanpur Student Gymkhana**

**Live Demo:** https://swifty-tau.vercel.app

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Repo Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Security & Compliance](#security--compliance)

---

## Overview

**Swifty** is a comprehensive digital management system for IIT Kanpur's Student Gymkhana, designed to replace time-consuming, paper-based administrative workflows. It provides a secure, hierarchical digital platform for service requests, venue scheduling, financial management, and official communication.

---

## Key Features

* **Secure Authentication:** Two-step verification using passwords and email OTPs for logins and sensitive actions, secured by JWT and Role-Based Access Control.
* **Coordinator Dashboard:** A centralized portal for club coordinators to submit and track the real-time status of Permission Letters, Venue Bookings, and MoUs.
* **Financial Management:** A real-time ledger allowing clubs to monitor allocated budgets, track spending, and securely upload receipts.
* **Hierarchical Approvals:** Custom dashboards for authorities to review, approve, or reject requests through a strict multi-tier pipeline with mandatory feedback.
* **Administrative Oversight:** Grants authorities elevated privileges to audit club financial ledgers, view request histories, and broadcast targeted announcements.
* **Public Calendar & Notifications:** An automated public calendar displaying approved events, paired with a background service that sends instant email alerts for OTPs and status updates.
---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript | 
| **UI Framework** | Tailwind CSS | 
| **Backend** | FastAPI (Python) |
| **Authentication** | PyJWT | Token-based sessions |
| **Password Hashing** | Passlib + Bcrypt | Secure credential storage |
| **Database** | PostgreSQL |
| **ORM** | SQLAlchemy |
| **Email Service** | Brevo | 
| **File Storage** | Cloudinary |
| **Testing** | Pytest |
| **CORS** | FastAPI Middleware | 
| **Deployment** | Vercel (Frontend), Render (Backend) |

---

## System Architecture

Swifty follows a decoupled **Model-View-Controller (MVC)** pattern, ensuring a strict separation between the user interface, business logic, and data management.

* **Frontend (View):** Built with HTML5, Vanilla JS, and Tailwind CSS. It features isolated, role-specific dashboards (RBAC) and uses asynchronous fetch requests for seamless, lightweight performance.
* **Backend API (Controller):** Powered by FastAPI (Python). The backend is modularized into domain-specific routers (e.g., auth, venues, finances) and utilizes background utilities for issuing JWT tokens and dispatching automated email notifications.
* **Database (Model):** PostgreSQL managed via SQLAlchemy ORM. The relational database is fully ACID-compliant, enforcing strict constraints to prevent double-booking and maintain immutable financial ledgers.

### Core Architecture Flow
1. **User Action:** A coordinator submits a form (e.g., Venue Booking) via the Frontend UI.
2. **Gateway:** The FastAPI Backend receives the request, validates the JWT session, and confirms role permissions.
3. **Processing:** The specific Router interacts with the Database Layer via SQLAlchemy to check constraints (e.g., verifying room capacity or budget limits).
4. **Trigger:** If successful, the database updates the pipeline status, and the Utility layer dispatches the required background emails/OTPs to the next authority in the hierarchy.
---
## Repo Structure

```text
swifty/
├── frontend/                 # Client-side UI
│   ├── components/           # Reusable JavaScript/UI elements
│   └── *.html                # Role-specific dashboards and pages
│
├── backend/                  # FastAPI Server
│   ├── app/
│   │   ├── routers/          # API endpoints (auth, venues, finances, etc.)
│   │   ├── utils/            # Shared logic (email service, security, hashing)
│   │   ├── main.py           # FastAPI application entry point
│   │   ├── models.py         # SQLAlchemy database models
│   │   └── database.py       # Database connection & session setup
│   ├── tests/                # Automated test suites
│   ├── .env.example          # Local testing environment template
│   └── requirements.txt      # Python dependencies
│
├── docker-compose.yml        # Docker config for the isolated local test database
├── seed_db.py                # Script to populate the test database with dummy users
└── README.md                 # Project documentation
```
---

## Installation & Setup

### **Prerequisites**
* **Python 3.10+** (Required for the FastAPI backend)
* **Docker Desktop** (For running local database)
* **Git** (For cloning the repository)
* **Cloudinary Account** (Free tier is fine-required for securely storing uploaded bills and MoU PDFs)

### Clone the Repository
```bash
git clone [https://github.com/sauryas24/swifty.git](https://github.com/sauryas24/swifty.git)
cd swifty

# Make sure Docker Desktop is open and running in the background.
docker-compose up -d
```
### Backend and Database Setup

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your configuration

# 1. Create the database tables
python -m database.main

# 2. Populate it with test users (Coordinators, GenSec, FacAd, etc.)
python seed_db.py

# Start FastAPI server
uvicorn app.main:app --reload
```
Backend runs on: **http://127.0.0.1:8000**  
API Docs: **http://127.0.0.1:8000/docs**

### Frontend Setup

```bash
#Open new terminal window.
# Navigate to frontend directory
cd frontend

# Update API endpoint in config.js
# Change API_BASE_URL to match your backend URL
# Local: "http://127.0.0.1:8000"
# Render: "https://swifty-dni9.onrender.com"

# Serve frontend using Python
python -m http.server 5500
```
Frontend runs on: **http://127.0.0.1:5500** 

To open the website locally, type: **http://127.0.0.1:5500/index.html** in the web browser.

## Check API documentation
#### Open http://127.0.0.1:8000/docs in browser


## Security & Compliance

* **Robust Authentication:** Stateless JWT sessions, strict Role-Based Access Control (RBAC), and 6-digit email OTPs required for all critical actions.
* **Data Integrity & Anti-Fraud:** Immutable, append-only financial ledgers and duplicate invoice detection backed by PostgreSQL's ACID compliance. 
* **Concurrency Control:** Atomic transactions and row-level database locking physically prevent venue double-booking and race conditions.
* **Audit & Compliance:** DOSA-compliant workflows featuring mandatory rejection comments, immutable approval histories, and encrypted 24-hour automated backups.
