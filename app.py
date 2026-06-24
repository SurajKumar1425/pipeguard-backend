from typing import Optional
from pydantic import BaseModel, EmailStr

# =========================
# SIGNUP MODEL
# =========================

class SignupRequest(BaseModel):

    full_name: str

    company_name: Optional[str] = ""

    phone: str

    email: EmailStr

    password: str

    country_code: str = "+91"


# =========================
# PHONE VALIDATION
# =========================

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


# =========================
# PASSWORD VALIDATION
# =========================

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

            detail="Password must contain uppercase, lowercase and number"

        )


# =========================
# SIGNUP API
# =========================

@app.post("/signup")
@limiter.limit("5/minute")
def signup(

    request: Request,

    user: SignupRequest

):

    try:

        print(
            f"Signup Request: {user.email}"
        )

        validate_phone_number(
            user.phone
        )

        validate_password_strength(
            user.password
        )

        conn = get_db()

        cursor = conn.cursor()
                # =========================
        # EMAIL EXISTS CHECK
        # =========================

        cursor.execute(

            """
            SELECT id

            FROM users

            WHERE email=?
            """,

            (
                str(user.email).lower(),
            )

        )

        existing_user = (
            cursor.fetchone()
        )

        if existing_user:

            conn.close()

            raise HTTPException(

                status_code=400,

                detail="Email already registered"

            )

        # =========================
        # HASH PASSWORD
        # =========================

        hashed_password = (

            hash_password(
                user.password
            )

        )

        print(
            "Password Hashed"
        )

        # =========================
        # INSERT USER
        # =========================

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

                str(user.email).lower(),

                hashed_password,

                user.country_code,

                1

            )

        )

        conn.commit()

        print(
            "User Saved"
        )
                # =========================
        # CLOSE CONNECTION
        # =========================

        conn.close()

        # =========================
        # CREATE JWT TOKEN
        # =========================

        token = create_access_token(

            str(user.email).lower()

        )

        # =========================
        # CREATE SESSION
        # =========================

        create_user_session(

            str(user.email).lower()

        )

        print(
            "Signup Success"
        )

        # =========================
        # RESPONSE
        # =========================

        return {

            "success": True,

            "message":
            "Signup successful",

            "token":
            token,

            "email":
            str(user.email).lower()

        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(

            f"Signup Error: {str(e)}"

        )

        raise HTTPException(

            status_code=500,

            detail=f"Signup Failed: {str(e)}"

        )
        
