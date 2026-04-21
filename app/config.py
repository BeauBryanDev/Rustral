import os 
from dotenv import load_dotenv

load_dotenv()

class Config:
    
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRES = os.getenv("JWT_ACCESS_TOKEN_EXPIRES")
    JWT_REFRESH_TOKEN_EXPIRES = os.getenv("JWT_REFRESH_TOKEN_EXPIRES")
    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DB = os.getenv("MONGODB_DB")
    MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION")
    MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
    MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
    MONGODB_AUTH_SOURCE = os.getenv("MONGODB_AUTH_SOURCE")
    ONNX_MODEL_PATH = os.getenv("ONNX_MODEL_PATH")
    ONNX_MODEL_NAME = os.getenv("ONNX_MODEL_NAME")
    ONNX_MODEL_INPUT_NAME = os.getenv("ONNX_MODEL_INPUT_NAME")
    ONNX_MODEL_OUTPUT_NAME = os.getenv("ONNX_MODEL_OUTPUT_NAME")
    ARUCO_REAL_SIZE  =  30.00
    UPLOAD_FOLDER = os.getenv("outputs")
    MODEL_PATH  = os.getenv("MODEL_PATH")