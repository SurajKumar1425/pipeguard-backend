import bcrypt
import jwt

from datetime import (
    datetime,
    timedelta
)

# =========================
# STRONG JWT SECRET
# =========================

SECRET_KEY = (
    "pipeguard_ai_v12_secure_"
    "production_jwt_secret_"
    "2026_version"
)

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_DAYS = 7


# =========================
# HASH PASSWORD
# =========================

def hash_password(
    password: str
):

    hashed = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    )

    return hashed.decode()


# =========================
# VERIFY PASSWORD
# =========================

def verify_password(
    plain_password: str,
    hashed_password: str
):

    return bcrypt.checkpw(
        plain_password.encode(),
        hashed_password.encode()
    )


# =========================
# CREATE ACCESS TOKEN
# =========================

def create_access_token(
    email: str
):

    expire = (
        datetime.utcnow()
        + timedelta(
            days=
            ACCESS_TOKEN_EXPIRE_DAYS
        )
    )

    payload = {

        "sub": email,

        "exp": expire

    }

    token = jwt.encode(

        payload,

        SECRET_KEY,

        algorithm=
        ALGORITHM

    )

    return token


# =========================
# VERIFY TOKEN
# =========================

def verify_token(
    token: str
):

    try:

        payload = jwt.decode(

            token,

            SECRET_KEY,

            algorithms=[
                ALGORITHM
            ]

        )

        return payload.get(
            "sub"
        )

    except jwt.ExpiredSignatureError:

        return None

    except jwt.InvalidTokenError:

        return None

    except Exception:

        return None
