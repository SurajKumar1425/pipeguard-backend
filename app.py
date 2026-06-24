# ==================================================
# PIPEGUARD AI V16
# PART 1
# IMPORTS + SECURITY + MONITORING
# ==================================================

import io
import os
import re
import json
import time
import uuid
import base64
import logging
import traceback
from datetime import datetime

from typing import (
    Dict,
    Any,
    Optional,
    Tuple
)

# ==================================================
# FASTAPI
# ==================================================

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    UploadFile,
    File,
    Request,
    status
)

from fastapi.responses import (
    JSONResponse
)

from fastapi.middleware.cors import (
    CORSMiddleware
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

# ==================================================
# DATA PROCESSING
# ==================================================

import pandas as pd

# ==================================================
# REAL TIME MONITORING
# ==================================================

import psutil

# ==================================================
# RATE LIMITING
# ==================================================

from slowapi import Limiter
from slowapi.util import (
    get_remote_address
)

from slowapi.errors import (
    RateLimitExceeded
)

# ==================================================
# PYDANTIC
# ==================================================

from pydantic import (
    BaseModel,
    EmailStr,
    Field
)

# ==================================================
# LOCAL FILES
# ==================================================

from database import (
    get_db,
    create_tables
)

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)

# ==================================================
# START TIME
# ==================================================

APP_START_TIME = time.time()

# ==================================================
# LOGGING
# ==================================================

logging.basicConfig(

    level=logging.INFO,

    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    )

)

logger = logging.getLogger(
    "PIPEGUARD"
)

# ==================================================
# RATE LIMITER
# ==================================================

limiter = Limiter(
    key_func=get_remote_address
)

# ==================================================
# FILE LIMITS
# ==================================================

MAX_FILE_SIZE = (
    20 * 1024 * 1024
)

ALLOWED_EXTENSIONS = {

    ".csv",
    ".xlsx",
    ".xls",
    ".json",
    ".txt"

}

# ==================================================
# TEMP EMAILS
# ==================================================

TEMP_EMAIL_DOMAINS = {

    "mailinator.com",
    "10minutemail.com",
    "guerrillamail.com",
    "yopmail.com",
    "tempmail.com",
    "temp-mail.org",
    "getnada.com",
    "trashmail.com",
    "fakeinbox.com",
    "dispostable.com",
    "maildrop.cc",
    "mailnesia.com",
    "sharklasers.com",
    "grr.la",
    "throwawaymail.com",
    "burnermail.com"

}

# ==================================================
# BLOCKED PHONES
# ==================================================

BLOCKED_PHONES = {

    "1234567890",
    "1111111111",
    "2222222222",
    "3333333333",
    "4444444444",
    "5555555555",
    "6666666666",
    "7777777777",
    "8888888888",
    "9999999999",
    "0000000000",
    "9876543210"

}

# ==================================================
# REGEX
# ==================================================

PHONE_REGEX = re.compile(
    r"^[6-9]\d{9}$"
)

EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

# ==================================================
# SECURITY HEADERS
# ==================================================

SECURITY_HEADERS = {

    "X-Frame-Options":
        "DENY",

    "X-Content-Type-Options":
        "nosniff",

    "Referrer-Policy":
        "strict-origin-when-cross-origin"

}

# ==================================================
# GLOBAL MONITORING
# ==================================================

MONITOR = {

    "total_requests": 0,

    "successful_uploads": 0,

    "failed_uploads": 0,

    "active_users": 0,

    "total_errors": 0

}

print(
    "PipeGuard AI Security Layer Loaded"
)
# ==================================================
# PIPEGUARD AI V16
# PART 2
# FASTAPI + CORS + MONITORING
# ==================================================

app = FastAPI(

    title="PipeGuard AI",

    description=(
        "Enterprise AI Data Quality Platform"
    ),

    version="16.0"

)

# ==================================================
# RATE LIMITER
# ==================================================

app.state.limiter = limiter

@app.exception_handler(
    RateLimitExceeded
)
async def rate_limit_handler(
    request: Request,
    exc: RateLimitExceeded
):

    return JSONResponse(

        status_code=429,

        content={

            "success": False,

            "message":
                "Too many requests",

            "retry":
                "Please try again later"

        }

    )

# ==================================================
# CORS
# ==================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[

        "https://pipeguard-dashboard.vercel.app",

        "http://localhost:5173",

        "http://127.0.0.1:5173"

    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

)

# ==================================================
# DATABASE INIT
# ==================================================

create_tables()

# ==================================================
# SECURITY
# ==================================================

security = HTTPBearer()

# ==================================================
# REQUEST TRACKER
# ==================================================

@app.middleware("http")
async def request_tracker(

    request: Request,

    call_next

):

    request_id = str(
        uuid.uuid4()
    )

    MONITOR[
        "total_requests"
    ] += 1

    start_time = time.time()

    try:

        response = await call_next(
            request
        )

        duration = round(

            time.time()
            - start_time,

            3

        )

        logger.info(

            f"[{request_id}] "

            f"{request.method} "

            f"{request.url.path} "

            f"{response.status_code} "

            f"{duration}s"

        )

        response.headers[
            "X-Request-ID"
        ] = request_id

        return response

    except Exception as e:

        MONITOR[
            "total_errors"
        ] += 1

        logger.error(

            f"[{request_id}] "

            f"ERROR: {str(e)}"

        )

        raise e

# ==================================================
# SECURITY HEADERS
# ==================================================

@app.middleware("http")
async def add_security_headers(

    request: Request,

    call_next

):

    response = await call_next(
        request
    )

    for key, value in (
        SECURITY_HEADERS.items()
    ):

        response.headers[
            key
        ] = value

    return response

# ==================================================
# STARTUP EVENT
# ==================================================

@app.on_event("startup")
async def startup_event():

    try:

        create_tables()

        logger.info(
            "Database Ready"
        )

        logger.info(
            "PipeGuard AI Started"
        )

    except Exception as e:

        logger.error(
            f"Startup Error: {e}"
        )

# ==================================================
# SHUTDOWN EVENT
# ==================================================

@app.on_event("shutdown")
async def shutdown_event():

    logger.warning(
        "PipeGuard AI Stopped"
    )

# ==================================================
# UPTIME
# ==================================================

def get_uptime():

    seconds = int(

        time.time()

        - APP_START_TIME

    )

    hours = seconds // 3600

    minutes = (
        seconds % 3600
    ) // 60

    return (
        f"{hours}h "
        f"{minutes}m"
    )

# ==================================================
# HEALTH SCORE
# ==================================================

def system_health_score():

    cpu = psutil.cpu_percent()

    ram = (
        psutil.virtual_memory()
        .percent
    )

    disk = (
        psutil.disk_usage("/")
        .percent
    )

    score = 100

    score -= cpu * 0.2

    score -= ram * 0.2

    score -= disk * 0.1

    score = max(
        0,
        min(
            100,
            round(score)
        )
    )

    return score

# ==================================================
# LIVE MONITOR
# ==================================================

@app.get("/live-monitor")
def live_monitor():

    return {

        "status":
            "running",

        "uptime":
            get_uptime(),

        "cpu":
            psutil.cpu_percent(),

        "ram":
            psutil.virtual_memory().percent,

        "disk":
            psutil.disk_usage("/").percent,

        "health_score":
            system_health_score(),

        "requests":
            MONITOR[
                "total_requests"
            ],

        "errors":
            MONITOR[
                "total_errors"
            ],

        "successful_uploads":
            MONITOR[
                "successful_uploads"
            ],

        "failed_uploads":
            MONITOR[
                "failed_uploads"
            ]

    }

# ==================================================
# DATABASE HEALTH
# ==================================================

@app.get("/database-health")
def database_health():

    try:

        conn = get_db()

        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1"
        )

        conn.close()

        return {

            "database":
                "connected",

            "status":
                "healthy"

        }

    except Exception as e:

        return {

            "database":
                "disconnected",

            "error":
                str(e)

        }

print(
    "PipeGuard Monitoring Layer Loaded"
)
# ==================================================
# PIPEGUARD AI V16
# PART 3
# SECURITY LAYER
# ==================================================

# ==================================================
# AUDIT LOG
# ==================================================

AUDIT_LOGS = []

def add_audit_log(

    action: str,

    user: str = "anonymous",

    status: str = "success"

):

    AUDIT_LOGS.append({

        "timestamp":
            str(datetime.utcnow()),

        "user":
            user,

        "action":
            action,

        "status":
            status

    })

# ==================================================
# PYDANTIC MODELS
# ==================================================

class SignupRequest(BaseModel):

    full_name: str = Field(

        ...,

        min_length=2,

        max_length=100

    )

    company_name: str = ""

    country_code: str = "+91"

    phone: str

    email: EmailStr

    password: str


class LoginRequest(BaseModel):

    email: EmailStr

    password: str


class UpdateProfileRequest(BaseModel):

    full_name: Optional[str] = None

    company_name: Optional[str] = None

    phone: Optional[str] = None


class ChangePasswordRequest(BaseModel):

    old_password: str

    new_password: str

# ==================================================
# PASSWORD VALIDATION
# ==================================================

def validate_password(

    password: str

):

    if len(password) < 8:

        raise HTTPException(

            status_code=400,

            detail=
            "Password must contain at least 8 characters"

        )

    if not re.search(

        r"[A-Z]",

        password

    ):

        raise HTTPException(

            status_code=400,

            detail=
            "Password must contain uppercase letter"

        )

    if not re.search(

        r"[a-z]",

        password

    ):

        raise HTTPException(

            status_code=400,

            detail=
            "Password must contain lowercase letter"

        )

    if not re.search(

        r"\d",

        password

    ):

        raise HTTPException(

            status_code=400,

            detail=
            "Password must contain number"

        )

    if not re.search(

        r"[!@#$%^&*()_+=<>?/]",

        password

    ):

        raise HTTPException(

            status_code=400,

            detail=
            "Password must contain special character"

        )

    return True

# ==================================================
# EMAIL VALIDATION
# ==================================================

def validate_email(

    email: str

):

    email = email.lower()

    if not EMAIL_REGEX.match(

        email

    ):

        raise HTTPException(

            status_code=400,

            detail=
            "Invalid email address"

        )

    domain = (

        email

        .split("@")[-1]

        .lower()

    )

    if domain in TEMP_EMAIL_DOMAINS:

        raise HTTPException(

            status_code=400,

            detail=
            "Temporary email addresses are not allowed"

        )

    return True

# ==================================================
# PHONE VALIDATION
# ==================================================

def validate_phone(

    phone: str

):

    if not PHONE_REGEX.match(

        phone

    ):

        raise HTTPException(

            status_code=400,

            detail=
            "Invalid Indian phone number"

        )

    if phone in BLOCKED_PHONES:

        raise HTTPException(

            status_code=400,

            detail=
            "Blocked phone number"

        )

    return True

# ==================================================
# FILE SIZE CHECK
# ==================================================

def validate_file_size(

    uploaded_file: UploadFile

):

    uploaded_file.file.seek(

        0,

        2

    )

    file_size = (

        uploaded_file.file.tell()

    )

    uploaded_file.file.seek(

        0

    )

    if file_size > MAX_FILE_SIZE:

        raise HTTPException(

            status_code=400,

            detail=
            "File exceeds maximum allowed size"

        )

# ==================================================
# EXTENSION CHECK
# ==================================================

def validate_file_extension(

    uploaded_file: UploadFile

):

    filename = (

        uploaded_file.filename

        .lower()

    )

    allowed = any(

        filename.endswith(ext)

        for ext in ALLOWED_EXTENSIONS

    )

    if not allowed:

        raise HTTPException(

            status_code=400,

            detail=
            "Unsupported file format"

        )

# ==================================================
# FILE NAME SECURITY
# ==================================================

def validate_filename(

    uploaded_file: UploadFile

):

    filename = (

        uploaded_file.filename

    )

    dangerous_patterns = [

        "..",

        "/",

        "\\",

        ".exe",

        ".bat",

        ".cmd",

        ".sh",

        ".msi",

        ".php",

        ".js"

    ]

    lower = filename.lower()

    for pattern in dangerous_patterns:

        if pattern in lower:

            raise HTTPException(

                status_code=400,

                detail=
                "Dangerous filename detected"

            )

# ==================================================
# CONTENT SCAN
# ==================================================

def scan_uploaded_file(

    uploaded_file: UploadFile

):

    uploaded_file.file.seek(

        0

    )

    content = (

        uploaded_file.file.read(
            4096
        )

    )

    uploaded_file.file.seek(
        0
    )

    suspicious = [

        b"<script",

        b"<?php",

        b"powershell",

        b"cmd.exe",

        b"wget ",

        b"curl "

    ]

    for item in suspicious:

        if item.lower() in content.lower():

            raise HTTPException(

                status_code=400,

                detail=
                "Suspicious content detected"

            )

# ==================================================
# FULL FILE SECURITY
# ==================================================

def secure_file_validation(

    uploaded_file: UploadFile

):

    validate_file_size(
        uploaded_file
    )

    validate_file_extension(
        uploaded_file
    )

    validate_filename(
        uploaded_file
    )

    scan_uploaded_file(
        uploaded_file
    )

    return True

# ==================================================
# LOGIN ATTEMPT TRACKER
# ==================================================

FAILED_LOGINS = {}

MAX_LOGIN_ATTEMPTS = 5

def check_login_limit(

    email: str

):

    count = FAILED_LOGINS.get(

        email,

        0

    )

    if count >= MAX_LOGIN_ATTEMPTS:

        raise HTTPException(

            status_code=429,

            detail=
            "Too many failed login attempts"

        )

def record_failed_login(

    email: str

):

    FAILED_LOGINS[email] = (

        FAILED_LOGINS.get(
            email,
            0
        ) + 1

    )

def reset_failed_login(

    email: str

):

    FAILED_LOGINS[email] = 0

print(
    "PipeGuard Security Layer Loaded"
)
# ==================================================
# PIPEGUARD AI V16
# PART 5
# SIGNUP + LOGIN
# ==================================================

# ==================================================
# SIGNUP
# ==================================================

@app.post("/signup")
@limiter.limit("5/minute")
def signup(

    request: Request,

    user: SignupRequest

):

    validate_email(
        user.email
    )

    validate_phone(
        user.phone
    )

    validate_password(
        user.password
    )

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT id
        FROM users
        WHERE email=?
        """,

        (
            user.email.lower(),
        )

    )

    existing_user = (
        cursor.fetchone()
    )

    if existing_user:

        conn.close()

        raise HTTPException(

            status_code=400,

            detail=
            "Email already exists"

        )

    hashed_password = (
        hash_password(
            user.password
        )
    )

    cursor.execute(

        """
        INSERT INTO users (

            full_name,
            company_name,
            phone,
            email,
            password,
            country_code,
            is_verified

        )

        VALUES (

            ?, ?, ?, ?, ?, ?, ?

        )
        """,

        (

            user.full_name,

            user.company_name,

            user.phone,

            user.email.lower(),

            hashed_password,

            user.country_code,

            1

        )

    )

    conn.commit()

    conn.close()

    add_audit_log(

        action="SIGNUP",

        user=user.email

    )

    token = create_access_token(
        user.email.lower()
    )

    create_user_session(
        user.email.lower()
    )

    return {

        "success": True,

        "message":
            "Account created successfully",

        "token":
            token

    }

# ==================================================
# LOGIN
# ==================================================

@app.post("/login")
@limiter.limit("10/minute")
def login(

    request: Request,

    user: LoginRequest

):

    check_login_limit(
        user.email.lower()
    )

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT

            id,
            email,
            password

        FROM users

        WHERE email=?
        """,

        (
            user.email.lower(),
        )

    )

    result = (
        cursor.fetchone()
    )

    conn.close()

    if not result:

        record_failed_login(
            user.email.lower()
        )

        raise HTTPException(

            status_code=401,

            detail=
            "Invalid email"

        )

    stored_password = (
        result[2]
    )

    if not verify_password(

        user.password,

        stored_password

    ):

        record_failed_login(
            user.email.lower()
        )

        raise HTTPException(

            status_code=401,

            detail=
            "Invalid password"

        )

    reset_failed_login(
        user.email.lower()
    )

    token = create_access_token(
        user.email.lower()
    )

    create_user_session(
        user.email.lower()
    )

    add_audit_log(

        action="LOGIN",

        user=user.email

    )

    return {

        "success": True,

        "token":
            token,

        "email":
            user.email,

        "message":
            "Login successful"

    }

# ==================================================
# USER EXISTS
# ==================================================

@app.get("/user-exists")
def user_exists(

    email: str

):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT id
        FROM users
        WHERE email=?
        """,

        (
            email.lower(),
        )

    )

    exists = (
        cursor.fetchone()
        is not None
    )

    conn.close()

    return {

        "exists":
            exists

    }

# ==================================================
# ACCOUNT STATS
# ==================================================

@app.get("/user-count")
def user_count(

    admin: str =
    Depends(require_admin)

):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT COUNT(*)
        FROM users
        """

    )

    count = (
        cursor.fetchone()[0]
    )

    conn.close()

    return {

        "total_users":
            count

    }

print(
    "PipeGuard Auth APIs Loaded"
)
# ==================================================
# PIPEGUARD AI V16
# PART 6
# PROFILE + ACCOUNT MANAGEMENT
# ==================================================

# ==================================================
# PROFILE
# ==================================================

@app.get("/profile")
def profile(

    email: str =
    Depends(get_current_user)

):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT

            full_name,
            company_name,
            phone,
            email,
            plan,
            created_at

        FROM users

        WHERE email=?

        """,

        (
            email,
        )

    )

    user = cursor.fetchone()

    conn.close()

    if not user:

        raise HTTPException(

            status_code=404,

            detail="User not found"

        )

    return {

        "full_name":
            user[0],

        "company_name":
            user[1],

        "phone":
            user[2],

        "email":
            user[3],

        "plan":
            user[4],

        "created_at":
            user[5]

    }

# ==================================================
# UPDATE PROFILE
# ==================================================

@app.put("/update-profile")
def update_profile(

    data: UpdateProfileRequest,

    email: str =
    Depends(get_current_user)

):

    conn = get_db()

    cursor = conn.cursor()

    if data.phone:

        validate_phone(
            data.phone
        )

    cursor.execute(

        """
        UPDATE users

        SET

            full_name=
            COALESCE(
                ?, full_name
            ),

            company_name=
            COALESCE(
                ?, company_name
            ),

            phone=
            COALESCE(
                ?, phone
            )

        WHERE email=?

        """,

        (

            data.full_name,

            data.company_name,

            data.phone,

            email

        )

    )

    conn.commit()

    conn.close()

    add_audit_log(

        action=
        "UPDATE_PROFILE",

        user=email

    )

    return {

        "success": True,

        "message":
            "Profile updated"

    }

# ==================================================
# CHANGE PASSWORD
# ==================================================

@app.post("/change-password")
def change_password(

    data:
    ChangePasswordRequest,

    email: str =
    Depends(get_current_user)

):

    validate_password(
        data.new_password
    )

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT password

        FROM users

        WHERE email=?

        """,

        (
            email,
        )

    )

    result = (
        cursor.fetchone()
    )

    if not result:

        conn.close()

        raise HTTPException(

            status_code=404,

            detail=
            "User not found"

        )

    stored_password = (
        result[0]
    )

    if not verify_password(

        data.old_password,

        stored_password

    ):

        conn.close()

        raise HTTPException(

            status_code=400,

            detail=
            "Old password incorrect"

        )

    new_hash = hash_password(

        data.new_password

    )

    cursor.execute(

        """
        UPDATE users

        SET password=?

        WHERE email=?

        """,

        (

            new_hash,

            email

        )

    )

    conn.commit()

    conn.close()

    add_audit_log(

        action=
        "CHANGE_PASSWORD",

        user=email

    )

    return {

        "success": True,

        "message":
            "Password changed"

    }

# ==================================================
# DELETE ACCOUNT
# ==================================================

@app.delete("/delete-account")
def delete_account(

    email: str =
    Depends(get_current_user)

):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        DELETE FROM users

        WHERE email=?

        """,

        (
            email,
        )

    )

    cursor.execute(

        """
        DELETE FROM pipeline_reports

        WHERE company_email=?

        """,

        (
            email,
        )

    )

    conn.commit()

    conn.close()

    destroy_user_session(
        email
    )

    add_audit_log(

        action=
        "DELETE_ACCOUNT",

        user=email

    )

    return {

        "success": True,

        "message":
            "Account deleted"

    }

# ==================================================
# MY WORKSPACE
# ==================================================

@app.get("/my-workspace")
def my_workspace(

    email: str =
    Depends(get_current_user)

):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT COUNT(*)

        FROM pipeline_reports

        WHERE company_email=?

        """,

        (
            email,
        )

    )

    total_reports = (
        cursor.fetchone()[0]
    )

    cursor.execute(

        """
        SELECT AVG(
            health_score
        )

        FROM pipeline_reports

        WHERE company_email=?

        """,

        (
            email,
        )

    )

    avg_score = (
        cursor.fetchone()[0]
    )

    conn.close()

    return {

        "email":
            email,

        "reports":
            total_reports,

        "average_health_score":
            round(
                avg_score or 0,
                2
            ),

        "active_session":
            True

    }

# ==================================================
# CURRENT USER DETAILS
# ==================================================

@app.get("/current-user-details")
def current_user_details(

    email: str =
    Depends(get_current_user)

):

    return {

        "email":
            email,

        "logged_in":
            True,

        "last_seen":
            ACTIVE_USERS.get(
                email
            )

    }

print(
    "PipeGuard Profile Layer Loaded"
)
# ==================================================
# PIPEGUARD AI V16
# PART 7
# UPLOAD ENGINE
# ==================================================

def load_uploaded_file(
    file: UploadFile
):

    filename = (
        file.filename.lower()
    )

    try:

        if filename.endswith(".csv"):

            return pd.read_csv(
                file.file
            )

        elif filename.endswith(
            ".xlsx"
        ):

            return pd.read_excel(
                file.file
            )

        elif filename.endswith(
            ".xls"
        ):

            return pd.read_excel(
                file.file
            )

        elif filename.endswith(
            ".json"
        ):

            return pd.read_json(
                file.file
            )

        elif filename.endswith(
            ".txt"
        ):

            return pd.read_csv(
                file.file,
                sep=None,
                engine="python"
            )

        else:

            raise HTTPException(

                status_code=400,

                detail=
                "Unsupported file"

            )

    except Exception as e:

        raise HTTPException(

            status_code=400,

            detail=
            f"Unable to read file: {e}"

        )

# ==================================================
# AUTO CLEANER
# ==================================================

def auto_clean_dataframe(

    df: pd.DataFrame

):

    report = {}

    before_rows = len(df)

    duplicates = (
        df.duplicated()
        .sum()
    )

    report[
        "duplicates_removed"
    ] = int(
        duplicates
    )

    df = df.drop_duplicates()

    missing_values = int(

        df.isnull()
        .sum()
        .sum()

    )

    report[
        "missing_values"
    ] = missing_values

    for column in df.columns:

        try:

            if (
                df[column]
                .dtype
                == "object"
            ):

                df[column] = (

                    df[column]

                    .astype(str)

                    .str.strip()

                )

        except:

            pass

    after_rows = len(df)

    report[
        "rows_before"
    ] = before_rows

    report[
        "rows_after"
    ] = after_rows

    return (

        df,

        report

    )

# ==================================================
# DATA QUALITY
# ==================================================

def calculate_health_score(

    df: pd.DataFrame

):

    rows = len(df)

    cols = len(df.columns)

    total_cells = (
        rows * cols
    )

    if total_cells == 0:

        return 0

    missing = int(

        df.isnull()
        .sum()
        .sum()

    )

    duplicates = int(

        df.duplicated()
        .sum()

    )

    missing_pct = (
        missing
        / total_cells
    ) * 100

    duplicate_pct = (
        duplicates
        / max(rows, 1)
    ) * 100

    score = 100

    score -= (
        missing_pct * 0.6
    )

    score -= (
        duplicate_pct * 0.4
    )

    score = max(
        0,
        min(
            100,
            round(score)
        )
    )

    return score

# ==================================================
# ISSUE DETECTOR
# ==================================================

def detect_issues(

    df: pd.DataFrame

):

    issues = []

    missing = int(

        df.isnull()
        .sum()
        .sum()

    )

    duplicates = int(

        df.duplicated()
        .sum()

    )

    if missing > 0:

        issues.append(

            f"{missing} missing values"

        )

    if duplicates > 0:

        issues.append(

            f"{duplicates} duplicate rows"

        )

    if len(df.columns) == 0:

        issues.append(
            "No columns detected"
        )

    return issues

# ==================================================
# UPLOAD API
# ==================================================

@app.post("/upload-pipeline")
@limiter.limit("20/minute")
def upload_pipeline(

    request: Request,

    pipeline_name: str,

    file: UploadFile = File(...),

    email: str =
    Depends(get_current_user)

):

    try:

        secure_file_validation(
            file
        )

        df = load_uploaded_file(
            file
        )

        cleaned_df, clean_report = (
            auto_clean_dataframe(
                df
            )
        )

        score = (
            calculate_health_score(
                cleaned_df
            )
        )

        issues = (
            detect_issues(
                cleaned_df
            )
        )

        conn = get_db()

        cursor = conn.cursor()

        cursor.execute(

            """
            INSERT INTO
            pipeline_reports (

                company_email,

                pipeline_name,

                file_type,

                health_score,

                issues,

                total_rows,

                total_columns

            )

            VALUES (

                ?, ?, ?, ?, ?, ?, ?

            )
            """,

            (

                email,

                pipeline_name,

                file.filename,

                score,

                json.dumps(
                    issues
                ),

                len(
                    cleaned_df
                ),

                len(
                    cleaned_df.columns
                )

            )

        )

        conn.commit()

        conn.close()

        MONITOR[
            "successful_uploads"
        ] += 1

        add_audit_log(

            action=
            "UPLOAD_PIPELINE",

            user=email

        )

        return {

            "success": True,

            "pipeline":
                pipeline_name,

            "health_score":
                score,

            "issues":
                issues,

            "clean_report":
                clean_report,

            "rows":
                len(
                    cleaned_df
                ),

            "columns":
                len(
                    cleaned_df.columns
                )

        }

    except Exception as e:

        MONITOR[
            "failed_uploads"
        ] += 1

        add_audit_log(

            action=
            "UPLOAD_FAILED",

            user=email,

            status="failed"

        )

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )

print(
    "PipeGuard Upload Engine Loaded"
)
# ==================================================
# PIPEGUARD AI V16
# PART 8
# AI DATA QUALITY ENGINE
# ==================================================

# ==================================================
# SCHEMA DRIFT
# ==================================================

def detect_schema_drift(
    df: pd.DataFrame
):

    drift = []

    for column in df.columns:

        dtype = str(
            df[column].dtype
        )

        drift.append({

            "column":
                column,

            "datatype":
                dtype

        })

    return drift

# ==================================================
# OUTLIER DETECTION
# ==================================================

def detect_outliers(
    df: pd.DataFrame
):

    results = {}

    numeric_cols = df.select_dtypes(
        include=["number"]
    ).columns

    for col in numeric_cols:

        try:

            q1 = (
                df[col]
                .quantile(0.25)
            )

            q3 = (
                df[col]
                .quantile(0.75)
            )

            iqr = q3 - q1

            lower = (
                q1 - 1.5 * iqr
            )

            upper = (
                q3 + 1.5 * iqr
            )

            outliers = df[
                (
                    df[col] < lower
                )
                |
                (
                    df[col] > upper
                )
            ]

            results[col] = len(
                outliers
            )

        except:
            pass

    return results

# ==================================================
# DATATYPE CORRECTION
# ==================================================

def auto_fix_datatypes(
    df: pd.DataFrame
):

    fixes = []

    for column in df.columns:

        try:

            if (
                df[column]
                .dtype
                == "object"
            ):

                converted = pd.to_numeric(

                    df[column],

                    errors="coerce"

                )

                numeric_count = (
                    converted
                    .notna()
                    .sum()
                )

                if numeric_count > (
                    len(df) * 0.8
                ):

                    df[column] = converted

                    fixes.append(

                        f"{column} converted to numeric"

                    )

        except:
            pass

    return df, fixes

# ==================================================
# EMAIL CLEANER
# ==================================================

def clean_email_columns(
    df: pd.DataFrame
):

    fixes = []

    for col in df.columns:

        if "email" in col.lower():

            try:

                before = len(df)

                df = df[
                    df[col]
                    .astype(str)
                    .str.contains(
                        "@",
                        na=False
                    )
                ]

                removed = (
                    before
                    - len(df)
                )

                if removed > 0:

                    fixes.append(

                        f"{removed} invalid emails removed"

                    )

            except:
                pass

    return df, fixes

# ==================================================
# PHONE CLEANER
# ==================================================

def clean_phone_columns(
    df: pd.DataFrame
):

    fixes = []

    for col in df.columns:

        if (
            "phone"
            in col.lower()
        ):

            try:

                before = len(df)

                df = df[
                    df[col]
                    .astype(str)
                    .str.len()
                    >= 10
                ]

                removed = (
                    before
                    - len(df)
                )

                if removed > 0:

                    fixes.append(

                        f"{removed} invalid phones removed"

                    )

            except:
                pass

    return df, fixes

# ==================================================
# AI RECOMMENDATIONS
# ==================================================

def generate_ai_recommendations(
    df: pd.DataFrame
):

    recommendations = []

    missing = int(
        df.isnull()
        .sum()
        .sum()
    )

    duplicates = int(
        df.duplicated()
        .sum()
    )

    if missing > 0:

        recommendations.append(
            "Fill missing values"
        )

    if duplicates > 0:

        recommendations.append(
            "Remove duplicate records"
        )

    if len(df.columns) > 50:

        recommendations.append(
            "High column count detected"
        )

    if len(df) > 100000:

        recommendations.append(
            "Large dataset optimization recommended"
        )

    return recommendations

# ==================================================
# SMART AI CLEANER
# ==================================================

def smart_ai_cleaner(
    df: pd.DataFrame
):

    report = {

        "datatype_fixes": [],
        "email_fixes": [],
        "phone_fixes": [],
        "outliers": {},
        "schema": [],
        "recommendations": []

    }

    df, datatype_fixes = (
        auto_fix_datatypes(
            df
        )
    )

    report[
        "datatype_fixes"
    ] = datatype_fixes

    df, email_fixes = (
        clean_email_columns(
            df
        )
    )

    report[
        "email_fixes"
    ] = email_fixes

    df, phone_fixes = (
        clean_phone_columns(
            df
        )
    )

    report[
        "phone_fixes"
    ] = phone_fixes

    report[
        "outliers"
    ] = detect_outliers(
        df
    )

    report[
        "schema"
    ] = detect_schema_drift(
        df
    )

    report[
        "recommendations"
    ] = generate_ai_recommendations(
        df
    )

    return df, report

# ==================================================
# AI ANALYSIS API
# ==================================================

@app.post("/ai-quality-check")
def ai_quality_check(

    file: UploadFile = File(...),

    email: str =
    Depends(get_current_user)

):

    secure_file_validation(
        file
    )

    df = load_uploaded_file(
        file
    )

    cleaned_df, report = (
        smart_ai_cleaner(
            df
        )
    )

    return {

        "success": True,

        "rows":
            len(cleaned_df),

        "columns":
            len(
                cleaned_df.columns
            ),

        "analysis":
            report

    }

print(
    "PipeGuard AI Engine Loaded"
)
# ==================================================
# PIPEGUARD AI V16
# PART 9
# REPORTS + DASHBOARD
# ==================================================

# ==================================================
# MY REPORTS
# ==================================================

@app.get("/my-reports")
def my_reports(

    email: str =
    Depends(get_current_user)

):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT

            id,
            pipeline_name,
            health_score,
            total_rows,
            total_columns,
            created_at

        FROM pipeline_reports

        WHERE company_email=?

        ORDER BY id DESC

        """,

        (
            email,
        )

    )

    reports = cursor.fetchall()

    conn.close()

    data = []

    for row in reports:

        data.append({

            "id":
                row[0],

            "pipeline_name":
                row[1],

            "health_score":
                row[2],

            "rows":
                row[3],

            "columns":
                row[4],

            "created_at":
                row[5]

        })

    return {

        "count":
            len(data),

        "reports":
            data

    }

# ==================================================
# REPORT DETAILS
# ==================================================

@app.get("/report/{report_id}")
def report_details(

    report_id: int,

    email: str =
    Depends(get_current_user)

):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT *

        FROM pipeline_reports

        WHERE id=?
        AND company_email=?

        """,

        (

            report_id,
            email

        )

    )

    report = cursor.fetchone()

    conn.close()

    if not report:

        raise HTTPException(

            status_code=404,

            detail=
            "Report not found"

        )

    return {

        "id":
            report[0],

        "company_email":
            report[1],

        "pipeline_name":
            report[2],

        "file_type":
            report[3],

        "health_score":
            report[4],

        "issues":
            report[5],

        "rows":
            report[6],

        "columns":
            report[7],

        "created_at":
            report[8]

    }

# ==================================================
# DELETE REPORT
# ==================================================

@app.delete("/delete-report/{report_id}")
def delete_report(

    report_id: int,

    email: str =
    Depends(get_current_user)

):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        DELETE FROM
        pipeline_reports

        WHERE id=?
        AND company_email=?

        """,

        (

            report_id,
            email

        )

    )

    conn.commit()

    conn.close()

    add_audit_log(

        action=
        "DELETE_REPORT",

        user=email

    )

    return {

        "success": True,

        "message":
            "Report deleted"

    }

# ==================================================
# SEARCH REPORTS
# ==================================================

@app.get("/search-reports")
def search_reports(

    keyword: str,

    email: str =
    Depends(get_current_user)

):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT

            id,
            pipeline_name,
            health_score

        FROM pipeline_reports

        WHERE

        company_email=?

        AND pipeline_name
        LIKE ?

        """,

        (

            email,

            f"%{keyword}%"

        )

    )

    results = cursor.fetchall()

    conn.close()

    return {

        "count":
            len(results),

        "results":
            results

    }

# ==================================================
# PIPELINE COUNT
# ==================================================

@app.get("/pipeline-count")
def pipeline_count(

    email: str =
    Depends(get_current_user)

):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT COUNT(*)

        FROM pipeline_reports

        WHERE company_email=?

        """,

        (
            email,
        )

    )

    count = cursor.fetchone()[0]

    conn.close()

    return {

        "pipelines":
            count

    }

# ==================================================
# REPORT COUNT
# ==================================================

@app.get("/report-count")
def report_count(

    email: str =
    Depends(get_current_user)

):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT COUNT(*)

        FROM pipeline_reports

        WHERE company_email=?

        """,

        (
            email,
        )

    )

    total = cursor.fetchone()[0]

    conn.close()

    return {

        "total_reports":
            total

    }

# ==================================================
# DASHBOARD STATS
# ==================================================

@app.get("/dashboard-stats")
def dashboard_stats(

    email: str =
    Depends(get_current_user)

):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT

        COUNT(*),
        AVG(health_score)

        FROM pipeline_reports

        WHERE company_email=?

        """,

        (
            email,
        )

    )

    stats = cursor.fetchone()

    total_reports = stats[0]

    avg_score = round(
        stats[1] or 0,
        2
    )

    conn.close()

    return {

        "total_reports":
            total_reports,

        "average_health_score":
            avg_score,

        "successful_uploads":
            MONITOR[
                "successful_uploads"
            ],

        "failed_uploads":
            MONITOR[
                "failed_uploads"
            ]

    }

# ==================================================
# SYSTEM STATS
# ==================================================

@app.get("/system-stats")
def system_stats(

    admin: str =
    Depends(require_admin)

):

    return {

        "cpu":
            psutil.cpu_percent(),

        "ram":
            psutil.virtual_memory().percent,

        "disk":
            psutil.disk_usage("/").percent,

        "uptime":
            get_uptime(),

        "health_score":
            system_health_score(),

        "active_users":
            len(
                ACTIVE_USERS
            ),

        "requests":
            MONITOR[
                "total_requests"
            ],

        "errors":
            MONITOR[
                "total_errors"
            ]

    }

# ==================================================
# GLOBAL USER COUNT
# ==================================================

@app.get("/all-users")
def all_users(

    admin: str =
    Depends(require_admin)

):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT

        id,
        full_name,
        email,
        plan

        FROM users

        ORDER BY id DESC

        """

    )

    users = cursor.fetchall()

    conn.close()

    return {

        "count":
            len(users),

        "users":
            users

    }

print(
    "PipeGuard Report Layer Loaded"
)
# ==================================================
# PIPEGUARD AI V16
# PART 10
# SELF MONITORING ENGINE
# ==================================================

import threading

# ==================================================
# SYSTEM ALERTS
# ==================================================

SYSTEM_ALERTS = []

# ==================================================
# SELF HEAL STATUS
# ==================================================

SELF_HEAL_STATS = {

    "database_reconnects": 0,

    "memory_cleanups": 0,

    "high_cpu_events": 0,

    "critical_alerts": 0

}

# ==================================================
# ALERT LOGGER
# ==================================================

def create_alert(

    level: str,

    message: str

):

    SYSTEM_ALERTS.append({

        "time":
            str(datetime.utcnow()),

        "level":
            level,

        "message":
            message

    })

    if level == "CRITICAL":

        SELF_HEAL_STATS[
            "critical_alerts"
        ] += 1

# ==================================================
# DATABASE CHECK
# ==================================================

def database_alive():

    try:

        conn = get_db()

        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1"
        )

        conn.close()

        return True

    except:

        return False

# ==================================================
# AUTO DATABASE RECOVERY
# ==================================================

def auto_reconnect_database():

    try:

        conn = get_db()

        conn.close()

        SELF_HEAL_STATS[
            "database_reconnects"
        ] += 1

        create_alert(

            "INFO",

            "Database reconnected"

        )

    except:

        create_alert(

            "CRITICAL",

            "Database recovery failed"

        )

# ==================================================
# MEMORY CHECK
# ==================================================

def monitor_memory():

    ram = (

        psutil.virtual_memory()
        .percent

    )

    if ram > 90:

        SELF_HEAL_STATS[
            "memory_cleanups"
        ] += 1

        create_alert(

            "WARNING",

            f"High RAM Usage {ram}%"

        )

# ==================================================
# CPU CHECK
# ==================================================

def monitor_cpu():

    cpu = psutil.cpu_percent()

    if cpu > 90:

        SELF_HEAL_STATS[
            "high_cpu_events"
        ] += 1

        create_alert(

            "WARNING",

            f"High CPU Usage {cpu}%"

        )

# ==================================================
# DISK CHECK
# ==================================================

def monitor_disk():

    disk = (

        psutil.disk_usage("/")
        .percent

    )

    if disk > 90:

        create_alert(

            "CRITICAL",

            f"Disk usage critical {disk}%"

        )

# ==================================================
# HEALTH CHECK LOOP
# ==================================================

def self_monitor_loop():

    while True:

        try:

            if not database_alive():

                auto_reconnect_database()

            monitor_memory()

            monitor_cpu()

            monitor_disk()

        except Exception as e:

            create_alert(

                "ERROR",

                str(e)

            )

        time.sleep(60)

# ==================================================
# START MONITOR
# ==================================================

@app.on_event("startup")
async def start_self_monitor():

    monitor_thread = threading.Thread(

        target=self_monitor_loop,

        daemon=True

    )

    monitor_thread.start()

# ==================================================
# MONITOR DASHBOARD
# ==================================================

@app.get("/self-monitor")
def self_monitor():

    return {

        "uptime":
            get_uptime(),

        "cpu":
            psutil.cpu_percent(),

        "ram":
            psutil.virtual_memory().percent,

        "disk":
            psutil.disk_usage("/").percent,

        "health_score":
            system_health_score(),

        "self_heal":
            SELF_HEAL_STATS,

        "alerts":
            len(
                SYSTEM_ALERTS
            )

    }

# ==================================================
# ALERTS
# ==================================================

@app.get("/system-alerts")
def system_alerts(

    admin: str =
    Depends(require_admin)

):

    return {

        "count":
            len(
                SYSTEM_ALERTS
            ),

        "alerts":
            SYSTEM_ALERTS[-100:]

    }

# ==================================================
# HEALTH SCORE API
# ==================================================

@app.get("/system-health-score")
def health_score_api():

    return {

        "health_score":
            system_health_score(),

        "status":
            "healthy"

            if system_health_score() > 70

            else

            "warning"

    }

# ==================================================
# READY CHECK
# ==================================================

@app.get("/ready")
def ready():

    return {

        "ready": True,

        "database":
            database_alive(),

        "uptime":
            get_uptime()

    }

# ==================================================
# PING
# ==================================================

@app.get("/ping")
def ping():

    return {

        "message":
            "pong"

    }

print(
    "PipeGuard Self Monitoring Loaded"
)
# ==================================================
# PIPEGUARD AI V16
# PART 11
# PRODUCTION LAYER
# ==================================================

from fastapi.responses import (
    JSONResponse
)

# ==================================================
# VERSION
# ==================================================

APP_VERSION = "16.0"

# ==================================================
# GLOBAL EXCEPTION HANDLER
# ==================================================

@app.exception_handler(Exception)
async def global_exception_handler(

    request: Request,

    exc: Exception

):

    MONITOR[
        "total_errors"
    ] += 1

    logger.error(

        f"GLOBAL ERROR: {str(exc)}"

    )

    logger.error(

        traceback.format_exc()

    )

    return JSONResponse(

        status_code=500,

        content={

            "success": False,

            "error":
                "Internal server error",

            "request_path":
                str(request.url.path)

        }

    )

# ==================================================
# HTTP EXCEPTION HANDLER
# ==================================================

@app.exception_handler(
    HTTPException
)
async def http_exception_handler(

    request: Request,

    exc: HTTPException

):

    return JSONResponse(

        status_code=
        exc.status_code,

        content={

            "success":
                False,

            "detail":
                exc.detail

        }

    )

# ==================================================
# ROOT
# ==================================================

@app.get("/")
def home():

    return {

        "application":
            "PipeGuard AI",

        "version":
            APP_VERSION,

        "status":
            "running",

        "health_score":
            system_health_score()

    }

# ==================================================
# HEALTH
# ==================================================

@app.get("/health")
def health():

    db_ok = (
        database_alive()
    )

    return {

        "status":

            "healthy"

            if db_ok

            else

            "warning",

        "database":

            "connected"

            if db_ok

            else

            "disconnected",

        "uptime":
            get_uptime(),

        "version":
            APP_VERSION

    }

# ==================================================
# API STATUS
# ==================================================

@app.get("/api-status")
def api_status():

    return {

        "running":
            True,

        "version":
            APP_VERSION,

        "cpu":
            psutil.cpu_percent(),

        "ram":
            psutil.virtual_memory().percent,

        "requests":
            MONITOR[
                "total_requests"
            ]

    }

# ==================================================
# VERSION
# ==================================================

@app.get("/version")
def version():

    return {

        "version":
            APP_VERSION

    }

# ==================================================
# TEST
# ==================================================

@app.get("/test")
def test():

    return {

        "message":
            "PipeGuard API Working"

    }

# ==================================================
# SUPPORTED FILES
# ==================================================

@app.get("/supported-files")
def supported_files():

    return {

        "supported_files": [

            "csv",
            "xlsx",
            "xls",
            "json",
            "txt"

        ]

    }

# ==================================================
# STARTUP VALIDATION
# ==================================================

@app.on_event("startup")
async def startup_validation():

    try:

        create_tables()

        logger.info(
            "Database Ready"
        )

        logger.info(
            f"PipeGuard AI {APP_VERSION}"
        )

    except Exception as e:

        logger.error(
            str(e)
        )

# ==================================================
# SECURITY REPORT
# ==================================================

@app.get("/security-report")
def security_report(

    admin: str =
    Depends(require_admin)

):

    return {

        "jwt_enabled":
            True,

        "rate_limit":
            True,

        "upload_protection":
            True,

        "audit_logs":
            len(
                AUDIT_LOGS
            ),

        "health_score":
            system_health_score()

    }

# ==================================================
# CLEANUP TASK
# ==================================================

@app.on_event("startup")
async def cleanup_task():

    try:

        if len(
            SYSTEM_ALERTS
        ) > 1000:

            SYSTEM_ALERTS.clear()

        if len(
            USER_ACTIVITY
        ) > 5000:

            USER_ACTIVITY.clear()

    except:

        pass

# ==================================================
# FINAL STARTUP LOG
# ==================================================

print(
    "=" * 50
)

print(
    "PIPEGUARD AI V16 STARTED"
)

print(
    "=" * 50
)
