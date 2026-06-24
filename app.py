import io
import re
import json
import base64
import datetime
from typing import List, Dict, Any, Tuple, Optional

# FastAPI framework runtime web layer components
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

# Pydantic enterprise data validation and structure models
from pydantic import (
    BaseModel,
    EmailStr,
    Field
)

# Heavy-duty computational math and matrix evaluation layers
import pandas as pd
import numpy as np

# Internal pipeline integration bridges (Ensure database.py and auth.py are in local scope)
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

# ==============================================================================
# 1. ENTERPRISE CORE CONFIGURATIONS, BLACKLISTS & STATIC REGEX MATRICES
# ==============================================================================

TEMP_EMAIL_DOMAINS: set = {
    "mailinator.com", "10minutemail.com", "guerrillamail.com", "yopmail.com",
    "tempmail.com", "temp-mail.org", "getnada.com", "trashmail.com",
    "fakeinbox.com", "dispostable.com", "maildrop.cc", "mailnesia.com",
    "sharklasers.com", "grr.la", "guerrillamailblock.com", "anonbox.net",
    "anymailfinder.com", "bouncely.com", "burnemail.com", "creator.ai",
    "throwawaymail.com", "tempmailaddress.com", "getairmail.com", "chimpmail.com"
}

BLOCKED_PHONES: set = {
    "1234567890", "1111111111", "2222222222", "3333333333", "4444444444",
    "5555555555", "6666666666", "7777777777", "8888888888", "9999999999",
    "0000000000", "9876543210", "0123456789", "1234512345", "9999988888"
}

# Pre-compiled static internal regex models targeting data sanitization pipelines
EMAIL_REGEX: re.Pattern = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_REGEX: re.Pattern = re.compile(r"^\d{10}$")
ALPHA_NUMERIC_SPACE: re.Pattern = re.compile(r"^[a-zA-Z0-9\s]*$")
COMPANY_SANITY_CHECK: re.Pattern = re.compile(r"^[a-zA-Z0-9\s\.,&\-\(\)]*$")

# ==============================================================================
# 2. FASTAPI INSTANCE DEFINITIONS & ROBUST MIDDLEWARE ROUTING
# ==============================================================================

app = FastAPI(
    title="PipeGuard AI",
    description="Enterprise-Grade Data Quality Pipeline Management System Backend Engine Architecture.",
    version="12.5",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Explicit layout configurations for cross-origin tracking mechanisms (Vercel Production Alignments)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Synchronize core table metrics on system initialization steps
create_tables()

# Initialize operational security handler layers
security = HTTPBearer()

# ==============================================================================
# 3. ENTITY DATA PROTECTION LAYERS & REUSABLE PYDANTIC INPUT MODEL SCHEMAS
# ==============================================================================

class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Legal identification name parameter")
    company_name: str = Field("", max_length=150, description="Corporate asset tracking entity space")
    country_code: str = Field("+91", min_length=2, max_length=5, description="ISO global network telephone routing system mapping")
    phone: str = Field(..., min_length=10, max_length=15, description="Primary network structural mobile destination index")
    email: EmailStr = Field(..., description="B2B workspace transactional authentication address link")
    password: str = Field(..., min_length=8, description="Cryptographically matched systemic verification passkey array")

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Systemic user access identification criteria")
    password: str = Field(..., description="Secure credential system verification variable")

class APIStatusResponse(BaseModel):
    application: str
    version: str
    database: str
    authentication: str
    supported_files: List[str]
    system_time: str

class WorkspaceResponse(BaseModel):
    email: str
    full_name: str
    company: str
    plan: str
    status: str
    account_created_node: Optional[str] = "2026-Node"

# ==============================================================================
# 4. EXPLICIT SECURE VALIDATION ENGINES & COMPLIANCE PARSER BLOCKS
# ==============================================================================

def validate_password(password: str) -> bool:
    """Performs deep contextual check routines against inbound corporate user key buffers."""
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password structure boundary failure: Must match or exceed 8 characters.")
    if not any(char.isupper() for char in password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insecure passkey layout: Missing upper-case alphabetic structure.")
    if not any(char.islower() for char in password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insecure passkey layout: Missing lower-case alphabetic structure.")
    if not any(char.isdigit() for char in password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insecure passkey layout: Missing numerical digit coordinate variable.")
    return True

def validate_uploaded_file(uploaded_file: UploadFile) -> bool:
    """Intercepts execution threads to assert incoming dataset structure types prior to RAM loading operations."""
    allowed_extensions: List[str] = [".csv", ".xlsx", ".xls", ".json"]
    filename: str = uploaded_file.filename.lower()
    
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Structural validation block: Target format type unmappable. Please use CSV, XLSX, XLS, or JSON structures."
        )
    return True

# ==============================================================================
# 5. ZERO-RETENTION ZERO-DISK VOLATILE MEMORY EXTRACTION PIPELINE
# ==============================================================================

def load_file_safely(uploaded_file: UploadFile) -> Tuple[pd.DataFrame, str]:
    """Sucks bulk binary matrix arrays explicitly into temporary isolated volatile blocks."""
    filename: str = uploaded_file.filename.lower()
    
    try:
        file_bytes: bytes = uploaded_file.file.read()
        if not file_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="System extraction error: Received dataset has an empty 0-byte structural weight.")
            
        uploaded_file.file.seek(0)
        buffer: io.BytesIO = io.BytesIO(file_bytes)
        
        if filename.endswith(".csv"):
            # Native Pandas dynamic string delimiter configuration tracking structure
            df: pd.DataFrame = pd.read_csv(buffer, keep_default_na=True, skipinitialspace=True)
            return df, "csv"
            
        elif filename.endswith(".xlsx"):
            df: pd.DataFrame = pd.read_excel(buffer, engine="openpyxl", keep_default_na=True)
            return df, "xlsx"
            
        elif filename.endswith(".xls"):
            df: pd.DataFrame = pd.read_excel(buffer, engine="xlrd", keep_default_na=True)
            return df, "xls"
            
        elif filename.endswith(".json"):
            df: pd.DataFrame = pd.read_json(buffer)
            return df, "json"
            
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dataset decoding engine missing matching extension map routing nodes.")
            
    except Exception as parse_crash_err:
        if isinstance(parse_crash_err, HTTPException):
            raise parse_crash_err
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Inbound processing breakdown during dynamic frame generation: {str(parse_crash_err)}"
        )

# ==============================================================================
# 6. HIGH-SPEED VECTORIZED MATRIX PROFILING & TELEMETRY CONTROLLERS
# ==============================================================================

def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Generates matrix profiling data structures using fast internal CPU thread vectorized masks."""
    total_rows: int = len(df)
    total_columns: int = len(df.columns)
    
    if total_rows == 0:
        return {
            "total_rows": 0, "total_columns": total_columns, "missing_values": 0,
            "duplicate_rows": 0, "empty_columns": [str(c) for c in df.columns],
            "invalid_emails": 0, "invalid_phones": 0
        }

    # Extract foundational missing structure densities
    missing_values: int = int(df.isnull().sum().sum())
    duplicate_rows: int = int(df.duplicated().sum())
    empty_columns: List[str] = [str(col) for col in df.columns if df[col].isnull().all()]

    # Vectorized target verification operations: Core Client Emails
    invalid_emails: int = 0
    email_cols: List[Any] = [col for col in df.columns if "email" in str(col).lower()]
    
    for col in email_cols:
        # Cast vector blocks to stripped strings instantly across RAM frames
        series: pd.Series = df[col].fillna("").astype(str).str.strip()
        non_empty_mask: pd.Series = series != ""
        target_elements: pd.Series = series[non_empty_mask]
        
        if not target_elements.empty:
            invalid_mask: pd.Series = ~target_elements.str.match(EMAIL_REGEX.pattern)
            invalid_emails += int(invalid_mask.sum())

    # Vectorized target verification operations: Contact Telephone Matrices
    invalid_phones: int = 0
    phone_cols: List[Any] = [col for col in df.columns if "phone" in str(col).lower() or "mobile" in str(col).lower()]
    
    for col in phone_cols:
        series: pd.Series = df[col].fillna("").astype(str).str.replace(".0", "", regex=False).str.replace(" ", "", regex=False)
        non_empty_mask: pd.Series = series != ""
        target_elements: pd.Series = series[non_empty_mask]
        
        if not target_elements.empty:
            invalid_mask: pd.Series = ~target_elements.str.match(PHONE_REGEX.pattern)
            invalid_phones += int(invalid_mask.sum())

    return {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "missing_values": missing_values,
        "duplicate_rows": duplicate_rows,
        "empty_columns": empty_columns,
        "invalid_emails": invalid_emails,
        "invalid_phones": invalid_phones
    }

def calculate_health_score(analysis: Dict[str, Any]) -> int:
    """Calculates systemic structural integrity metrics utilizing weight distribution metrics."""
    score: float = 100.0
    total_elements: int = analysis["total_rows"] * analysis["total_columns"]
    
    if analysis["total_rows"] == 0 or total_elements == 0:
        return 100
        
    # Deducting proportional value densities down to structural safety boundaries
    score -= (analysis["missing_values"] * 0.3)
    score -= (analysis["duplicate_rows"] * 1.0)
    score -= (analysis["invalid_emails"] * 0.5)
    score -= (analysis["invalid_phones"] * 0.5)
    score -= (len(analysis["empty_columns"]) * 2.0)
    
    return max(0, min(100, round(score)))

# ==============================================================================
# 7. AUTOMATED ATOMIC CONTEXT CLEANING & TRANSFORMATION ENGINES
# ==============================================================================

def clean_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Applies complex, safe structural adjustments across datasets without data corruption risk."""
    cleaned_df: pd.DataFrame = df.copy()
    log: List[str] = []

    # Transformation Alpha Step: Extract distinct unique entities
    initial_row_count: int = len(cleaned_df)
    cleaned_df = cleaned_df.drop_duplicates()
    dropped_rows_diff: int = initial_row_count - len(cleaned_df)
    if dropped_rows_diff > 0:
        log.append(f"Data mutation routine: Discarded {dropped_rows_diff} completely duplicated data lines.")

    # Transformation Beta Step: Remove whitespace noise across all structural textual datasets
    string_object_columns: Any = cleaned_df.select_dtypes(include=["object"]).columns
    for col in string_object_columns:
        cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
    log.append("Global operational format adjustment: Cleared white-space structures inside text blocks.")

    # Transformation Gamma Step: Secure coordinate imputation algorithms
    for col in cleaned_df.columns:
        if cleaned_df[col].dtype == "object":
            cleaned_df[col] = cleaned_df[col].fillna("Unknown")
        else:
            if not cleaned_df[col].isnull().all():
                computed_median: Any = cleaned_df[col].median()
                cleaned_df[col] = cleaned_df[col].fillna(computed_median)
            else:
                cleaned_df[col] = cleaned_df[col].fillna(0)
    log.append("Statistical validation routine: Filled missing elements via structured column metrics.")

    # Transformation Delta Step: Delete completely defunct column segments
    dead_columns: List[str] = [
        str(col) for col in cleaned_df.columns 
        if cleaned_df[col].isnull().all() or (cleaned_df[col] == "Unknown").all() or (cleaned_df[col] == 0).all() and len(cleaned_df) > 5
    ]
    if dead_columns:
        cleaned_df = cleaned_df.drop(columns=dead_columns)
        log.append(f"Structural optimization cleanup: Purged entirely defunct columns: {', '.join(dead_columns)}")

    # Transformation Epsilon Step: Standardize field alignment parameters
    email_columns: List[Any] = [col for col in cleaned_df.columns if "email" in str(col).lower()]
    for col in email_columns:
        cleaned_df[col] = cleaned_df[col].astype(str).str.lower().str.strip()
        
    phone_columns: List[Any] = [col for col in cleaned_df.columns if "phone" in str(col).lower() or "mobile" in str(col).lower()]
    for col in phone_columns:
        cleaned_df[col] = cleaned_df[col].astype(str).str.replace(".0", "", regex=False).str.replace(" ", "", regex=False)

    return {
        "dataframe": cleaned_df,
        "log": log
    }

# ==============================================================================
# 8. MIDDLEWARE AUTH DECODE AND IDENTITY BOUNDARY VERIFICATION
# ==============================================================================

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """Intercepts token parameters down the line to isolate matching identity profile scopes."""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Security context block: Authorization credentials missing.")
        
    extracted_email: Optional[str] = verify_token(credentials.credentials)
    if not extracted_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Session context closed: Active JWT access token failed authentication validation tests."
        )
    return extracted_email

# ==============================================================================
# 9. COMPREHENSIVE PRODUCTION PLATFORM INTERACTION ENDPOINT ROUTERS
# ==============================================================================

@app.get("/", tags=["System Infrastructure Management"])
def home() -> Dict[str, Any]:
    """Root application entry destination point verifying operational lifecycle status."""
    return {
        "message": "Welcome to PipeGuard AI Processing Matrix Engine Node Node-1",
        "version": "12.5",
        "status": "ONLINE",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@app.get("/api-status", response_model=APIStatusResponse, tags=["System Infrastructure Management"])
def api_status() -> Dict[str, Any]:
    """Reports continuous diagnostic status updates to frontend dashboards."""
    return {
        "application": "PipeGuard AI Core Engine Pipeline Instance Mesh Node",
        "version": "12.5",
        "database": "CONNECTED",
        "authentication": "JWT-HS256-ACTIVE",
        "supported_files": ["csv", "xlsx", "xls", "json"],
        "system_time": datetime.datetime.utcnow().isoformat()
    }

@app.get("/health", tags=["System Infrastructure Management"])
def health_check() -> Dict[str, Any]:
    """Used by automatic edge balancing clusters to determine computing node conditions."""
    return {
        "status": "healthy",
        "service": "PipeGuard AI engine processing container network",
        "version": "12.5",
        "uptime_state": "NOMINAL"
    }

@app.get("/ping", tags=["System Infrastructure Management"])
def ping() -> Dict[str, str]:
    """Standard structural latency response confirmation check."""
    return {"message": "pong"}

@app.post("/signup", status_code=status.HTTP_201_CREATED, tags=["Platform Identity Management"])
def signup(user: SignupRequest) -> Dict[str, Any]:
    """Intercepts client parameters to construct permanent cryptographically signed platform access files."""
    validate_password(user.password)
    
    extracted_domain: str = user.email.split("@")[-1].lower()
    if extracted_domain in TEMP_EMAIL_DOMAINS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Security Compliance Exception: Temporary or disposable email communication domains are completely blocked on this server."
        )
        
    if not user.phone.isdigit() or not re.match(r"^[6-9]\d{9}$", user.phone) or user.phone in BLOCKED_PHONES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Input validation failure: Invalid Indian mobile contact number layout sequence parameters."
        )

    db_connection = get_db()
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute("SELECT email FROM users WHERE email = ?", (user.email,))
        if db_cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Identity parameters collision: The specified email address already belongs to an established corporate user profile workspace."
            )
            
        hashed_password_signature: str = hash_password(user.password)
        db_cursor.execute(
            """
            INSERT INTO users (full_name, company_name, country_code, phone, email, password, is_verified, plan)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Free Enterprise Tier Evaluation Mode')
            """,
            (user.full_name, user.company_name, user.country_code, user.phone, user.email, hashed_password_signature, 1)
        )
        db_connection.commit()
    except Exception as db_err:
        if isinstance(db_err, HTTPException):
            raise db_err
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database persistent logging routine crashed: {str(db_err)}")
    finally:
        db_connection.close()

    generated_jwt_access_token: str = create_access_token(user.email)
    return {
        "message": "User company entry profile registered successfully.",
        "access_token": generated_jwt_access_token,
        "token_type": "Bearer"
    }

@app.post("/login", status_code=status.HTTP_200_OK, tags=["Platform Identity Management"])
def login(data: LoginRequest) -> Dict[str, Any]:
    """Examines incoming corporate passkey signatures before distributing active session authorization locks."""
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute("SELECT password FROM users WHERE email = ?", (data.email,))
        user_record: Optional[Tuple[str]] = db_cursor.fetchone()
    except Exception as query_err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Data volume access routine failed: {str(query_err)}")
    finally:
        db_connection.close()

    if not user_record or not verify_password(data.password, user_record[0]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Authentication failed: Input secure passcode verification mismatch or unknown email tracking point."
        )

    generated_jwt_access_token: str = create_access_token(data.email)
    return {
        "message": "Identity authorization confirmed. Workspace session mapped.",
        "access_token": generated_jwt_access_token,
        "token_type": "Bearer"
    }

@app.get("/my-workspace", response_model=WorkspaceResponse, tags=["User Operational Workspaces"])
def my_workspace(email: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Pulls current operational workspace configuration targets bound to user session scopes."""
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute("SELECT full_name, company_name, plan FROM users WHERE email = ?", (email,))
        user_record: Optional[Tuple[str, str, str]] = db_cursor.fetchone()
    except Exception as query_err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal database context lookup breakdown: {str(query_err)}")
    finally:
        db_connection.close()

    if not user_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corporate context reference error: Active identity file could not be extracted.")
        
    return {
        "email": email,
        "full_name": user_record[0],
        "company": user_record[1] if user_record[1] else "Independent Operation Node",
        "plan": user_record[2] if user_record[2] else "Standard Operational Evaluation Mode",
        "status": "ACTIVE",
        "account_created_node": "2026-V2-Production"
    }

# ==============================================================================
# 10. REAL-TIME DATA PROCESSING PIPELINE & STREAM TRANSFORM LOGIC
# ==============================================================================

@app.post("/upload-pipeline", status_code=status.HTTP_200_OK, tags=["Data Pipeline Analytical Core"])
def upload_pipeline(
    pipeline_name: str, 
    file: UploadFile = File(...), 
    email: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Runs data ingest streams, runs profiling, cleans datasets, logs reports, and ships a Base64 CSV block."""
    # Action A: Confirm inbound payload structural integrity rules
    validate_uploaded_file(file)
    
    # Action B: Execute zero-retention safe memory data translation routines
    dataframe_matrix, resolved_file_type = load_file_safely(file)

    # Action C: Profile data matrices for quality anomalies using high-speed vectorized operations
    analysis_metrics: Dict[str, Any] = analyze_dataframe(dataframe_matrix)
    computed_health_score: int = calculate_health_score(analysis_metrics)
    
    # Action D: Run operational asset modification pipelines on target frames
    cleaning_pipeline_results: Dict[str, Any] = clean_dataframe(dataframe_matrix)
    transformed_dataframe: pd.DataFrame = cleaning_pipeline_results["dataframe"]
    generated_cleaning_logs: List[str] = cleaning_pipeline_results["log"]

    # Action E: Construct clean, string-parameterized anomaly logs (Guards against Injection vulnerabilities)
    detected_anomalies_summary: List[str] = []
    if analysis_metrics["missing_values"] > 0: 
        detected_anomalies_summary.append(f"{analysis_metrics['missing_values']} missing rows mapped")
    if analysis_metrics["duplicate_rows"] > 0: 
        detected_anomalies_summary.append(f"{analysis_metrics['duplicate_rows']} exact duplicates purged")
    if analysis_metrics["invalid_emails"] > 0: 
        detected_anomalies_summary.append(f"{analysis_metrics['invalid_emails']} bad email shapes found")
    if analysis_metrics["invalid_phones"] > 0: 
        detected_anomalies_summary.append(f"{analysis_metrics['invalid_phones']} bad layout phone lines found")
    
    if not detected_anomalies_summary: 
        detected_anomalies_summary.append("Optimized Corporate Data Profile - Zero Fault Vectors Found")

    sanitized_issue_string: str = ", ".join(detected_anomalies_summary)

    # Action F: Sync structural report telemetry with backend relational systems
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute(
            """
            INSERT INTO pipeline_reports (company_email, pipeline_name, file_type, health_score, issues, total_rows, total_columns)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                email, pipeline_name, resolved_file_type, computed_health_score, 
                sanitized_issue_string, analysis_metrics["total_rows"], analysis_metrics["total_columns"]
            )
        )
        db_connection.commit()
    except Exception as insert_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Database state sync error: Failed to log pipeline telemetry variables: {str(insert_err)}"
        )
    finally:
        db_connection.close()

    # Action G: Convert cleaned matrix straight into Base64 CSV text sequences for direct client download triggers
    string_io_buffer: io.StringIO = io.StringIO()
    transformed_dataframe.to_csv(string_io_buffer, index=False)
    csv_payload_string: str = string_io_buffer.getvalue()
    base64_encoded_clean_file: str = base64.b64encode(csv_payload_string.encode("utf-8")).decode("utf-8")

    return {
        "message": "B2B data pipeline ingestion and cleansing completed successfully.",
        "pipeline_name": pipeline_name,
        "file_type": resolved_file_type,
        "health_score": computed_health_score,
        "issues": detected_anomalies_summary,
        "analysis": analysis_metrics,
        "cleaning_log": generated_cleaning_logs,
        "clean_file_data": base64_encoded_clean_file,
        "rows": analysis_metrics["total_rows"],
        "columns": analysis_metrics["total_columns"]
    }

@app.get("/my-reports", tags=["Data Pipeline Analytical Core"])
def my_reports(email: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Extracts aggregate evaluation histories belonging to requesting user workspace partitions."""
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute(
            """
            SELECT pipeline_name, file_type, health_score, issues, total_rows, total_columns, created_at
            FROM pipeline_reports WHERE company_email = ? ORDER BY created_at DESC
            """, (email,)
        )
        fetched_report_records: List[Tuple[Any, ...]] = db_cursor.fetchall()
    except Exception as select_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Persistent history volume access execution error: {str(select_err)}"
        )
    finally:
        db_connection.close()

    return {
        "email": email,
        "total_reports": len(fetched_report_records),
        "reports": [{
            "pipeline_name": record[0],
            "file_type": record[1],
            "health_score": record[2],
            "issues": record[3].split(", ") if record[3] else [],
            "total_rows": record[4],
            "total_columns": record[5],
            "created_at": record[6]
        } for record in fetched_report_records]
    }

@app.get("/dashboard-stats", tags=["Data Pipeline Analytical Core"])
def dashboard_stats(email: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Compiles operational analytical trends across historical logs for corporate platform data visuals."""
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute("SELECT COUNT(*) FROM pipeline_reports WHERE company_email = ?", (email,))
        total_reports_count: int = db_cursor.fetchone()[0]

        db_cursor.execute("SELECT AVG(health_score) FROM pipeline_reports WHERE company_email = ?", (email,))
        average_health_score_record: Optional[Tuple[Optional[float]]] = db_cursor.fetchone()
        computed_average_health: float = average_health_score_record[0] if (average_health_score_record and average_health_score_record[0] is not None) else 0.0

        db_cursor.execute(
            """
            SELECT pipeline_name, health_score, created_at
            FROM pipeline_reports WHERE company_email = ? ORDER BY created_at DESC LIMIT 5
            """, (email,)
        )
        recent_scans_records: List[Tuple[str, int, Any]] = db_cursor.fetchall()
    except Exception as metrics_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"UI Telemetry processing pipeline failure: {str(metrics_err)}"
        )
    finally:
        db_connection.close()

    return {
        "total_reports": total_reports_count,
        "average_health": round(computed_average_health, 2),
        "recent_reports": [
            {
                "pipeline": scan[0], 
                "health_score": scan[1], 
                "created_at": scan[2]
            } for scan in recent_scans_records
        ]
    }
