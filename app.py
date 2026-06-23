from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

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
    version="6.0"
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


class SignupRequest(BaseModel):
    company_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@app.get("/")
def home():
    return {
        "message": "Welcome to PipeGuard AI 🚀",
        "status": "ONLINE",
        "version": "6.0"
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
        "backend_version": "6.0",
        "database": "CONNECTED",
        "authentication": "JWT ENABLED"
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

    if cursor.fetchone():

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
        "access": "GRANTED"
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

    df = pd.read_csv(file.file)

    missing_values = int(
        df.isnull().sum().sum()
    )

    duplicate_rows = int(
        df.duplicated().sum()
    )

    score = 100

    score -= missing_values * 2
    score -= duplicate_rows * 5

    if score < 0:
        score = 0

    issues = []

    if missing_values > 0:
        issues.append(
            f"{missing_values} missing values found"
        )

    if duplicate_rows > 0:
        issues.append(
            f"{duplicate_rows} duplicate rows found"
        )

    if len(issues) == 0:
        issues.append(
            "No issues detected"
        )

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

    return {
        "message": "Pipeline Scan Completed",
        "pipeline": pipeline_name,
        "health_score": score,
        "issues": issues
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

    result = []

    for report in reports:

        result.append(
            {
                "pipeline": report[0],
                "health_score": report[1],
                "issues": report[2],
                "created_at": report[3]
            }
        )

    return {
        "company": email,
        "total_reports": len(result),
        "reports": result
    }