from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import re

from database import get_db, create_tables
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)

app = FastAPI(
    title="PipeGuard AI",
    description="AI Powered Data Reliability Platform",
    version="9.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()

security = HTTPBearer()


# -------------------------
# Request Models
# -------------------------

class SignupRequest(BaseModel):
    company_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# -------------------------
# Base APIs
# -------------------------

@app.get("/")
def home():

    return {
        "message": "Welcome to PipeGuard AI 🚀",
        "status": "ONLINE",
        "version": "9.0"
    }


@app.get("/health")
def health():

    return {
        "service": "PipeGuard AI",
        "status": "Healthy"
    }


@app.get("/api-status")
def api_status():

    return {
        "application": "PipeGuard AI",
        "backend_version": "9.0",
        "database": "CONNECTED",
        "authentication": "JWT ENABLED",
        "scan_engine": "ACTIVE"
    }
    # -------------------------
# Signup API
# -------------------------

@app.post("/signup")
def signup(user: SignupRequest):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT email FROM users WHERE email=?",
        (user.email,)
    )

    existing_user = cursor.fetchone()

    if existing_user:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = hash_password(
        user.password
    )

    cursor.execute(
        """
        INSERT INTO users
        (
            company_name,
            email,
            password
        )
        VALUES (?, ?, ?)
        """,
        (
            user.company_name,
            user.email,
            hashed_password
        )
    )

    conn.commit()
    conn.close()

    return {
        "message": "Account created successfully"
    }


# -------------------------
# Login API
# -------------------------

@app.post("/login")
def login(data: LoginRequest):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT password
        FROM users
        WHERE email=?
        """,
        (data.email,)
    )

    user = cursor.fetchone()

    conn.close()

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email"
        )

    if not verify_password(
        data.password,
        user[0]
    ):

        raise HTTPException(
            status_code=401,
            detail="Wrong password"
        )

    token = create_access_token(
        data.email
    )

    return {
        "access_token": token,
        "token_type": "Bearer"
    }


# -------------------------
# JWT Verification
# -------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    email = verify_token(token)

    if not email:

        raise HTTPException(
            status_code=401,
            detail="Invalid Token"
        )

    return email


# -------------------------
# Workspace API
# -------------------------

@app.get("/my-workspace")
def my_workspace(
    email: str = Depends(get_current_user)
):

    return {

        "message": "Welcome to PipeGuard Workspace",

        "company": email,

        "access": "GRANTED",

        "features": [
            "Pipeline Monitoring",
            "Data Quality Scans",
            "Issue Detection",
            "Health Reports",
            "Auto Fix Engine"
        ]

    }
    # -------------------------
# Upload Pipeline API
# -------------------------

@app.post("/upload-pipeline")
def upload_pipeline(
    pipeline_name: str,
    file: UploadFile = File(...),
    email: str = Depends(get_current_user)
):

    # Read CSV

    df = pd.read_csv(file.file)

    # -------------------------
    # Missing Values
    # -------------------------

    missing_values = int(
        df.isnull().sum().sum()
    )

    missing_details = []

    for col in df.columns:

        rows = df[
            df[col].isnull()
        ].index.tolist()

        for row in rows[:10]:

            missing_details.append(
                f"Row {row + 2}: {col} is empty"
            )

    # -------------------------
    # Duplicate Rows
    # -------------------------

    duplicate_rows = int(
        df.duplicated().sum()
    )

    duplicate_details = []

    duplicate_indexes = df[
        df.duplicated()
    ].index.tolist()

    for row in duplicate_indexes[:10]:

        duplicate_details.append(
            f"Row {row + 2}: Duplicate row detected"
        )

    # -------------------------
    # Invalid Emails
    # -------------------------

    invalid_emails = 0

    email_details = []

    if "Email" in df.columns:

        email_series = (
            df["Email"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        invalid_mask = ~email_series.str.match(
            r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        )

        invalid_emails = int(
            invalid_mask.sum()
        )

        invalid_rows = df[
            invalid_mask
        ].index.tolist()

        for row in invalid_rows[:10]:

            email_details.append(
                f"Row {row + 2}: Invalid email format"
            )

    # -------------------------
    # Invalid Phones (FIXED)
    # -------------------------

    invalid_phones = 0

    phone_details = []

    if "Phone" in df.columns:

        phone_series = (
            df["Phone"]
            .fillna("")
            .astype(str)
            .str.replace(".0", "", regex=False)
            .str.replace(" ", "", regex=False)
            .str.strip()
        )

        invalid_phone_mask = ~phone_series.str.match(
            r"^\d{10}$"
        )

        invalid_phones = int(
            invalid_phone_mask.sum()
        )

        invalid_phone_rows = df[
            invalid_phone_mask
        ].index.tolist()

        for row in invalid_phone_rows[:10]:

            phone_details.append(
                f"Row {row + 2}: Invalid phone number"
            )
                # -------------------------
    # Negative Revenue
    # -------------------------

    negative_revenue = 0

    revenue_details = []

    if "Order_Value" in df.columns:

        negative_mask = (
            pd.to_numeric(
                df["Order_Value"],
                errors="coerce"
            ).fillna(0) < 0
        )

        negative_revenue = int(
            negative_mask.sum()
        )

        negative_rows = df[
            negative_mask
        ].index.tolist()

        for row in negative_rows[:10]:

            revenue_details.append(
                f"Row {row + 2}: Negative revenue detected"
            )

    # -------------------------
    # Health Score
    # -------------------------

    score = 100

    score -= missing_values * 1
    score -= duplicate_rows * 2
    score -= invalid_emails * 1
    score -= invalid_phones * 1
    score -= negative_revenue * 2

    if score < 0:
        score = 0

    # -------------------------
    # Issues List
    # -------------------------

    issues = []

    if missing_values > 0:
        issues.append(
            f"{missing_values} missing values found"
        )

    if duplicate_rows > 0:
        issues.append(
            f"{duplicate_rows} duplicate rows found"
        )

    if invalid_emails > 0:
        issues.append(
            f"{invalid_emails} invalid emails found"
        )

    if invalid_phones > 0:
        issues.append(
            f"{invalid_phones} invalid phone numbers found"
        )

    if negative_revenue > 0:
        issues.append(
            f"{negative_revenue} negative revenue records found"
        )

    if len(issues) == 0:

        issues.append(
            "No issues detected"
        )

    # -------------------------
    # Details Object
    # -------------------------

    details = {

        "missing": missing_details,

        "duplicates": duplicate_details,

        "invalid_emails": email_details,

        "invalid_phones": phone_details,

        "negative_revenue": revenue_details

    }

    # -------------------------
    # Save Report
    # -------------------------

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO pipeline_reports
        (
            company_email,
            pipeline_name,
            health_score,
            issues
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            email,
            pipeline_name,
            score,
            ", ".join(issues)
        )
    )

    conn.commit()
    conn.close()

    # -------------------------
    # Final Response
    # -------------------------

    return {

        "message": "Pipeline Scan Completed Successfully",

        "pipeline": pipeline_name,

        "health_score": score,

        "issues": issues,

        "metrics": {

            "missing_values": missing_values,

            "duplicate_rows": duplicate_rows,

            "invalid_emails": invalid_emails,

            "invalid_phones": invalid_phones,

            "negative_revenue": negative_revenue

        },

        "details": details

    }
    # -------------------------
# Reports API
# -------------------------

@app.get("/my-reports")
def my_reports(
    email: str = Depends(get_current_user)
):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            pipeline_name,
            health_score,
            issues,
            created_at
        FROM pipeline_reports
        WHERE company_email=?
        ORDER BY created_at DESC
        """,
        (email,)
    )

    reports = cursor.fetchall()

    conn.close()

    report_list = []

    for report in reports:

        report_list.append(
            {
                "pipeline": report[0],
                "health_score": report[1],
                "issues": report[2],
                "created_at": report[3]
            }
        )

    return {

        "company": email,

        "total_reports": len(
            report_list
        ),

        "reports": report_list

    }


# -------------------------
# End Of File
# -------------------------
