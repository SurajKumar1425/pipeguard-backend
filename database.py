import sqlite3

DATABASE_NAME = "pipeguard.db"


# =========================
# DATABASE CONNECTION
# =========================

def get_db():

    conn = sqlite3.connect(
        DATABASE_NAME,
        check_same_thread=False
    )

    return conn


# =========================
# CREATE TABLES
# =========================

def create_tables():

    conn = get_db()

    cursor = conn.cursor()

    # =========================
    # USERS TABLE
    # =========================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            full_name TEXT NOT NULL,

            company_name TEXT,

            phone TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            is_verified INTEGER DEFAULT 0,

            otp TEXT,

            country_code TEXT DEFAULT '+91',

            plan TEXT DEFAULT 'FREE',

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP

        )
        """
    )

    # =========================
    # PIPELINE REPORTS TABLE
    # =========================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_reports (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            company_email TEXT NOT NULL,

            pipeline_name TEXT NOT NULL,

            file_type TEXT,

            health_score INTEGER,

            issues TEXT,

            total_rows INTEGER,

            total_columns INTEGER,

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP

        )
        """
    )

    conn.commit()

    conn.close()
