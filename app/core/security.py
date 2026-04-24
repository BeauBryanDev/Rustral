import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import Config

# bcrypt has a 72-byte input limit. Use pbkdf2_sha256 
# #for all new passwords so avoid annoying edge cases
# "where users have long passwords that get truncated and cause login issues.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

algorithm = Config.JWT_ALGORITHM
access_token_expires = timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)
refresh_token_expires = timedelta(seconds=Config.JWT_REFRESH_TOKEN_EXPIRES)


def _create_token_payload(
    subject: str,
    expires_delta: Optional[timedelta],
    token_type: str,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> dict:
    now = datetime.now(timezone.utc)
    expire_at = now + (expires_delta or access_token_expires if token_type == "access" else refresh_token_expires)

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire_at,
        "token_type": token_type,
    }

    if extra_claims:
        payload.update(extra_claims)

    return payload


def create_access_token(
    subject: str,
    extra_claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = access_token_expires,
):
    """
    Generates a JWT access token.
    
    Args:
        subject (str): The subject claim, usually the authenticated user id.
        extra_claims (Optional[Dict[str, Any]]): Additional JWT claims.
        expires_delta (Optional[timedelta]): The expiration time for the JWT.
        
    Returns:
        str: The JWT access token.
    """
    payload = _create_token_payload(
        subject=subject,
        expires_delta=expires_delta,
        token_type="access",
        extra_claims=extra_claims,
    )
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=algorithm)

# TODO: Implement these in blueprints managements and auth managements flask blueprints

def create_refresh_token(
    subject: str,
    extra_claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = refresh_token_expires,
):
    """  
    Generates a JWT refresh token.
    
    Args:
        subject (str): The subject claim, usually the authenticated user id.
        extra_claims (Optional[Dict[str, Any]]): Additional JWT claims.
        expires_delta (Optional[timedelta]): The expiration time for the JWT.

    Returns:
        str: The JWT refresh token.
    """
    payload = _create_token_payload(
        subject=subject,
        expires_delta=expires_delta,
        token_type="refresh",
        extra_claims=extra_claims,
    )
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=algorithm)

def verify_password(plain_password, hashed_password):
    """  
    Verifies a plain text password against a hashed password. 
    
    Args:    
        plain_password (str): The plain text password to verify.
        hashed_password (str): The hashed password to compare against.
        
    Returns:
        bool: True if the passwords match, False otherwise.
    """ 
    
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Generates a secure hash from a plain text password.
    
    Args:
        password (str): The raw password string.
        
    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def verify_jwt(token: str):
    """  
    Verifies a JWT token and returns the decoded payload if valid.
    
    Args:
        token (str): The JWT token to verify.
        
    Returns:
        dict: The decoded payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[algorithm])
        return payload
    except JWTError as e:
        logging.error(f"Error verifying JWT token: {e}")
        return None
    
    
def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodes and validates a JWT access token.

    Args:
        token (str): The JWT string provided in the request header.
        
    Returns:
        Optional[dict]: The token payload if valid, None otherwise.
    """
    try:
        decoded_token = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[algorithm])
        return decoded_token
    except JWTError as error:
        logging.error(f"Token decoding failed: {error}")
        return None
