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

from pydantic import BaseModel

import pandas as pd

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
# TEMP EMAIL BLOCK LIST
# =========================

TEMP_EMAIL_DOMAINS = {

    "mailinator.com",
    "10minutemail.com",
    "tempmail.com",
    "temp-mail.org",
    "guerrillamail.com",
    "yopmail.com",
    "trashmail.com",
    "fakeinbox.com",
    "getnada.com",
    "dispostable.com"

}

# =========================
# APP INIT
# =========================

app = FastAPI(

    title="PipeGuard AI",

    description=
    "AI Powered Data Reliability Platform",

    version="11.0"

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
# DATABASE
# =========================

create_tables()

security = HTTPBearer()

# =========================
# MODELS
# =========================

class SignupRequest(BaseModel):

    full_name: str

    company_name: str = ""

    phone: str

    email: str

    password: str


class LoginRequest(BaseModel):

    email: str

    password: str
    # =========================
# SIGNUP API
# =========================

@app.post("/signup")
def signup(user: SignupRequest):

    conn = get_db()
    cursor = conn.cursor()

    # Temp Email Block

    domain = user.email.split("@")[-1].lower()

    if domain in TEMP_EMAIL_DOMAINS:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail="Temporary email addresses are not allowed"
        )

    # Existing User Check

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

    # Password Hash

    hashed_password = hash_password(
        user.password
    )

    # Insert User

    cursor.execute(
        """
        INSERT INTO users
        (
            full_name,
            company_name,
            phone,
            email,
            password,
            is_verified
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user.full_name,
            user.company_name,
            user.phone,
            user.email,
            hashed_password,
            1
        )
    )

    conn.commit()
    conn.close()

    # Auto Login Token

    token = create_access_token(
        user.email
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

    token = credentials.credentials

    email = verify_token(
        token
    )

    if not email:

        raise HTTPException(
            status_code=401,
            detail="Invalid Token"
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

    return {

        "message":
            "Welcome to PipeGuard Workspace",

        "company":
            email,

        "access":
            "GRANTED",

        "features": [

            "Pipeline Monitoring",

            "Data Quality Scans",

            "Issue Detection",

            "Row Level Analysis",

            "Health Reports",

            "Auto Fix Engine"

        ]

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
    # READ CSV
    # =====================

    df = pd.read_csv(
        file.file
    )

    # =====================
    # MISSING VALUES
    # =====================

    missing_values = int(
        df.isnull()
        .sum()
        .sum()
    )

    missing_details = []

    for col in df.columns:

        rows = df[
            df[col].isnull()
        ].index.tolist()

        for row in rows[:20]:

            missing_details.append(

                f"Row {row + 2}: "
                f"{col} is empty"

            )

    # =====================
    # DUPLICATE ROWS
    # =====================

    duplicate_rows = int(
        df.duplicated().sum()
    )

    duplicate_details = []

    duplicate_indexes = df[
        df.duplicated()
    ].index.tolist()

    for row in duplicate_indexes[:20]:

        duplicate_details.append(

            f"Row {row + 2}: "
            f"Duplicate row detected"

        )
            # =====================
    # INVALID EMAILS
    # =====================

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

        for row in invalid_rows[:20]:

            email_details.append(
                f"Row {row + 2}: Invalid email format"
            )

    # =====================
    # INVALID PHONES
    # =====================

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

        for row in invalid_phone_rows[:20]:

            phone_details.append(
                f"Row {row + 2}: Invalid phone number"
            )

    # =====================
    # NEGATIVE REVENUE
    # =====================

    negative_revenue = 0

    revenue_details = []

    if "Order_Value" in df.columns:

        revenue_series = pd.to_numeric(
            df["Order_Value"],
            errors="coerce"
        )

        negative_mask = (
            revenue_series.fillna(0) < 0
        )

        negative_revenue = int(
            negative_mask.sum()
        )

        negative_rows = df[
            negative_mask
        ].index.tolist()

        for row in negative_rows[:20]:

            revenue_details.append(
                f"Row {row + 2}: Negative revenue detected"
            )

    # =====================
    # HEALTH SCORE
    # =====================

    score = 100

    score -= missing_values * 0.3

    score -= duplicate_rows * 1

    score -= invalid_emails * 0.5

    score -= invalid_phones * 0.5

    score -= negative_revenue * 1

    score = max(
        0,
        round(score)
    )

    # =====================
    # ISSUES LIST
    # =====================

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
            # =====================
    # DETAILS OBJECT
    # =====================

    details = {

        "missing":
            missing_details,

        "duplicates":
            duplicate_details,

        "invalid_emails":
            email_details,

        "invalid_phones":
            phone_details,

        "negative_revenue":
            revenue_details

    }

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

    # =====================
    # FINAL RESPONSE
    # =====================

    return {

        "message":
            "Pipeline Scan Completed Successfully",

        "pipeline":
            pipeline_name,

        "health_score":
            score,

        "issues":
            issues,

        "metrics": {

            "missing_values":
                missing_values,

            "duplicate_rows":
                duplicate_rows,

            "invalid_emails":
                invalid_emails,

            "invalid_phones":
                invalid_phones,

            "negative_revenue":
                negative_revenue

        },

        "details":
            details

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

        report_list.append({

            "pipeline":
                report[0],

            "health_score":
                report[1],

            "issues":
                report[2],

            "created_at":
                report[3]

        })

    return {

        "company":
            email,

        "total_reports":
            len(report_list),

        "reports":
            report_list

    }


# =========================
# END OF FILE
# =========================
