from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    UploadFile,
    File
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from fastapi.middleware.cors import (
    CORSMiddleware
)

from pydantic import (
    BaseModel,
    EmailStr
)

import pandas as pd
import json
import re
import os

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
# TEMP EMAIL DOMAINS
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
    "guerrillamailblock.com"

}

# =========================
# BLOCKED PHONES
# =========================

BLOCKED_PHONES = {

    "1234567890",
    "1111111111",
    "9999999999",
    "0000000000",
    "9876543210"

}

# =========================
# APP INIT
# =========================

app = FastAPI(

    title="PipeGuard AI",

    description=
    "AI Data Quality Platform",

    version="12.0"

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
# DATABASE INIT
# =========================

create_tables()

security = HTTPBearer()

# =========================
# MODELS
# =========================

class SignupRequest(BaseModel):

    full_name: str

    company_name: str = ""

    country_code: str = "+91"

    phone: str

    email: EmailStr

    password: str


class LoginRequest(BaseModel):

    email: EmailStr

    password: str
    # =========================
# HOME ROUTE
# =========================

@app.get("/")
def home():

    return {

        "message":
            "Welcome to PipeGuard AI",

        "version":
            "12.0",

        "status":
            "ONLINE"

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
            "12.0",

        "database":
            "CONNECTED",

        "authentication":
            "ACTIVE",

        "supported_files": [

            "csv",
            "xlsx",
            "xls",
            "json"

        ]

    }


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
        r"[0-9]",
        password
    ):

        raise HTTPException(
            status_code=400,
            detail=
            "Password must contain a number"
        )

    return True


# =========================
# FILE LOADER
# =========================

def load_file(
    uploaded_file
):

    filename = (
        uploaded_file.filename
        .lower()
    )

    try:

        if filename.endswith(".csv"):

            return pd.read_csv(
                uploaded_file.file
            )

        elif (
            filename.endswith(".xlsx")
            or
            filename.endswith(".xls")
        ):

            return pd.read_excel(
                uploaded_file.file
            )

        elif filename.endswith(".json"):

            data = json.load(
                uploaded_file.file
            )

            return pd.DataFrame(
                data
            )

        else:

            raise HTTPException(
                status_code=400,
                detail=
                "Unsupported file format"
            )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail=
            "Failed to read file"
        )
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
    # PASSWORD VALIDATION
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

    if not user.phone.isdigit():

        conn.close()

        raise HTTPException(
            status_code=400,
            detail=
            "Phone number must contain only digits"
        )

    if len(user.phone) != 10:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail=
            "Phone number must be exactly 10 digits"
        )

    if user.phone in BLOCKED_PHONES:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail=
            "Invalid phone number"
        )

    # =====================
    # USER EXISTS CHECK
    # =====================

    cursor.execute(
        """
        SELECT email
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
    # PASSWORD HASH
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
            country_code,
            phone,
            email,
            password,
            is_verified
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user.full_name,
            user.company_name,
            user.country_code,
            user.phone,
            user.email,
            hashed_password,
            1
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
            "Invalid email address"
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
# JWT AUTH
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
# WORKSPACE API
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

        "company":
            user[1],

        "plan":
            user[2],

        "status":
            "ACTIVE"

    }
    # =========================
# FILE LOADER
# =========================

def load_file(
    uploaded_file
):

    filename = (
        uploaded_file.filename
        .lower()
    )

    try:

        # =====================
        # CSV
        # =====================

        if filename.endswith(".csv"):

            df = pd.read_csv(
                uploaded_file.file
            )

            return df, "csv"

        # =====================
        # XLSX
        # =====================

        elif filename.endswith(".xlsx"):

            df = pd.read_excel(
                uploaded_file.file,
                engine="openpyxl"
            )

            return df, "xlsx"

        # =====================
        # XLS
        # =====================

        elif filename.endswith(".xls"):

            df = pd.read_excel(
                uploaded_file.file,
                engine="xlrd"
            )

            return df, "xls"

        # =====================
        # JSON
        # =====================

        elif filename.endswith(".json"):

            data = json.load(
                uploaded_file.file
            )

            df = pd.DataFrame(
                data
            )

            return df, "json"

        else:

            raise HTTPException(
                status_code=400,
                detail=
                "Supported formats: CSV, XLSX, XLS, JSON"
            )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=
            f"File processing failed: {str(e)}"
        )


# =========================
# FILE VALIDATION
# =========================

def validate_uploaded_file(
    uploaded_file
):

    allowed_extensions = [

        ".csv",
        ".xlsx",
        ".xls",
        ".json"

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
            "Unsupported file format"
        )

    return True
    # =========================
# DATA QUALITY ENGINE
# =========================

def analyze_dataframe(df):

    results = {}

    # =====================
    # TOTAL ROWS / COLS
    # =====================

    total_rows = len(df)

    total_columns = len(df.columns)

    results["total_rows"] = total_rows

    results["total_columns"] = total_columns

    # =====================
    # MISSING VALUES
    # =====================

    missing_values = int(
        df.isnull()
        .sum()
        .sum()
    )

    results["missing_values"] = (
        missing_values
    )

    # =====================
    # DUPLICATE ROWS
    # =====================

    duplicate_rows = int(
        df.duplicated()
        .sum()
    )

    results["duplicate_rows"] = (
        duplicate_rows
    )

    # =====================
    # EMPTY COLUMNS
    # =====================

    empty_columns = []

    for column in df.columns:

        if (
            df[column]
            .isnull()
            .all()
        ):

            empty_columns.append(
                column
            )

    results["empty_columns"] = (
        empty_columns
    )

    # =====================
    # INVALID EMAILS
    # =====================

    invalid_emails = 0

    email_columns = [

        col for col in df.columns

        if "email" in col.lower()

    ]

    for col in email_columns:

        email_series = (
            df[col]
            .fillna("")
            .astype(str)
        )

        invalid_mask = (
            ~email_series.str.match(
                r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
            )
        )

        invalid_emails += int(
            invalid_mask.sum()
        )

    results["invalid_emails"] = (
        invalid_emails
    )

    # =====================
    # INVALID PHONES
    # =====================

    invalid_phones = 0

    phone_columns = [

        col for col in df.columns

        if (
            "phone" in col.lower()
            or
            "mobile" in col.lower()
        )

    ]

    for col in phone_columns:

        phone_series = (
            df[col]
            .fillna("")
            .astype(str)
            .str.replace(
                ".0",
                "",
                regex=False
            )
        )

        invalid_mask = (
            ~phone_series.str.match(
                r"^\d{10}$"
            )
        )

        invalid_phones += int(
            invalid_mask.sum()
        )

    results["invalid_phones"] = (
        invalid_phones
    )

    return results


# =========================
# HEALTH SCORE ENGINE
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
        analysis["invalid_emails"]
        * 0.5
    )

    score -= (
        analysis["invalid_phones"]
        * 0.5
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
        round(score)
    )

    return score
    # =========================
# AUTO DATA CLEANING ENGINE
# =========================

def clean_dataframe(df):

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
    # REMOVE EXTRA SPACES
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
    # FILL MISSING VALUES
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

            cleaned_df[col] = (

                cleaned_df[col]

                .fillna(
                    cleaned_df[col]
                    .median()
                )

            )

    cleaning_log.append(

        "Missing values handled"

    )

    # =====================
    # REMOVE EMPTY COLUMNS
    # =====================

    empty_columns = []

    for col in cleaned_df.columns:

        if (
            cleaned_df[col]
            .isnull()
            .all()
        ):

            empty_columns.append(
                col
            )

    if len(empty_columns) > 0:

        cleaned_df = (
            cleaned_df.drop(
                columns=
                empty_columns
            )
        )

        cleaning_log.append(

            f"{len(empty_columns)} empty columns removed"

        )

    # =====================
    # STANDARDIZE EMAILS
    # =====================

    email_columns = [

        col for col
        in cleaned_df.columns

        if "email"
        in col.lower()

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

        col for col
        in cleaned_df.columns

        if (
            "phone"
            in col.lower()

            or

            "mobile"
            in col.lower()
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
# UPLOAD PIPELINE API
# =========================

@app.post("/upload-pipeline")
def upload_pipeline(

    pipeline_name: str,

    file: UploadFile = File(...),

    email: str = Depends(
        get_current_user
    )

):

    # =====================
    # FILE VALIDATION
    # =====================

    validate_uploaded_file(
        file
    )

    # =====================
    # LOAD FILE
    # =====================

    df, file_type = (
        load_file(file)
    )

    # =====================
    # DATA ANALYSIS
    # =====================

    analysis = (
        analyze_dataframe(df)
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
        clean_dataframe(df)
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
    # ISSUES
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

    if analysis[
        "invalid_emails"
    ] > 0:

        issues.append(
            f"{analysis['invalid_emails']} invalid emails"
        )

    if analysis[
        "invalid_phones"
    ] > 0:

        issues.append(
            f"{analysis['invalid_phones']} invalid phones"
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
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            email,
            pipeline_name,
            file_type,
            health_score,
            ", ".join(issues),
            analysis["total_rows"],
            analysis["total_columns"]
        )
    )

    conn.commit()

    conn.close()

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

        "rows":
            analysis[
                "total_rows"
            ],

        "columns":
            analysis[
                "total_columns"
            ]

    }
    # =========================
# REPORTS API
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

    reports = cursor.fetchall()

    conn.close()

    report_list = []

    for report in reports:

        report_list.append({

            "pipeline_name":
                report[0],

            "file_type":
                report[1],

            "health_score":
                report[2],

            "issues":
                report[3],

            "total_rows":
                report[4],

            "total_columns":
                report[5],

            "created_at":
                report[6]

        })

    return {

        "email":
            email,

        "total_reports":
            len(report_list),

        "reports":
            report_list

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
        SELECT
            COUNT(*)
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
        SELECT
            AVG(health_score)
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

    recent_scans = (
        cursor.fetchall()
    )

    conn.close()

    recent_reports = []

    for row in recent_scans:

        recent_reports.append({

            "pipeline":
                row[0],

            "health_score":
                row[1],

            "created_at":
                row[2]

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
# HEALTH CHECK
# =========================

@app.get("/health")
def health_check():

    return {

        "status":
            "healthy",

        "service":
            "PipeGuard AI",

        "version":
            "12.0"

    }


# =========================
# SYSTEM INFO
# =========================

@app.get("/system-info")
def system_info():

    return {

        "application":
            "PipeGuard AI",

        "supported_files": [

            "csv",
            "xlsx",
            "xls",
            "json"

        ],

        "features": [

            "Data Cleaning",

            "Duplicate Detection",

            "Missing Value Detection",

            "Invalid Email Detection",

            "Invalid Phone Detection",

            "Dashboard Analytics"

        ]

    }


# =========================
# GLOBAL ERROR RESPONSE
# =========================

@app.get("/ping")
def ping():

    return {

        "message":
            "pong"

    }
