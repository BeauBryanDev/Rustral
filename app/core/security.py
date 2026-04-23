import logging
from datetime import datetime, timedelta
from typing import Any, Union, Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import Config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

algorithm = Config.JWT_ALGORITHM
access_token_expires = timedelta(minutes=Config.JWT_ACCESS_TOKEN_EXPIRES)
refresh_token_expires = timedelta(days=Config.JWT_REFRESH_TOKEN_EXPIRES)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = access_token_expires):
    """
    Generates a JWT access token.
    
    Args:
        data (dict): The data to include in the JWT payload.
        expires_delta (Optional[timedelta]): The expiration time for the JWT.
        
    Returns:
        str: The JWT access token.
    """
    to_encode = data.copy()
    
    if expires_delta:
        
        expire = datetime.utcnow() + expires_delta
        
        # If the access token is valid for the next hour, keep it for that long
    else:
        expire = datetime.utcnow() + access_token_expires
        
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, Config.JWT_SECRET_KEY, algorithm=algorithm)
    
    return encoded_jwt

# TODO: Implement these in blueprints managements and auth managements flask blueprints

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = refresh_token_expires):
    """  
    Generates a JWT refresh token.
    
    Args:
        data (dict): The data to include in the JWT payload.
        expires_delta (Optional[timedelta]): The expiration time for the JWT.

    Returns:
        str: The JWT refresh token.
    """
    to_encode = data.copy()
    
    if expires_delta:
        
        expire = datetime.utcnow() + expires_delta
        
    else:
        expire = datetime.utcnow() + refresh_token_expires
        
        
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, Config.JWT_SECRET_KEY, algorithm=algorithm)
    
    return encoded_jwt

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
        
        logging.error(f"Error al verif  icar el token JWT: {e}")
        
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
        
        decoded_token = jwt.decode(token, Config.SECRET_KEY, algorithms=[algorithm])
        
        return decoded_token if decoded_token["exp"] >= datetime.utcnow().timestamp() else None
    
    except JWTError as error:
        
        logging.error(f"Token decoding failed: {error}")
        
        return None
        