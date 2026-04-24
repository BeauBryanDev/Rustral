import os
from typing import List, Union

from dotenv import load_dotenv

load_dotenv()


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_list_env(name: str, default: Union[str, List[str]]) -> Union[str, List[str]]:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or default


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRES = _get_int_env("JWT_ACCESS_TOKEN_EXPIRES", 3600)
    JWT_REFRESH_TOKEN_EXPIRES = _get_int_env("JWT_REFRESH_TOKEN_EXPIRES", 86400)
    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DB = os.getenv("MONGODB_DB")
    MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION")
    MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
    MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
    MONGODB_AUTH_SOURCE = os.getenv("MONGODB_AUTH_SOURCE", "admin")
    ONNX_MODEL_PATH = os.getenv("ONNX_MODEL_PATH")
    ONNX_MODEL_NAME = os.getenv("ONNX_MODEL_NAME")
    ONNX_MODEL_INPUT_NAME = os.getenv("ONNX_MODEL_INPUT_NAME")
    ONNX_MODEL_OUTPUT_NAME = os.getenv("ONNX_MODEL_OUTPUT_NAME")
    ARUCO_REAL_SIZE = 30.00
    UPLOAD_FOLDER = os.getenv("outputs", "outputs")
    LOG_FOLDER = os.getenv("logs", "logs")
    MODEL_PATH = os.getenv("MODEL_PATH")
    CORS_ORIGINS = _get_list_env("CORS_ORIGINS", "*")
    PYTEST_CURRENT_TEST = os.getenv("PYTEST_CURRENT_TEST", None)
