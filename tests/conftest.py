import os
import sys
import types
import cv2
import pytest
import numpy as np
from unittest.mock import patch, MagicMock


try:
    import pkg_resources  # type: ignore
except ModuleNotFoundError:
    # mongomock 4.1.2 imports pkg_resources from setuptools at import time.
    # Some CI images do not expose that module early enough, so provide a tiny
    # compatibility shim before importing mongomock.
    pkg_resources = types.ModuleType("pkg_resources")

    class _Distribution:
        version = "4.1.2"

    def _get_distribution(name):
        return _Distribution()

    pkg_resources.get_distribution = _get_distribution
    sys.modules["pkg_resources"] = pkg_resources

import mongomock


os.environ["SECRET_KEY"] = "test_super_secret_key"
os.environ["ONNX_MODEL_PATH"] = "dummy_path.onnx"
os.environ["JWT_SECRET_KEY"] = "test_jwt_secret"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_ACCESS_TOKEN_EXPIRES"] = "3600"
os.environ["JWT_REFRESH_TOKEN_EXPIRES"] = "86400"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB"] = "test_db"
os.environ["MONGODB_COLLECTION"] = "detections"
os.environ["ONNX_MODEL_INPUT_NAME"] = "images"
os.environ["ONNX_MODEL_OUTPUT_NAME"] = "output0"


if "flask_cors" not in sys.modules:
    flask_cors_stub = types.ModuleType("flask_cors")

    def _cors_stub(app, *args, **kwargs):
        return app

    flask_cors_stub.CORS = _cors_stub
    sys.modules["flask_cors"] = flask_cors_stub


if "onnxruntime" not in sys.modules:
    onnxruntime_stub = types.ModuleType("onnxruntime")

    class _StubInput:
        name = "images"

    class _StubOutput:
        def __init__(self, name):
            self.name = name

    class _StubInferenceSession:
        def __init__(self, *args, **kwargs):
            self._inputs = [_StubInput()]
            self._outputs = [_StubOutput("output0"), _StubOutput("output1")]

        def get_inputs(self):
            return self._inputs

        def get_outputs(self):
            return self._outputs

        def run(self, *args, **kwargs):
            return [
                np.zeros((1, 116, 8400), dtype=np.float32),
                np.zeros((1, 32, 160, 160), dtype=np.float32),
            ]

    onnxruntime_stub.InferenceSession = _StubInferenceSession
    sys.modules["onnxruntime"] = onnxruntime_stub


# Patch MongoClient before importing db_instance
with patch('pymongo.MongoClient', mongomock.MongoClient):
    from app.core.database import db_instance

# Also make sure the db_instance uses mocked client
db_instance._client = mongomock.MongoClient()
db_instance._db = db_instance._client['test_db']
db_instance._connected = True

# Now import app components that depend on config
from app.core.security import create_access_token
from app.app import create_app

@pytest.fixture(autouse=True)
def mock_database():
    """
    Globally intercepts MongoDB connections for all tests.
    Forces the Singleton db_instance to use mongomock instead of real pymongo.
    The 'autouse=True' ensures no test ever writes to the production database.
    """
    if db_instance is None:
        yield None
        return
        
    with patch("app.core.database.MongoClient", mongomock.MongoClient):
        # Reset the singleton to use the mocked client
        db_instance._client = mongomock.MongoClient()
        db_instance._db = db_instance._client["test_fractorust_db"]
        yield db_instance
        # Cleanup after each test
        db_instance._client.drop_database("test_fractorust_db")


@pytest.fixture(autouse=True)
def mock_onnx_runtime():
    """
    Globally intercepts ONNX Runtime initialization.
    Prevents the VisionService from attempting to load heavy .onnx files from disk.
    Provides dummy outputs matching the expected YOLOv8 tensor shapes.
    """
    with patch("onnxruntime.InferenceSession") as mock_session:
        mock_instance = MagicMock()
        
        # Mocking input/output metadata
        mock_input = MagicMock()
        mock_input.name = "images"
        mock_instance.get_inputs.return_value = [mock_input]
        
        mock_output1 = MagicMock()
        mock_output1.name = "output0"
        mock_output2 = MagicMock()
        mock_output2.name = "output1"
        mock_instance.get_outputs.return_value = [mock_output1, mock_output2]
        
        # Mocking inference execution to return zeros simulating YOLO tensors
        # output0: boxes/conf/masks (1, 116, 8400), output1: prototypes (1, 32, 160, 160)
        mock_instance.run.return_value = [
            np.zeros((1, 116, 8400), dtype=np.float32),
            np.zeros((1, 32, 160, 160), dtype=np.float32)
        ]
        
        mock_session.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="session")
def app_client():
    """
    Provides a Flask test client for integration testing of the API endpoints.
    """
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers():
    """
    Generates a valid Bearer token for a dummy user ID to test protected routes.
    """
    dummy_user_id = "60d5ec49f1b2c8b1f8e4b5a1"
    token = create_access_token(subject=dummy_user_id)
    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture
def admin_auth_headers():
    """
    Generates a valid Bearer token for a dummy admin user ID to test admin routes.
    """
    dummy_admin_user_id = "60d5ec49f1b2c8b1f8e4b5a2"
    token = create_access_token(subject=dummy_admin_user_id)
    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture
def valid_image_bytes():
    """
    Generates a valid 640x640 JPEG image entirely in memory.
    Useful for testing the /analyze endpoint without needing physical files.
    """
    # Create a blank black image
    dummy_image = np.zeros((640, 640, 3), dtype=np.uint8)
    
    # Draw a white rectangle to simulate a bright object
    cv2.rectangle(dummy_image, (100, 100), (300, 300), (255, 255, 255), -1)
    
    # Encode to JPEG format
    success, encoded_image = cv2.imencode('.jpg', dummy_image)
    if not success:
        raise ValueError("Failed to encode dummy image fixture")
        
    return encoded_image.tobytes()
