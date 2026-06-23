import re
@app.post("/upload-pipeline")
def upload_pipeline(
    pipeline_name: str,
    file: UploadFile = File(...),
    email: str = Depends(get_current_user)
):

    df = pd.read_csv(file.file)

    # Missing Values
    missing_values = int(
        df.isnull().sum().sum()
    )

    # Duplicate Rows
    duplicate_rows = int(
        df.duplicated().sum()
    )

    # Invalid Emails
    invalid_emails = 0

    if "Email" in df.columns:

        email_series = (
            df["Email"]
            .dropna()
            .astype(str)
        )

        invalid_emails = int(
            (~email_series.str.match(
                r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
            )).sum()
        )

    # Invalid Phones
    invalid_phones = 0

    if "Phone" in df.columns:

        phone_series = (
            df["Phone"]
            .dropna()
            .astype(str)
        )

        invalid_phones = int(
            (~phone_series.str.match(
                r"^\d{10}$"
            )).sum()
        )

    # Negative Revenue
    negative_revenue = 0

    if "Order_Value" in df.columns:

        negative_revenue = int(
            (
                df["Order_Value"]
                .fillna(0) < 0
            ).sum()
        )

    # Health Score
    score = 100

    score -= missing_values * 2
    score -= duplicate_rows * 5
    score -= invalid_emails * 2
    score -= invalid_phones * 2
    score -= negative_revenue * 3

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

    # Save Report

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

        "issues": issues,

        "metrics": {

            "missing_values": missing_values,
            "duplicate_rows": duplicate_rows,
            "invalid_emails": invalid_emails,
            "invalid_phones": invalid_phones,
            "negative_revenue": negative_revenue

        }

    }
