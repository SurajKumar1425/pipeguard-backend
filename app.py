import os
import json
import time
import logging
from datetime import datetime

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

APP_VERSION = "17.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("PipeGuard")

app = FastAPI(
    title="PipeGuard AI",
    description="AI Data Quality Platform",
    version=APP_VERSION
)

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

limiter = Limiter(
    key_func=get_remote_address
)

app.state.limiter = limiter

security = HTTPBearer()

ACTIVE_USERS = {}

MONITOR = {
    "total_requests": 0,
    "successful_uploads": 0,
    "failed_uploads": 0,
    "total_errors": 0
}

create_tables()


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
            "message": "Too many requests"
        }
    )


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


def create_user_session(
    email: str
):
    ACTIVE_USERS[email] = str(
        datetime.utcnow()
    )


def destroy_user_session(
    email: str
):
    ACTIVE_USERS.pop(
        email,
        None
    )


def get_current_user(
    credentials:
    HTTPAuthorizationCredentials
    = Depends(security)
):
    token = credentials.credentials

    email = verify_token(
        token
    )

    if not email:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    return email


def require_admin(
    email: str =
    Depends(get_current_user)
):
    ADMIN_EMAILS = [
        "admin@pipeguard.ai"
    ]

    if email not in ADMIN_EMAILS:

        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return email


@app.on_event("startup")
async def startup():

    create_tables()

    logger.info(
        "PipeGuard Started"
    )
    from typing import Optional
from email_validator import (
    validate_email,
    EmailNotValidError
)

# ---------- MODELS ----------

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


# ---------- VALIDATION ----------

def validate_password_strength(
    password: str
):

    if len(password) < 8:

        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters"
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
            detail="Password must contain upper, lower and number"
        )


def validate_phone_number(
    phone: str
):

    digits = "".join(
        c for c in phone
        if c.isdigit()
    )

    if len(digits) < 10:

        raise HTTPException(
            status_code=400,
            detail="Invalid phone number"
        )


# ---------- SIGNUP ----------

@app.post("/signup")
@limiter.limit("5/minute")
def signup(

    request: Request,

    user: SignupRequest

):

    try:

        validate_email(
            user.email
        )

    except EmailNotValidError:

        raise HTTPException(
            status_code=400,
            detail="Invalid email"
        )

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

    existing = cursor.fetchone()

    if existing:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    encrypted_password = (
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
            encrypted_password,
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
        "message": "Signup successful",
        "token": token
    }


# ---------- LOGIN ----------

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
            detail="Invalid email"
        )

    stored_password = (
        result[0]
    )

    if not verify_password(
        user.password,
        stored_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid password"
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
        "email": user.email
    }


# ---------- CURRENT USER ----------

@app.get("/current-user")
def current_user(

    email: str =
    Depends(get_current_user)

):

    return {
        "success": True,
        "email": email
    }


# ---------- LOGOUT ----------

@app.post("/logout")
def logout(

    email: str =
    Depends(get_current_user)

):

    destroy_user_session(
        email
    )

    return {
        "success": True,
        "message": "Logged out"
    }


# ---------- TOKEN VALIDATION ----------

@app.get("/validate-token")
def validate_token_route(

    email: str =
    Depends(get_current_user)

):

    return {
        "valid": True,
        "email": email
    }
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

        "full_name": user[0],
        "company_name": user[1],
        "phone": user[2],
        "email": user[3],
        "plan": user[4],
        "created_at": user[5]

    }


@app.put("/update-profile")
def update_profile(

    data: UpdateProfileRequest,

    email: str =
    Depends(get_current_user)

):

    conn = get_db()
    cursor = conn.cursor()

    if data.phone:

        validate_phone_number(
            data.phone
        )

    cursor.execute(
        """
        UPDATE users

        SET

        full_name =
        COALESCE(
            ?, full_name
        ),

        company_name =
        COALESCE(
            ?, company_name
        ),

        phone =
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

    return {

        "success": True,
        "message": "Profile updated"

    }


@app.post("/change-password")
def change_password(

    data:
    ChangePasswordRequest,

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

    stored_password = result[0]

    if not verify_password(
        data.old_password,
        stored_password
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
        "message": "Password changed"

    }


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

    return {

        "success": True,
        "message": "Account deleted"

    }


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

        "email": email,

        "total_reports":
        total_reports,

        "average_health_score":
        round(
            avg_score or 0,
            2
        ),

        "active_session":
        True

    }


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

        "exists": exists

    }
    ALLOWED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls",
    ".json",
    ".txt"
}

MAX_FILE_SIZE_MB = 20


def validate_file(
    file: UploadFile
):

    filename = (
        file.filename.lower()
    )

    extension = (
        os.path.splitext(
            filename
        )[1]
    )

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail="Unsupported file format"
        )

    return extension


def load_file(
    file: UploadFile,
    extension: str
):

    try:

        if extension == ".csv":

            return pd.read_csv(
                file.file
            )

        elif extension in [
            ".xlsx",
            ".xls"
        ]:

            return pd.read_excel(
                file.file
            )

        elif extension == ".json":

            return pd.read_json(
                file.file
            )

        elif extension == ".txt":

            return pd.read_csv(
                file.file,
                sep=None,
                engine="python"
            )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Unable to read file: {str(e)}"
        )


def calculate_health_score(
    df: pd.DataFrame
):

    rows = len(df)

    if rows == 0:
        return 0

    missing_values = int(
        df.isnull()
        .sum()
        .sum()
    )

    duplicate_rows = int(
        df.duplicated()
        .sum()
    )

    total_cells = (
        rows *
        len(df.columns)
    )

    missing_percent = (
        missing_values /
        max(total_cells, 1)
    ) * 100

    duplicate_percent = (
        duplicate_rows /
        max(rows, 1)
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

    for column in df.columns:

        null_pct = (
            df[column]
            .isnull()
            .mean()
        ) * 100

        if null_pct > 50:

            issues.append(
                f"{column} has >50% null values"
            )

    return issues


def auto_clean_dataframe(
    df: pd.DataFrame
):

    report = {}

    report[
        "rows_before"
    ] = len(df)

    report[
        "duplicates_removed"
    ] = int(
        df.duplicated()
        .sum()
    )

    df = df.drop_duplicates()

    for col in df.columns:

        try:

            if (
                df[col].dtype
                == "object"
            ):

                df[col] = (
                    df[col]
                    .astype(str)
                    .str.strip()
                )

        except:
            pass

    report[
        "rows_after"
    ] = len(df)

    return (
        df,
        report
    )


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

        extension = validate_file(
            file
        )

        df = load_file(
            file,
            extension
        )

        original_rows = len(df)

        cleaned_df, clean_report = (
            auto_clean_dataframe(
                df
            )
        )

        health_score = (
            calculate_health_score(
                cleaned_df
            )
        )

        issues = detect_issues(
            cleaned_df
        )

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO pipeline_reports (

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
                extension,
                health_score,
                json.dumps(
                    issues
                ),
                len(cleaned_df),
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

        return {

            "success": True,

            "pipeline_name":
            pipeline_name,

            "health_score":
            health_score,

            "issues":
            issues,

            "rows":
            len(cleaned_df),

            "columns":
            len(
                cleaned_df.columns
            ),

            "clean_report":
            clean_report,

            "original_rows":
            original_rows

        }

    except HTTPException:
        raise

    except Exception as e:

        MONITOR[
            "failed_uploads"
        ] += 1

        logger.error(
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Upload failed"
        )


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

    for report in reports:

        data.append({

            "id":
            report[0],

            "pipeline_name":
            report[1],

            "file_type":
            report[2],

            "health_score":
            report[3],

            "rows":
            report[4],

            "columns":
            report[5],

            "created_at":
            report[6]

        })

    return {

        "success": True,

        "count":
        len(data),

        "reports":
        data

    }


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
            detail="Report not found"
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
        json.loads(
            report[5]
        )
        if report[5]
        else [],

        "total_rows":
        report[6],

        "total_columns":
        report[7],

        "created_at":
        report[8]

    }


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
        DELETE FROM pipeline_reports

        WHERE id=?
        AND company_email=?
        """,
        (
            report_id,
            email
        )
    )

    conn.commit()

    deleted = cursor.rowcount

    conn.close()

    if deleted == 0:

        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    return {

        "success": True,

        "message":
        "Report deleted"

    }


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

        WHERE company_email=?
        AND pipeline_name LIKE ?
        """,
        (
            email,
            f"%{keyword}%"
        )
    )

    results = cursor.fetchall()

    conn.close()

    return {

        "success": True,

        "count":
        len(results),

        "results":
        results

    }


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

    total = cursor.fetchone()[0]

    conn.close()

    return {

        "pipelines":
        total

    }


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
        ],

        "active_users":
        len(
            ACTIVE_USERS
        )

    }


@app.get("/user-count")
def user_count(

    email: str =
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

    count = cursor.fetchone()[0]

    conn.close()

    return {

        "total_users":
        count

    }


@app.get("/all-users")
def all_users(

    email: str =
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
            plan,
            created_at

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
@app.get("/")
def home():

    return {

        "application":
        "PipeGuard AI",

        "version":
        APP_VERSION,

        "status":
        "running"

    }


@app.get("/health")
def health():

    try:

        conn = get_db()

        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1"
        )

        conn.close()

        db_status = "connected"

    except:

        db_status = "disconnected"

    return {

        "status":
        "healthy",

        "database":
        db_status,

        "timestamp":
        str(
            datetime.utcnow()
        )

    }


@app.get("/api-status")
def api_status():

    return {

        "running":
        True,

        "version":
        APP_VERSION,

        "requests":
        MONITOR[
            "total_requests"
        ],

        "errors":
        MONITOR[
            "total_errors"
        ]

    }


@app.get("/version")
def version():

    return {

        "application":
        "PipeGuard AI",

        "version":
        APP_VERSION

    }


@app.get("/ping")
def ping():

    return {

        "message":
        "pong"

    }


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
            True

        }

    except:

        return {

            "ready":
            False,

            "database":
            False

        }


@app.get("/system-stats")
def system_stats(

    email: str =
    Depends(require_admin)

):

    return {

        "cpu_percent":
        psutil.cpu_percent(),

        "memory_percent":
        psutil.virtual_memory().percent,

        "disk_percent":
        psutil.disk_usage(
            "/"
        ).percent,

        "active_users":
        len(
            ACTIVE_USERS
        ),

        "successful_uploads":
        MONITOR[
            "successful_uploads"
        ],

        "failed_uploads":
        MONITOR[
            "failed_uploads"
        ],

        "total_requests":
        MONITOR[
            "total_requests"
        ],

        "total_errors":
        MONITOR[
            "total_errors"
        ]

    }


@app.get("/self-monitor")
def self_monitor(

    email: str =
    Depends(require_admin)

):

    cpu = psutil.cpu_percent()

    ram = (
        psutil.virtual_memory()
        .percent
    )

    disk = (
        psutil.disk_usage("/")
        .percent
    )

    status = "healthy"

    if cpu > 90:

        status = "warning"

    if ram > 90:

        status = "warning"

    if disk > 90:

        status = "critical"

    return {

        "status":
        status,

        "cpu":
        cpu,

        "ram":
        ram,

        "disk":
        disk,

        "active_users":
        len(
            ACTIVE_USERS
        )

    }


@app.get("/test")
def test():

    return {

        "success":
        True,

        "message":
        "PipeGuard API Working"

    }
