# =========================
# IMPORTS
# =========================

import io
import re
import json
import base64
import datetime

from typing import (
    List,
    Dict,
    Any,
    Tuple,
    Optional
)

# =========================
# FASTAPI
# =========================

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    UploadFile,
    File,
    status
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from fastapi.middleware.cors import (
    CORSMiddleware
)

# =========================
# PYDANTIC
# =========================

from pydantic import (
    BaseModel,
    EmailStr,
    Field
)

# =========================
# DATA PROCESSING
# =========================

import pandas as pd

# =========================
# DATABASE
# =========================

from database import (
    get_db,
    create_tables
)

# =========================
# AUTH
# =========================

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)

# =========================
# TEMP EMAIL BLACKLIST
# =========================

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
    "burnermail.com",
    "tempmailaddress.com"

}

# =========================
# BLOCKED PHONES
# =========================

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

# =========================
# REGEX
# =========================

EMAIL_REGEX = re.compile(

    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

)

PHONE_REGEX = re.compile(

    r"^[6-9]\d{9}$"

<<<<<<< HEAD
)

# =========================
# FASTAPI APP
# =========================

app = FastAPI(

    title="PipeGuard AI",

    description=
    "AI Data Quality Platform",

    version="15.0"

)

# =========================
# CORS
# =========================

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

# =========================
=======

# =========================
# FASTAPI APP
# =========================

app = FastAPI(

    title="PipeGuard AI",

    description=
    "AI Data Quality Platform",

    version="15.0"

)

# =========================
# CORS
# =========================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

)

# =========================
>>>>>>> 8c6eff2 (fix upload api)
# DATABASE INIT
# =========================

create_tables()

security = HTTPBearer()

# =========================
# MODELS
# =========================

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
    # =========================
# PASSWORD VALIDATION
# =========================

def validate_password(
    password: str
):

    if len(password) < 8:

        raise HTTPException(
            status_code=400,
            detail=
            "Password must be at least 8 characters"
        )

    if not re.search(
        r"[A-Z]",
        password
    ):

        raise HTTPException(
            status_code=400,
            detail=
            "Password must contain one uppercase letter"
        )

    if not re.search(
        r"[a-z]",
        password
    ):

        raise HTTPException(
            status_code=400,
            detail=
            "Password must contain one lowercase letter"
        )

    if not re.search(
        r"\d",
        password
    ):

        raise HTTPException(
            status_code=400,
            detail=
            "Password must contain one number"
        )

    return True


# =========================
# FILE VALIDATION
# =========================

def validate_uploaded_file(
    uploaded_file: UploadFile
):

    allowed_extensions = [

        ".csv",
        ".xlsx",
        ".xls",
        ".json",
        ".txt"

    ]

    filename = (
        uploaded_file.filename
        .lower()
    )

    if not any(
        filename.endswith(ext)
        for ext in allowed_extensions
    ):

        raise HTTPException(
            status_code=400,
            detail=
            "Supported formats: CSV, XLSX, XLS, JSON, TXT"
        )

    return True


# =========================
# FILE LOADER
# =========================

def load_file(
    uploaded_file: UploadFile
) -> Tuple[pd.DataFrame, str]:

    filename = (
        uploaded_file.filename
        .lower()
    )

    try:

        file_bytes = (
            uploaded_file.file.read()
        )

        uploaded_file.file.seek(0)

        buffer = io.BytesIO(
            file_bytes
        )

        # CSV

        if filename.endswith(".csv"):

            df = pd.read_csv(
                buffer
            )

            return df, "csv"

        # XLSX

        elif filename.endswith(".xlsx"):

            df = pd.read_excel(
                buffer,
                engine="openpyxl"
            )

            return df, "xlsx"

        # XLS

        elif filename.endswith(".xls"):

            df = pd.read_excel(
                buffer,
                engine="xlrd"
            )

            return df, "xls"

        # JSON

        elif filename.endswith(".json"):

            df = pd.read_json(
                buffer
            )

            return df, "json"

        # TXT

        elif filename.endswith(".txt"):

            df = pd.read_csv(
                buffer,
                sep=None,
                engine="python"
            )

            return df, "txt"

        else:

            raise HTTPException(
                status_code=400,
                detail=
                "Unsupported file format"
            )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=
            f"File processing failed: {str(e)}"
        )


# =========================
# DATA ANALYSIS
# =========================

def analyze_dataframe(
    df: pd.DataFrame
):

    total_rows = len(df)

    total_columns = len(
        df.columns
    )

    missing_values = int(
        df.isnull()
        .sum()
        .sum()
    )

    duplicate_rows = int(
        df.duplicated()
        .sum()
    )

    empty_columns = []

    for col in df.columns:

        if df[col].isnull().all():

            empty_columns.append(
                str(col)
            )

    return {

        "total_rows":
            total_rows,

        "total_columns":
            total_columns,

        "missing_values":
            missing_values,

        "duplicate_rows":
            duplicate_rows,

        "empty_columns":
            empty_columns

    }
    # =========================
# CLEAN DATAFRAME
# =========================

def clean_dataframe(
    df: pd.DataFrame
):

    cleaned_df = df.copy()

    cleaning_log = []

    # =====================
    # REMOVE DUPLICATES
    # =====================

    before_rows = len(
        cleaned_df
    )

    cleaned_df = (
        cleaned_df
        .drop_duplicates()
    )

    removed_duplicates = (
        before_rows
        - len(cleaned_df)
    )

    if removed_duplicates > 0:

        cleaning_log.append(

            f"{removed_duplicates} duplicate rows removed"

        )

    # =====================
    # TRIM SPACES
    # =====================

    object_columns = (

        cleaned_df

        .select_dtypes(
            include=["object"]
        )

        .columns

    )

    for col in object_columns:

        cleaned_df[col] = (

            cleaned_df[col]

            .astype(str)

            .str.strip()

        )

    cleaning_log.append(
        "Extra spaces removed"
    )

    # =====================
    # HANDLE NULL VALUES
    # =====================

    for col in cleaned_df.columns:

        if (
            cleaned_df[col]
            .dtype == "object"
        ):

            cleaned_df[col] = (

                cleaned_df[col]

                .fillna(
                    "Unknown"
                )

            )

        else:

            if not (
                cleaned_df[col]
                .isnull()
                .all()
            ):

                cleaned_df[col] = (

                    cleaned_df[col]

                    .fillna(
                        cleaned_df[col]
                        .median()
                    )

                )

            else:

                cleaned_df[col] = (

                    cleaned_df[col]

                    .fillna(0)

                )

    cleaning_log.append(
        "Missing values handled"
    )

    # =====================
    # STANDARDIZE EMAILS
    # =====================

    email_columns = [

        col

        for col in cleaned_df.columns

        if "email"
        in str(col).lower()

    ]

    for col in email_columns:

        cleaned_df[col] = (

            cleaned_df[col]

            .astype(str)

            .str.lower()

            .str.strip()

        )

    if len(email_columns) > 0:

        cleaning_log.append(
            "Emails standardized"
        )

    # =====================
    # STANDARDIZE PHONES
    # =====================

    phone_columns = [

        col

        for col in cleaned_df.columns

        if (

            "phone"
            in str(col).lower()

            or

            "mobile"
            in str(col).lower()

        )

    ]

    for col in phone_columns:

        cleaned_df[col] = (

            cleaned_df[col]

            .astype(str)

            .str.replace(
                ".0",
                "",
                regex=False
            )

            .str.replace(
                " ",
                "",
                regex=False
            )

        )

    if len(phone_columns) > 0:

        cleaning_log.append(
            "Phone numbers standardized"
        )

    return {

        "dataframe":
            cleaned_df,

        "log":
            cleaning_log

    }


# =========================
# HEALTH SCORE
# =========================

def calculate_health_score(
    analysis
):

    score = 100

    score -= (
        analysis["missing_values"]
        * 0.3
    )

    score -= (
        analysis["duplicate_rows"]
        * 1
    )

    score -= (
        len(
            analysis[
                "empty_columns"
            ]
        ) * 2
    )

    score = max(
        0,
        min(
            100,
            round(score)
        )
    )

    return score


# =========================
# JWT USER AUTH
# =========================

def get_current_user(

    credentials:
    HTTPAuthorizationCredentials =
    Depends(security)

):

    token = (
        credentials.credentials
    )

    email = (
        verify_token(token)
    )

    if not email:

        raise HTTPException(
            status_code=401,
            detail=
            "Invalid or expired token"
        )

    return email
    # =========================
# HOME API
# =========================

@app.get("/")
def home():

    return {

        "application":
            "PipeGuard AI",

        "version":
            "15.0",

        "status":
            "ONLINE"

    }


# =========================
# HEALTH API
# =========================

@app.get("/health")
def health():

    return {

        "status":
            "healthy",

        "database":
            "connected"

    }


# =========================
# API STATUS
# =========================

@app.get("/api-status")
def api_status():

    return {

        "application":
            "PipeGuard AI",

        "version":
            "15.0",

        "supported_files": [

            "csv",
            "xlsx",
            "xls",
            "json",
            "txt"

        ]

    }


# =========================
# SIGNUP API
# =========================

@app.post("/signup")
def signup(
    user: SignupRequest
):

    conn = get_db()

    cursor = conn.cursor()

    # =====================
    # PASSWORD CHECK
    # =====================

    validate_password(
        user.password
    )

    # =====================
    # TEMP MAIL BLOCK
    # =====================

    domain = (

        user.email

        .split("@")[-1]

        .lower()

    )

    if domain in TEMP_EMAIL_DOMAINS:

        conn.close()

        raise HTTPException(

            status_code=400,

            detail=
            "Temporary email addresses are not allowed"

        )

    # =====================
    # PHONE VALIDATION
    # =====================

    if not PHONE_REGEX.match(
        user.phone
    ):

        conn.close()

        raise HTTPException(

            status_code=400,

            detail=
            "Enter a valid Indian mobile number"

        )

    if user.phone in BLOCKED_PHONES:

        conn.close()

        raise HTTPException(

            status_code=400,

            detail=
            "Invalid phone number"

        )

    # =====================
    # EMAIL EXISTS
    # =====================

    cursor.execute(

        """
        SELECT id
        FROM users
        WHERE email=?
        """,

        (user.email,)

    )

    existing_user = (
        cursor.fetchone()
    )

    if existing_user:

        conn.close()

        raise HTTPException(

            status_code=400,

            detail=
            "Email already registered"

        )

    # =====================
    # HASH PASSWORD
    # =====================

    hashed_password = (
        hash_password(
            user.password
        )
    )

    # =====================
    # INSERT USER
    # =====================

    cursor.execute(

        """
        INSERT INTO users
        (
            full_name,
            company_name,
            phone,
            email,
            password,
            is_verified,
            country_code,
            plan
        )
        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?)
        """,

        (

            user.full_name,

            user.company_name,

            user.phone,

            user.email,

            hashed_password,

            1,

            user.country_code,

            "FREE"

        )

    )

    conn.commit()

    conn.close()

    # =====================
    # AUTO LOGIN TOKEN
    # =====================

    token = (
        create_access_token(
            user.email
        )
    )

    return {

        "message":
            "Account created successfully",

        "access_token":
            token,

        "token_type":
            "Bearer"

    }
    # =========================
# LOGIN API
# =========================

@app.post("/login")
def login(
    data: LoginRequest
):

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

    user = (
        cursor.fetchone()
    )

    conn.close()

    if not user:

        raise HTTPException(

            status_code=401,

            detail=
            "Invalid email"

        )

    if not verify_password(

        data.password,

        user[0]

    ):

        raise HTTPException(

            status_code=401,

            detail=
            "Invalid password"

        )

    token = (
        create_access_token(
            data.email
        )
    )

    return {

        "message":
            "Login successful",

        "access_token":
            token,

        "token_type":
            "Bearer"

    }


# =========================
# MY WORKSPACE
# =========================

@app.get("/my-workspace")
def my_workspace(

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
            country_code,
            plan
        FROM users
        WHERE email=?
        """,

        (email,)

    )

    user = (
        cursor.fetchone()
    )

    conn.close()

    if not user:

        raise HTTPException(

            status_code=404,

            detail=
            "User not found"

        )

    return {

        "email":
            email,

        "full_name":
            user[0],

        "company_name":
            user[1],

        "phone":
            user[2],

        "country_code":
            user[3],

        "plan":
            user[4]

    }


# =========================
# PROFILE API
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
            country_code,
            email,
            plan,
            created_at
        FROM users
        WHERE email=?
        """,

        (email,)

    )

    user = (
        cursor.fetchone()
    )

    conn.close()

    if not user:

        raise HTTPException(

            status_code=404,

            detail=
            "User not found"

        )

    return {

        "full_name":
            user[0],

        "company_name":
            user[1],

        "phone":
            user[2],

        "country_code":
            user[3],

        "email":
            user[4],

        "plan":
            user[5],

        "created_at":
            user[6]

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

        (email,)

    )

    user = (
        cursor.fetchone()
    )

    if not user:

        conn.close()

        raise HTTPException(

            status_code=404,

            detail=
            "User not found"

        )

    if not verify_password(

        data.old_password,

        user[0]

    ):

        conn.close()

        raise HTTPException(

            status_code=400,

            detail=
            "Old password incorrect"

        )

    new_hash = (
        hash_password(
            data.new_password
        )
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

        "message":
            "Password updated successfully"

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

    conn = get_db()

    cursor = conn.cursor()

    updates = []

    values = []

    if data.full_name:

        updates.append(
            "full_name=?"
        )

        values.append(
            data.full_name
        )

    if data.company_name is not None:

        updates.append(
            "company_name=?"
        )

        values.append(
            data.company_name
        )

    if data.phone:

        if not PHONE_REGEX.match(
            data.phone
        ):

            conn.close()

            raise HTTPException(
                status_code=400,
                detail=
                "Invalid phone number"
            )

        if data.phone in BLOCKED_PHONES:

            conn.close()

            raise HTTPException(
                status_code=400,
                detail=
                "Blocked phone number"
            )

        updates.append(
            "phone=?"
        )

        values.append(
            data.phone
        )

    if len(updates) == 0:

        conn.close()

        return {
            "message":
            "No changes provided"
        }

    values.append(email)

    query = f"""
    UPDATE users
    SET {", ".join(updates)}
    WHERE email=?
    """

    cursor.execute(
        query,
        tuple(values)
    )

    conn.commit()

    conn.close()

    return {

        "message":
            "Profile updated successfully"

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

        """
        DELETE FROM users
        WHERE email=?
        """,

        (email,)

    )

    cursor.execute(

        """
        DELETE FROM pipeline_reports
        WHERE company_email=?
        """,

        (email,)

    )

    conn.commit()

    conn.close()

    return {

        "message":
            "Account deleted successfully"

    }


# =========================
# TOKEN VALIDATION
# =========================

@app.get("/validate-token")
def validate_token_route(

    email: str =
    Depends(get_current_user)

):

    return {

        "valid": True,

        "email": email

    }


# =========================
# CURRENT USER
# =========================

@app.get("/current-user")
def current_user(

    email: str =
    Depends(get_current_user)

):

    return {

        "email":
            email

    }


# =========================
# LOGOUT
# =========================

@app.post("/logout")
def logout():

    return {

        "message":
            "Logout successful"

    }
    # =========================
# UPLOAD PIPELINE
# =========================

@app.post("/upload-pipeline")
def upload_pipeline(

    pipeline_name: str,

    file: UploadFile = File(...),

    email: str =
    Depends(get_current_user)

):

    # =====================
    # VALIDATE FILE
    # =====================

    validate_uploaded_file(
        file
    )

    # =====================
    # LOAD FILE
    # =====================

    df, file_type = load_file(
        file
    )

    # =====================
    # EMPTY DATA CHECK
    # =====================

    if len(df) == 0:

        raise HTTPException(

            status_code=400,

            detail=
            "Uploaded file is empty"

        )

    # =====================
    # ANALYSIS
    # =====================

    analysis = (
        analyze_dataframe(
            df
        )
    )

    # =====================
    # HEALTH SCORE
    # =====================

    health_score = (
        calculate_health_score(
            analysis
        )
    )

    # =====================
    # CLEAN DATA
    # =====================

    cleaned_result = (
        clean_dataframe(
            df
        )
    )

    cleaned_df = (
        cleaned_result[
            "dataframe"
        ]
    )

    cleaning_log = (
        cleaned_result[
            "log"
        ]
    )

    # =====================
    # ISSUE LIST
    # =====================

    issues = []

    if analysis[
        "missing_values"
    ] > 0:

        issues.append(

            f"{analysis['missing_values']} missing values"

        )

    if analysis[
        "duplicate_rows"
    ] > 0:

        issues.append(

            f"{analysis['duplicate_rows']} duplicate rows"

        )

    if len(
        analysis[
            "empty_columns"
        ]
    ) > 0:

        issues.append(

            f"{len(analysis['empty_columns'])} empty columns"

        )

    if len(issues) == 0:

        issues.append(
            "No issues detected"
        )

    # =====================
    # SAVE REPORT
    # =====================

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        INSERT INTO pipeline_reports
        (
            company_email,
            pipeline_name,
            file_type,
            health_score,
            issues,
            total_rows,
            total_columns
        )
        VALUES
        (?, ?, ?, ?, ?, ?, ?)
        """,

        (

            email,

            pipeline_name,

            file_type,

            health_score,

            ", ".join(issues),

            analysis[
                "total_rows"
            ],

            analysis[
                "total_columns"
            ]

        )

    )

    conn.commit()

    conn.close()

    # =====================
    # CLEAN FILE EXPORT
    # =====================

    csv_buffer = io.StringIO()

    cleaned_df.to_csv(

        csv_buffer,

        index=False

    )

    cleaned_csv = (
        csv_buffer.getvalue()
    )

    encoded_file = (

        base64.b64encode(

            cleaned_csv.encode(
                "utf-8"
            )

        )

        .decode(
            "utf-8"
        )

    )

    # =====================
    # RESPONSE
    # =====================

    return {

        "message":
            "Pipeline processed successfully",

        "pipeline_name":
            pipeline_name,

        "file_type":
            file_type,

        "health_score":
            health_score,

        "issues":
            issues,

        "analysis":
            analysis,

        "cleaning_log":
            cleaning_log,

        "clean_file":
            encoded_file

    }


# =========================
# SUPPORTED FILES
# =========================

@app.get("/supported-files")
def supported_files():

    return {

        "supported": [

            "csv",

            "xlsx",

            "xls",

            "json",

            "txt"

        ]

    }
    # =========================
# MY REPORTS
# =========================

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
            file_type,
            health_score,
            issues,
            total_rows,
            total_columns,
            created_at
        FROM pipeline_reports
        WHERE company_email=?
        ORDER BY created_at DESC
        """,

        (email,)

    )

    reports = (
        cursor.fetchall()
    )

    conn.close()

    response = []

    for report in reports:

        response.append({

            "id":
                report[0],

            "pipeline_name":
                report[1],

            "file_type":
                report[2],

            "health_score":
                report[3],

            "issues":
                report[4],

            "total_rows":
                report[5],

            "total_columns":
                report[6],

            "created_at":
                report[7]

        })

    return {

        "email":
            email,

        "total_reports":
            len(response),

        "reports":
            response

    }


# =========================
# REPORT DETAILS
# =========================

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
        SELECT
            id,
            company_email,
            pipeline_name,
            file_type,
            health_score,
            issues,
            total_rows,
            total_columns,
            created_at
        FROM pipeline_reports
        WHERE id=?
        """,

        (report_id,)

    )

    report = (
        cursor.fetchone()
    )

    conn.close()

    if not report:

        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    if report[1] != email:

        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    return {

        "id":
            report[0],

        "pipeline_name":
            report[2],

        "file_type":
            report[3],

        "health_score":
            report[4],

        "issues":
            report[5],

        "total_rows":
            report[6],

        "total_columns":
            report[7],

        "created_at":
            report[8]

    }


# =========================
# DELETE REPORT
# =========================

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
        SELECT company_email
        FROM pipeline_reports
        WHERE id=?
        """,

        (report_id,)

    )

    report = (
        cursor.fetchone()
    )

    if not report:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    if report[0] != email:

        conn.close()

        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    cursor.execute(

        """
        DELETE FROM pipeline_reports
        WHERE id=?
        """,

        (report_id,)

    )

    conn.commit()

    conn.close()

    return {

        "message":
            "Report deleted successfully"

    }


# =========================
# DASHBOARD STATS
# =========================

@app.get("/dashboard-stats")
def dashboard_stats(

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

        (email,)

    )

    total_reports = (
        cursor.fetchone()[0]
    )

    cursor.execute(

        """
        SELECT AVG(health_score)
        FROM pipeline_reports
        WHERE company_email=?
        """,

        (email,)

    )

    avg_health = (
        cursor.fetchone()[0]
    )

    if avg_health is None:

        avg_health = 0

    cursor.execute(

        """
        SELECT
            pipeline_name,
            health_score,
            created_at
        FROM pipeline_reports
        WHERE company_email=?
        ORDER BY created_at DESC
        LIMIT 5
        """,

        (email,)

    )

    recent = (
        cursor.fetchall()
    )

    conn.close()

    recent_reports = []

    for item in recent:

        recent_reports.append({

            "pipeline_name":
                item[0],

            "health_score":
                item[1],

            "created_at":
                item[2]

        })

    return {

        "total_reports":
            total_reports,

        "average_health":
            round(avg_health, 2),

        "recent_reports":
            recent_reports

    }
    # =========================
# SYSTEM STATS
# =========================

@app.get("/system-stats")
def system_stats():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    total_users = (
        cursor.fetchone()[0]
    )

    cursor.execute(
        "SELECT COUNT(*) FROM pipeline_reports"
    )

    total_reports = (
        cursor.fetchone()[0]
    )

    cursor.execute(
        """
        SELECT AVG(health_score)
        FROM pipeline_reports
        """
    )

    avg_health = (
        cursor.fetchone()[0]
    )

    conn.close()

    if avg_health is None:

        avg_health = 0

    return {

        "total_users":
            total_users,

        "total_reports":
            total_reports,

        "average_health":
            round(avg_health, 2)

    }


# =========================
# USER COUNT
# =========================

@app.get("/user-count")
def user_count():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    count = (
        cursor.fetchone()[0]
    )

    conn.close()

    return {

        "users":
            count

    }


# =========================
# PIPELINE COUNT
# =========================

@app.get("/pipeline-count")
def pipeline_count():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM pipeline_reports
        """
    )

    count = (
        cursor.fetchone()[0]
    )

    conn.close()

    return {

        "pipelines":
            count

    }


# =========================
# SEARCH REPORTS
# =========================

@app.get("/search-reports")
def search_reports(

    query: str,

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
            file_type,
            health_score,
            created_at
        FROM pipeline_reports
        WHERE company_email=?
        AND pipeline_name
        LIKE ?
        ORDER BY created_at DESC
        """,

        (
            email,
            f"%{query}%"
        )

    )

    reports = (
        cursor.fetchall()
    )

    conn.close()

    result = []

    for report in reports:

        result.append({

            "id":
                report[0],

            "pipeline_name":
                report[1],

            "file_type":
                report[2],

            "health_score":
                report[3],

            "created_at":
                report[4]

        })

    return {

        "results":
            result,

        "count":
            len(result)

    }


# =========================
# ALL USERS (ADMIN)
# =========================

@app.get("/all-users")
def all_users():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT
            id,
            full_name,
            email,
            plan,
            created_at
        FROM users
        ORDER BY created_at DESC
        """

    )

    users = (
        cursor.fetchall()
    )

    conn.close()

    response = []

    for user in users:

        response.append({

            "id":
                user[0],

            "full_name":
                user[1],

            "email":
                user[2],

            "plan":
                user[3],

            "created_at":
                user[4]

        })

    return {

        "total_users":
            len(response),

        "users":
            response

    }
    # =========================
# PING
# =========================

@app.get("/ping")
def ping():

    return {

        "message":
            "pong"

    }


# =========================
# VERSION
# =========================

@app.get("/version")
def version():

    return {

        "application":
            "PipeGuard AI",

        "version":
            "15.0"

    }


# =========================
# READY CHECK
# =========================

@app.get("/ready")
def ready():

    try:

        conn = get_db()

        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1"
        )

        conn.close()

        return {

            "ready":
                True,

            "database":
                "connected"

        }

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=
            f"Database error: {str(e)}"

        )


# =========================
# USER EXISTS
# =========================

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

        (email,)

    )

    user = (
        cursor.fetchone()
    )

    conn.close()

    return {

        "exists":
            bool(user)

    }


# =========================
# REPORT COUNT
# =========================

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

        (email,)

    )

    count = (
        cursor.fetchone()[0]
    )

    conn.close()

    return {

        "count":
            count

    }


# =========================
# ROOT ERROR TEST
# =========================

@app.get("/test")
def test():

    return {

        "status":
            "working",

        "message":
            "PipeGuard backend running"

    }


# =========================
# STARTUP CHECK
# =========================

@app.on_event("startup")
def startup_check():

    try:

        create_tables()

        print(
            "PipeGuard AI Started"
        )

    except Exception as e:

        print(
            f"Startup Error: {e}"
        )


# =========================
# GLOBAL EXCEPTION
# =========================

@app.exception_handler(Exception)
async def global_exception_handler(

    request,

    exc

):

    return {

        "success":
            False,

        "error":
            str(exc)

<<<<<<< HEAD
    }
=======
    }
>>>>>>> 8c6eff2 (fix upload api)
