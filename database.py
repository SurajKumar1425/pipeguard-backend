import sqlite3


DATABASE_NAME = "pipeguard.db"


# -------------------------
# Get Database Connection
# -------------------------

def get_db():

    conn = sqlite3.connect(
        DATABASE_NAME,
        check_same_thread=False
    )

    return conn


# -------------------------
# Create Tables
# -------------------------

def create_tables():

    conn = get_db()

    cursor = conn.cursor()


    # Users Table

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            company_name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP

        )
        """
    )


    # Pipeline Reports Table

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_reports (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            company_email TEXT NOT NULL,

            pipeline_name TEXT NOT NULL,

            health_score INTEGER,

            issues TEXT,

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP

        )
        """
    )


    conn.commit()

    conn.close()