import bcrypt
import jwt

from datetime import (
    datetime,
    timedelta
)

SECRET_KEY = "pipeguard_super_secret_key"


# -------------------------
# Hash Password
# -------------------------

def hash_password(password: str):

    hashed = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    )

    return hashed.decode()


# -------------------------
# Verify Password
# -------------------------

def verify_password(
    plain_password: str,
    hashed_password: str
):

    return bcrypt.checkpw(
        plain_password.encode(),
        hashed_password.encode()
    )


# -------------------------
# Create JWT Token
# -------------------------

def create_access_token(
    email: str
):

    payload = {

        "sub": email,

        "exp": datetime.utcnow()
        + timedelta(days=1)

    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm="HS256"
    )

    return token


# -------------------------
# Verify JWT Token
# -------------------------

def verify_token(
    token: str
):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        return payload["sub"]

    except:

        return None