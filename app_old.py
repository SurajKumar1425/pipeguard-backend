import os
import json
import time
import logging
import threading

from datetime import datetime
from random import randint
from typing import Optional

import pandas as pd
import psutil

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    UploadFile,
    File,
    Request
)

from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from pydantic import (
    BaseModel,
    EmailStr
)

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from email_validator import (
    validate_email,
    EmailNotValidError
)

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

# =========================
# APP CONFIG
# =========================

APP_NAME = "PipeGuard AI"

APP_VERSION = "18.0"

logging.basicConfig(

    level=logging.INFO,

    format="%(asctime)s | %(levelname)s | %(message)s"

)

logger = logging.getLogger(
    "PipeGuard"
)

# =========================
# FASTAPI
# =========================

app = FastAPI(

    title=APP_NAME,

    description="AI Powered Data Reliability Platform",

    version=APP_VERSION

)

# =========================
# CORS
# =========================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[

        "http://localhost:5173",

        "http://127.0.0.1:5173",

        "https://pipeguard-dashboard.vercel.app"

    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

)

# =========================
# RATE LIMITER
# =========================

limiter = Limiter(

    key_func=get_remote_address

)

app.state.limiter = limiter

# =========================
# SECURITY
# =========================

security = HTTPBearer()

# =========================
# DATABASE
# =========================

create_tables()

# =========================
# MEMORY STORE
# =========================

ACTIVE_USERS = {}

OTP_STORE = {}

SYSTEM_ALERTS = []

AUDIT_LOGS = []

SERVER_START_TIME = time.time()

# =========================
# MONITOR
# =========================

MONITOR = {

    "total_requests": 0,

    "successful_uploads": 0,

    "failed_uploads": 0,

    "total_errors": 0

}

SELF_HEAL_STATS = {

    "high_cpu_events": 0,

    "high_memory_events": 0,

    "database_failures": 0,

    "alerts_generated": 0

}

# =========================
# STARTUP
# =========================

@app.on_event("startup")
async def startup():

    create_tables()

    logger.info(

        f"{APP_NAME} V{APP_VERSION} Started"

    )

# =========================
# RATE LIMIT HANDLER
# =========================

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

            "detail": "Too many requests"

        }

    )

# =========================
# REQUEST LOGGER
# =========================

@app.middleware("http")
async def request_logger(

    request: Request,

    call_next

):

    start = time.time()

    MONITOR["total_requests"] += 1

    try:

        response = await call_next(
            request
        )

        duration = round(

            time.time() - start,

            3

        )

        logger.info(

            f"{request.method} "

            f"{request.url.path} "

            f"{response.status_code} "

            f"{duration}s"

        )

        return response

    except Exception as e:

        MONITOR["total_errors"] += 1

        logger.error(str(e))

        raise

# =========================
# NEXT SECTION
# =========================
# =========================
# REQUEST MODELS
# =========================

class SignupRequest(BaseModel):

    full_name: str

    company_name: Optional[str] = ""

    phone: str

    email: EmailStr

    password: str

    country_code: str = "+91"


class LoginRequest(BaseModel):

    email: EmailStr

    password: str


class ChangePasswordRequest(BaseModel):

    old_password: str

    new_password: str


class UpdateProfileRequest(BaseModel):

    full_name: Optional[str] = None

    company_name: Optional[str] = None

    phone: Optional[str] = None


# =========================
# PASSWORD VALIDATION
# =========================

def validate_password_strength(

    password: str

):

    if len(password) < 8:

        raise HTTPException(

            status_code=400,

            detail="Password must contain at least 8 characters"

        )

    has_upper = any(

        c.isupper()

        for c in password

    )

    has_lower = any(

        c.islower()

        for c in password

    )

    has_digit = any(

        c.isdigit()

        for c in password

    )

    if not (

        has_upper
        and has_lower
        and has_digit

    ):

        raise HTTPException(

            status_code=400,

            detail="Password must contain uppercase, lowercase and number"

        )


# =========================
# PHONE VALIDATION
# =========================

def validate_phone_number(

    phone: str

):

    digits = "".join(

        c

        for c in phone

        if c.isdigit()

    )

    if len(digits) != 10:

        raise HTTPException(

            status_code=400,

            detail="Invalid phone number"

        )


# =========================
# USER SESSION
# =========================

def create_user_session(

    email: str

):

    ACTIVE_USERS[email] = {

        "login_time": str(

            datetime.utcnow()

        )

    }


def destroy_user_session(

    email: str

):

    ACTIVE_USERS.pop(

        email,

        None

    )


# =========================
# CURRENT USER
# =========================

def get_current_user(

    credentials:

    HTTPAuthorizationCredentials

    = Depends(security)

):

    token = credentials.credentials

    email = verify_token(

        token

    )

    if email is None:

        raise HTTPException(

            status_code=401,

            detail="Invalid or Expired Token"

        )

    return email


# =========================
# ADMIN AUTH
# =========================

def require_admin(

    email: str =

    Depends(

        get_current_user

    )

):

    if email != "admin@pipeguard.ai":

        raise HTTPException(

            status_code=403,

            detail="Admin Access Required"

        )

    return email


# =========================
# OTP
# =========================

def generate_otp():

    return str(

        randint(

            100000,

            999999

        )

    )


# =========================
# NEXT SECTION
# =========================
# =========================
# SIGNUP
# =========================

@app.post("/signup")
@limiter.limit("5/minute")
def signup(

    request: Request,

    user: SignupRequest

):

    validate_phone_number(
        user.phone
    )

    validate_password_strength(
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
        INSERT INTO users(

            full_name,

            company_name,

            phone,

            email,

            password,

            country_code,

            is_verified

        )

        VALUES(

            ?,?,?,?,?,?,?

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

    token = create_access_token(

        user.email.lower()

    )

    create_user_session(

        user.email.lower()

    )

    return {

        "success": True,

        "message": "Signup Successful",

        "token": token,

        "email": user.email.lower()

    }


# =========================
# LOGIN
# =========================

@app.post("/login")
@limiter.limit("10/minute")
def login(

    request: Request,

    user: LoginRequest

):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT password

        FROM users

        WHERE email=?

        """,

        (

            user.email.lower(),

        )

    )

    result = cursor.fetchone()

    conn.close()

    if not result:

        raise HTTPException(

            status_code=401,

            detail="Invalid Email"

        )

    if not verify_password(

        user.password,

        result[0]

    ):

        raise HTTPException(

            status_code=401,

            detail="Invalid Password"

        )

    token = create_access_token(

        user.email.lower()

    )

    create_user_session(

        user.email.lower()

    )

    return {

        "success": True,

        "token": token,

        "email": user.email.lower()

    }


# =========================
# LOGOUT
# =========================

@app.post("/logout")
def logout(

    email: str =

    Depends(

        get_current_user

    )

):

    destroy_user_session(

        email

    )

    return {

        "success": True,

        "message": "Logout Successful"

    }


# =========================
# TOKEN VALIDATION
# =========================

@app.get("/validate-token")
def validate_token(

    email: str =

    Depends(

        get_current_user

    )

):

    return {

        "success": True,

        "valid": True,

        "email": email

    }


# =========================
# NEXT SECTION
# =========================
# =========================
# CURRENT USER
# =========================

@app.get("/current-user")
def current_user(

    email: str =
    Depends(get_current_user)

):

    return {

        "success": True,

        "email": email

    }


# =========================
# PROFILE
# =========================

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

        "success": True,

        "full_name": user[0],

        "company_name": user[1],

        "phone": user[2],

        "email": user[3],

        "plan": user[4],

        "created_at": user[5]

    }


# =========================
# UPDATE PROFILE
# =========================

@app.put("/update-profile")
def update_profile(

    data: UpdateProfileRequest,

    email: str =
    Depends(get_current_user)

):

    if data.phone:

        validate_phone_number(

            data.phone

        )

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        UPDATE users

        SET

        full_name=COALESCE(?,full_name),

        company_name=COALESCE(?,company_name),

        phone=COALESCE(?,phone)

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

    return {

        "success": True,

        "message": "Profile Updated"

    }


# =========================
# CHANGE PASSWORD
# =========================

@app.post("/change-password")
def change_password(

    data: ChangePasswordRequest,

    email: str =
    Depends(get_current_user)

):

    validate_password_strength(

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

    result = cursor.fetchone()

    if not result:

        conn.close()

        raise HTTPException(

            status_code=404,

            detail="User not found"

        )

    if not verify_password(

        data.old_password,

        result[0]

    ):

        conn.close()

        raise HTTPException(

            status_code=400,

            detail="Old password incorrect"

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

    return {

        "success": True,

        "message": "Password Changed"

    }


# =========================
# DELETE ACCOUNT
# =========================

@app.delete("/delete-account")
def delete_account(

    email: str =
    Depends(get_current_user)

):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        "DELETE FROM users WHERE email=?",

        (

            email,

        )

    )

    cursor.execute(

        "DELETE FROM pipeline_reports WHERE company_email=?",

        (

            email,

        )

    )

    conn.commit()

    conn.close()

    destroy_user_session(

        email

    )

    return {

        "success": True,

        "message": "Account Deleted"

    }


# =========================
# NEXT SECTION
# =========================
# =========================
# FILE SETTINGS
# =========================

ALLOWED_EXTENSIONS = {

    ".csv",

    ".xlsx",

    ".xls",

    ".json",

    ".txt"

}

MAX_FILE_SIZE_MB = 20


# =========================
# VALIDATE FILE
# =========================

def validate_file(

    file: UploadFile

):

    filename = file.filename.lower()

    extension = os.path.splitext(

        filename

    )[1]

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(

            status_code=400,

            detail="Unsupported file format"

        )

    return extension


# =========================
# LOAD FILE
# =========================

def load_file(

    file: UploadFile,

    extension: str

):

    try:

        if extension == ".csv":

            return pd.read_csv(

                file.file

            )

        if extension in [

            ".xlsx",

            ".xls"

        ]:

            return pd.read_excel(

                file.file

            )

        if extension == ".json":

            return pd.read_json(

                file.file

            )

        if extension == ".txt":

            return pd.read_csv(

                file.file,

                sep=None,

                engine="python"

            )

    except Exception as e:

        raise HTTPException(

            status_code=400,

            detail=f"Unable to read file : {str(e)}"

        )


# =========================
# HEALTH SCORE
# =========================

def calculate_health_score(

    df: pd.DataFrame

):

    rows = len(df)

    if rows == 0:

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

    total_cells = max(

        rows * len(df.columns),

        1

    )

    missing_percent = (

        missing / total_cells

    ) * 100

    duplicate_percent = (

        duplicates / rows

    ) * 100

    score = 100

    score -= (

        missing_percent * 0.6

    )

    score -= (

        duplicate_percent * 0.4

    )

    return max(

        0,

        round(score)

    )


# =========================
# NEXT SECTION
# =========================
# =========================
# DETECT ISSUES
# =========================

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

            f"{missing} Missing Values"

        )

    if duplicates > 0:

        issues.append(

            f"{duplicates} Duplicate Rows"

        )

    for column in df.columns:

        try:

            null_percent = (

                df[column]

                .isnull()

                .mean()

            ) * 100

            if null_percent > 50:

                issues.append(

                    f"{column} has more than 50% null values"

                )

        except:

            pass

    return issues


# =========================
# AUTO CLEAN
# =========================

def auto_clean_dataframe(

    df: pd.DataFrame

):

    report = {}

    report["rows_before"] = len(df)

    report["duplicates_removed"] = int(

        df.duplicated()

        .sum()

    )

    df = df.drop_duplicates()

    for column in df.columns:

        try:

            if df[column].dtype == "object":

                df[column] = (

                    df[column]

                    .astype(str)

                    .str.strip()

                )

        except:

            pass

    report["rows_after"] = len(df)

    return df, report


# =========================
# UPLOAD PIPELINE
# =========================

@app.post("/upload-pipeline")
@limiter.limit("20/minute")
def upload_pipeline(

    request: Request,

    pipeline_name: str,

    file: UploadFile = File(...),

    email: str = Depends(get_current_user)

):

    extension = validate_file(

        file

    )

    df = load_file(

        file,

        extension

    )

    original_rows = len(df)

    cleaned_df, clean_report = auto_clean_dataframe(

        df

    )

    health_score = calculate_health_score(

        cleaned_df

    )

    issues = detect_issues(

        cleaned_df

    )

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """

        INSERT INTO pipeline_reports(

            company_email,

            pipeline_name,

            file_type,

            health_score,

            issues,

            total_rows,

            total_columns

        )

        VALUES(

            ?,?,?,?,?,?,?

        )

        """,

        (

            email,

            pipeline_name,

            extension,

            health_score,

            json.dumps(issues),

            len(cleaned_df),

            len(cleaned_df.columns)

        )

    )

    conn.commit()

    conn.close()

    MONITOR["successful_uploads"] += 1

    return {

        "success": True,

        "pipeline_name": pipeline_name,

        "health_score": health_score,

        "issues": issues,

        "rows": len(cleaned_df),

        "columns": len(cleaned_df.columns),

        "clean_report": clean_report,

        "original_rows": original_rows

    }


# =========================
# NEXT SECTION
# =========================
