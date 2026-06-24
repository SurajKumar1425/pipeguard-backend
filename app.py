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

EMAIL_REGEX: re.Pattern = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_REGEX: re.Pattern = re.compile(r"^\d{10}$")
ALPHA_NUMERIC_SPACE: re.Pattern = re.compile(r"^[a-zA-Z0-9\s]*$")

# ==============================================================================
# 2. FASTAPI INSTANCE DEFINITIONS & ROBUST MIDDLEWARE ROUTING
# ==============================================================================

app = FastAPI(
    title="PipeGuard AI",
    description="Enterprise-Grade Data Quality Pipeline Management System Backend Engine Architecture.",
    version="14.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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

# ==============================================================================
# 3. ENTITY DATA PROTECTION LAYERS & PYDANTIC MODELS
# ==============================================================================

class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    company_name: str = Field("", max_length=150)
    country_code: str = Field("+91", min_length=2, max_length=5)
    phone: str = Field(..., min_length=10, max_length=15)
    email: EmailStr = Field(..., description="B2B workspace transactional authentication address link")
    password: str = Field(..., min_length=8)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    company_name: Optional[str] = Field(None, max_length=150)
    phone: Optional[str] = Field(None, min_length=10, max_length=15)

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

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
# 4. EXPLICIT SECURE VALIDATION ENGINES
# ==============================================================================

def validate_password(password: str) -> bool:
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")
    if not any(char.isupper() for char in password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter.")
    if not any(char.islower() for char in password):
        raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter.")
    if not any(char.isdigit() for char in password):
        raise HTTPException(status_code=400, detail="Password must contain at least one number.")
    return True

def validate_uploaded_file(uploaded_file: UploadFile) -> bool:
    allowed_extensions: List[str] = [".csv", ".xlsx", ".xls", ".json"]
    filename: str = uploaded_file.filename.lower()
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV, XLSX, XLS, or JSON.")
    return True

# ==============================================================================
# 5. IN-MEMORY PARSER (ZERO-DISK RETENTION)
# ==============================================================================

def load_file_safely(uploaded_file: UploadFile) -> Tuple[pd.DataFrame, str]:
    filename: str = uploaded_file.filename.lower()
    try:
        file_bytes: bytes = uploaded_file.file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        uploaded_file.file.seek(0)
        buffer: io.BytesIO = io.BytesIO(file_bytes)
        
        if filename.endswith(".csv"):
            return pd.read_csv(buffer, keep_default_na=True, skipinitialspace=True), "csv"
        elif filename.endswith(".xlsx"):
            return pd.read_excel(buffer, engine="openpyxl", keep_default_na=True), "xlsx"
        elif filename.endswith(".xls"):
            return pd.read_excel(buffer, engine="xlrd", keep_default_na=True), "xls"
        elif filename.endswith(".json"):
            return pd.read_json(buffer), "json"
        else:
            raise HTTPException(status_code=400, detail="Unsupported file extension map routing.")
    except Exception as parse_crash_err:
        if isinstance(parse_crash_err, HTTPException):
            raise parse_crash_err
        raise HTTPException(status_code=422, detail=f"File parsing breakdown: {str(parse_crash_err)}")

# ==============================================================================
# 6. HIGH-SPEED VECTORIZED MATRIX PROFILING
# ==============================================================================

def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    total_rows: int = len(df)
    total_columns: int = len(df.columns)
    if total_rows == 0:
        return {
            "total_rows": 0, "total_columns": total_columns, "missing_values": 0,
            "duplicate_rows": 0, "empty_columns": [str(c) for c in df.columns],
            "invalid_emails": 0, "invalid_phones": 0
        }

    missing_values: int = int(df.isnull().sum().sum())
    duplicate_rows: int = int(df.duplicated().sum())
    empty_columns: List[str] = [str(col) for col in df.columns if df[col].isnull().all()]

    invalid_emails: int = 0
    email_cols: List[Any] = [col for col in df.columns if "email" in str(col).lower()]
    for col in email_cols:
        series: pd.Series = df[col].fillna("").astype(str).str.strip()
        non_empty = series[series != ""]
        if not non_empty.empty:
            invalid_emails += int((~non_empty.str.match(EMAIL_REGEX.pattern)).sum())

    invalid_phones: int = 0
    phone_cols: List[Any] = [col for col in df.columns if "phone" in str(col).lower() or "mobile" in str(col).lower()]
    for col in phone_cols:
        series: pd.Series = df[col].fillna("").astype(str).str.replace(".0", "", regex=False).str.replace(" ", "", regex=False)
        non_empty = series[series != ""]
        if not non_empty.empty:
            invalid_phones += int((~non_empty.str.match(PHONE_REGEX.pattern)).sum())

    return {
        "total_rows": total_rows, "total_columns": total_columns, "missing_values": missing_values,
        "duplicate_rows": duplicate_rows, "empty_columns": empty_columns,
        "invalid_emails": invalid_emails, "invalid_phones": invalid_phones
    }

def calculate_health_score(analysis: Dict[str, Any]) -> int:
    score: float = 100.0
    if analysis["total_rows"] == 0:
        return 100
    score -= (analysis["missing_values"] * 0.3)
    score -= (analysis["duplicate_rows"] * 1.0)
    score -= (analysis["invalid_emails"] * 0.5)
    score -= (analysis["invalid_phones"] * 0.5)
    score -= (len(analysis["empty_columns"]) * 2.0)
    return max(0, min(100, round(score)))

# ==============================================================================
# 7. AUTOMATED CLEANING EXECUTION PIPELINE
# ==============================================================================

def clean_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    cleaned_df: pd.DataFrame = df.copy()
    log: List[str] = []

    initial_row_count: int = len(cleaned_df)
    cleaned_df = cleaned_df.drop_duplicates()
    if len(cleaned_df) < initial_row_count:
        log.append(f"Dropped {initial_row_count - len(cleaned_df)} duplicate rows.")

    string_object_columns = cleaned_df.select_dtypes(include=["object"]).columns
    for col in string_object_columns:
        cleaned_df[col] = cleaned_df[col].astype(str).str.strip()

    for col in cleaned_df.columns:
        if cleaned_df[col].dtype == "object":
            cleaned_df[col] = cleaned_df[col].fillna("Unknown")
        else:
            if not cleaned_df[col].isnull().all():
                cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].median())
            else:
                cleaned_df[col] = cleaned_df[col].fillna(0)

    email_columns = [col for col in cleaned_df.columns if "email" in str(col).lower()]
    for col in email_columns:
        cleaned_df[col] = cleaned_df[col].astype(str).str.lower().str.strip()
        
    phone_columns = [col for col in cleaned_df.columns if "phone" in str(col).lower() or "mobile" in str(col).lower()]
    for col in phone_columns:
        cleaned_df[col] = cleaned_df[col].astype(str).str.replace(".0", "", regex=False).str.replace(" ", "", regex=False)

    return {"dataframe": cleaned_df, "log": log}

# ==============================================================================
# 8. MIDDLEWARE AUTH DECODE
# ==============================================================================

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization credentials missing.")
    extracted_email = verify_token(credentials.credentials)
    if not extracted_email:
        raise HTTPException(status_code=401, detail="Session expired or token verification failed.")
    return extracted_email

# ==============================================================================
# 9. COMPREHENSIVE PLATFORM CORE ROUTERS (SIGNUP & LOGIN PROTECTED)
# ==============================================================================

@app.get("/", tags=["System Infrastructure"])
def home():
    return {"message": "Welcome to PipeGuard AI API Node Service Cluster", "status": "ONLINE", "timestamp": datetime.datetime.utcnow().isoformat()}

@app.get("/api-status", response_model=APIStatusResponse, tags=["System Infrastructure"])
def api_status():
    return {
        "application": "PipeGuard AI Core Engine Mesh Node", "version": "14.0.0",
        "database": "CONNECTED", "authentication": "JWT-HS256-ACTIVE",
        "supported_files": ["csv", "xlsx", "xls", "json"], "system_time": datetime.datetime.utcnow().isoformat()
    }

@app.get("/health", tags=["System Infrastructure"])
def health_check():
    return {"status": "healthy", "service": "Core Matrix Compute Container Cluster", "uptime_state": "NOMINAL"}

@app.post("/signup", status_code=status.HTTP_201_CREATED, tags=["Auth Management"])
def signup(user: SignupRequest) -> Dict[str, Any]:
    validate_password(user.password)
    
    extracted_domain = user.email.split("@")[-1].lower()
    if extracted_domain in TEMP_EMAIL_DOMAINS:
        raise HTTPException(status_code=400, detail="Disposable or temporary emails are completely blocked.")
        
    if not user.phone.isdigit() or not re.match(r"^[6-9]\d{9}$", user.phone) or user.phone in BLOCKED_PHONES:
        raise HTTPException(status_code=400, detail="Invalid phone number parameters sequence allocation.")

    db_connection = get_db()
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute("SELECT email FROM users WHERE email = ?", (user.email,))
        if db_cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email workspace coordinate is already mapped to an active identity.")
            
        hashed_password_signature = hash_password(user.password)
        db_cursor.execute(
            """
            INSERT INTO users (full_name, company_name, country_code, phone, email, password, is_verified, plan)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Free Enterprise Tier Evaluation')
            """,
            (user.full_name, user.company_name, user.country_code, user.phone, user.email, hashed_password_signature, 1)
        )
        db_connection.commit()
    except Exception as db_err:
        if isinstance(db_err, HTTPException): raise db_err
        raise HTTPException(status_code=500, detail=f"Database persistent stack error: {str(db_err)}")
    finally:
        db_connection.close()

    generated_jwt_access_token = create_access_token(user.email)
    return {
        "message": "Corporate profile initialized successfully. Automatic workspace redirection triggered.",
        "access_token": generated_jwt_access_token,
        "token_type": "Bearer"
    }

@app.post("/login", status_code=status.HTTP_200_OK, tags=["Auth Management"])
def login(data: LoginRequest) -> Dict[str, Any]:
    login_domain = data.email.split("@")[-1].lower()
    if login_domain in TEMP_EMAIL_DOMAINS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access Denied. Tempmail channels are blacklisted on this network. Please switch to a clean account domain."
        )

    db_connection = get_db()
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute("SELECT password FROM users WHERE email = ?", (data.email,))
        user_record = db_cursor.fetchone()
    finally:
        db_connection.close()

    if not user_record or not verify_password(data.password, user_record[0]):
        raise HTTPException(status_code=401, detail="Authentication structure validation rejected. Passcode mismatch.")

    generated_jwt_access_token = create_access_token(data.email)
    return {
        "message": "Identity verified successfully. Distributing access key tokens.",
        "access_token": generated_jwt_access_token,
        "token_type": "Bearer"
    }

# ==============================================================================
# 10. USER WORKSPACE PROFILE MUTATION SETTINGS (WEBSITE EXTENSION FEATS)
# ==============================================================================

@app.get("/my-workspace", response_model=WorkspaceResponse, tags=["Account Settings Dashboard"])
def my_workspace(email: str = Depends(get_current_user)) -> Dict[str, Any]:
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute("SELECT full_name, company_name, plan FROM users WHERE email = ?", (email,))
        user_record = db_cursor.fetchone()
    finally:
        db_connection.close()

    if not user_record:
        raise HTTPException(status_code=404, detail="Workspace configuration mapping could not be safely pulled.")
        
    return {
        "email": email, "full_name": user_record[0], "company": user_record[1] if user_record[1] else "Standalone Workspace",
        "plan": user_record[2] if user_record[2] else "Evaluation Engine Node", "status": "ACTIVE"
    }

@app.put("/update-profile", tags=["Account Settings Dashboard"])
def update_profile(profile_data: ProfileUpdateRequest, email: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Allows standard web clients to mutate profile metadata tags instantly on cloud records."""
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    try:
        if profile_data.full_name:
            db_cursor.execute("UPDATE users SET full_name = ? WHERE email = ?", (profile_data.full_name, email))
        if profile_data.company_name:
            db_cursor.execute("UPDATE users SET company_name = ? WHERE email = ?", (profile_data.company_name, email))
        if profile_data.phone:
            if profile_data.phone in BLOCKED_PHONES:
                raise HTTPException(status_code=400, detail="Target phone configuration matches active system blacklist indexes.")
            db_cursor.execute("UPDATE users SET phone = ? WHERE email = ?", (profile_data.phone, email))
        db_connection.commit()
    finally:
        db_connection.close()
    return {"message": "Account workspace parameters updated across production metadata nodes."}

@app.post("/change-password", tags=["Account Settings Dashboard"])
def change_password(passkeys: PasswordChangeRequest, email: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Secures and verifies previous credential flags before matching new structural keys."""
    validate_password(passkeys.new_password)
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
        stored_hash = db_cursor.fetchone()[0]
        if not verify_password(passkeys.old_password, stored_hash):
            raise HTTPException(status_code=400, detail="Credential authentication routine failed: Old passkey match logic error.")
        
        new_hashed_signature = hash_password(passkeys.new_password)
        db_cursor.execute("UPDATE users SET password = ? WHERE email = ?", (new_hashed_signature, email))
        db_connection.commit()
    finally:
        db_connection.close()
    return {"message": "Passkey encryption block updated successfully across all matching identity pipelines."}

# ==============================================================================
# 11. REAL-TIME DATA PROCESSING PIPELINE & DATA CLEANING MANAGEMENT
# ==============================================================================

@app.post("/upload-pipeline", status_code=status.HTTP_200_OK, tags=["Data Pipeline Core"])
def upload_pipeline(pipeline_name: str, file: UploadFile = File(...), email: str = Depends(get_current_user)) -> Dict[str, Any]:
    validate_uploaded_file(file)
    dataframe_matrix, resolved_file_type = load_file_safely(file)

    analysis_metrics = analyze_dataframe(dataframe_matrix)
    computed_health_score = calculate_health_score(analysis_metrics)
    
    cleaning_pipeline_results = clean_dataframe(dataframe_matrix)
    transformed_dataframe = cleaning_pipeline_results["dataframe"]
    generated_cleaning_logs = cleaning_pipeline_results["log"]

    detected_anomalies_summary = []
    if analysis_metrics["missing_values"] > 0: detected_anomalies_summary.append(f"{analysis_metrics['missing_values']} missing elements")
    if analysis_metrics["duplicate_rows"] > 0: detected_anomalies_summary.append(f"{analysis_metrics['duplicate_rows']} duplicates")
    if analysis_metrics["invalid_emails"] > 0: detected_anomalies_summary.append(f"{analysis_metrics['invalid_emails']} bad layout emails")
    if analysis_metrics["invalid_phones"] > 0: detected_anomalies_summary.append(f"{analysis_metrics['invalid_phones']} malformed phone channels")
    if not detected_anomalies_summary: detected_anomalies_summary.append("Optimized Corporate Frame Structure Engine Sync")

    sanitized_issue_string = ", ".join(detected_anomalies_summary)

    db_connection = get_db()
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute(
            """
            INSERT INTO pipeline_reports (company_email, pipeline_name, file_type, health_score, issues, total_rows, total_columns)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (email, pipeline_name, resolved_file_type, computed_health_score, sanitized_issue_string, analysis_metrics["total_rows"], analysis_metrics["total_columns"])
        )
        db_connection.commit()
    except Exception as insert_err:
        raise HTTPException(status_code=500, detail=f"Database allocation write failure sequence collapse: {str(insert_err)}")
    finally:
        db_connection.close()

    string_io_buffer = io.StringIO()
    transformed_dataframe.to_csv(string_io_buffer, index=False)
    base64_encoded_clean_file = base64.b64encode(string_io_buffer.getvalue().encode("utf-8")).decode("utf-8")

    return {
        "message": "B2B data pipeline metrics ingestion completed successfully.", "pipeline_name": pipeline_name, "file_type": resolved_file_type,
        "health_score": computed_health_score, "issues": detected_anomalies_summary, "analysis": analysis_metrics,
        "cleaning_log": generated_cleaning_logs, "clean_file_data": base64_encoded_clean_file,
        "rows": analysis_metrics["total_rows"], "columns": analysis_metrics["total_columns"]
    }

@app.get("/my-reports", tags=["Data Pipeline Core"])
def my_reports(email: str = Depends(get_current_user)) -> Dict[str, Any]:
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute("SELECT id, pipeline_name, file_type, health_score, issues, total_rows, total_columns, created_at FROM pipeline_reports WHERE company_email = ? ORDER BY created_at DESC", (email,))
        records = db_cursor.fetchall()
    finally:
        db_connection.close()

    return {
        "email": email, "total_reports": len(records),
        "reports": [{"id": r[0], "pipeline_name": r[1], "file_type": r[2], "health_score": r[3], "issues": r[4].split(", ") if r[4] else [], "total_rows": r[5], "total_columns": r[6], "created_at": r[7]} for r in records]
    }

@app.delete("/delete-report/{report_id}", tags=["Data Pipeline Core"])
def delete_report(report_id: int, email: str = Depends(get_current_user)) -> Dict[str, str]:
    """Allows application dashboard components to purge individual evaluation reports from storage grids."""
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute("SELECT company_email FROM pipeline_reports WHERE id = ?", (report_id,))
        record = db_cursor.fetchone()
        if not record:
            raise HTTPException(status_code=404, detail="Target processing telemetry log reference missing.")
        if record[0] != email:
            raise HTTPException(status_code=403, detail="Privilege boundary exception: Resource belongs to a different structural user workspace.")
            
        db_cursor.execute("DELETE FROM pipeline_reports WHERE id = ?", (report_id,))
        db_connection.commit()
    finally:
        db_connection.close()
    return {"message": "Target monitoring pipeline trace file scrubbed successfully."}

@app.get("/dashboard-stats", tags=["Data Pipeline Core"])
def dashboard_stats(email: str = Depends(get_current_user)) -> Dict[str, Any]:
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute("SELECT COUNT(*) FROM pipeline_reports WHERE company_email = ?", (email,))
        total_reports_count = db_cursor.fetchone()[0]

        db_cursor.execute("SELECT AVG(health_score) FROM pipeline_reports WHERE company_email = ?", (email,))
        avg_health = db_cursor.fetchone()[0] or 0.0

        db_cursor.execute("SELECT pipeline_name, health_score, created_at FROM pipeline_reports WHERE company_email = ? ORDER BY created_at DESC LIMIT 5", (email,))
        recent_scans = db_cursor.fetchall()
    finally:
        db_connection.close()

    return {
        "total_reports": total_reports_count, "average_health": round(avg_health, 2),
        "recent_reports": [{"pipeline": r[0], "health_score": r[1], "created_at": r[2]} for r in recent_scans]
    }

# ==============================================================================
# 12. ADVANCED SYSTEM TELEMETRY & SYSTEM-WIDE MANAGEMENT CONTROLLERS
# ==============================================================================

@app.get("/admin/stats", tags=["System Enterprise Administration"])
def admin_global_stats(email: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Extracts total system analytics matrix counters (Requires master root level validation hooks)"""
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute("SELECT COUNT(*) FROM users")
        total_registered_accounts = db_cursor.fetchone()[0]

        db_cursor.execute("SELECT COUNT(*) FROM pipeline_reports")
        total_executed_pipelines = db_cursor.fetchone()[0]
    finally:
        db_connection.close()

    return {
        "system_status": "OPTIMAL",
        "total_registered_corporate_nodes": total_registered_accounts,
        "total_active_pipelines_evaluated": total_executed_pipelines,
        "runtime_architecture_layer": "Monolithic Multi-Tenant Secure Thread Mapping Node"
    }
