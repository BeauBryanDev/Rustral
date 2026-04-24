# FractoRust-AI

**An Industrial Computer Vision System for Automated Corrosion Detection and Analysis**

FractoRust-AI is a sophisticated AI-powered platform designed to detect, quantify, and analyze rust corrosion on metal surfaces in real-time. Leveraging advanced machine learning models (YOLO v8 with instance segmentation), ArUco marker metrology, and fractal dimension analysis, the system provides precise measurements and severity assessments for industrial inspection workflows.

<div align="center">
  <img src="fractal_rust_icon.svg" alt="Rustral Fractal Icon" width="160px" />
</div>

## Key Features

- **Real-time Corrosion Detection**: YOLOv8 ONNX-based instance segmentation model identifies rust patterns with high precision
- **Precise Spatial Quantification**: ArUco marker calibration enables pixel-to-metric conversion for accurate area measurements
- **Fractal Dimension Analysis**: Minkowski-Bouligand box-counting algorithm assesses geometric complexity and corrosion severity
- **Audit-Ready Data**: Complete detection metadata including confidence scores, pixel counts, and computed areas
- **Synchronous MongoDB Integration**: Standard `pymongo` database access for CRUD and analytics
- **JWT Authentication**: Secure REST API with token-based access control
- **Docker-Ready**: Fully containerized deployment pipeline with Docker Compose
- **Comprehensive Testing**: Unit tests with pytest and coverage tracking

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    REST API (Flask)                          │
│         /api/v1/auth | /api/v1/detections | etc.           │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴─────────┐
        │                  │
┌───────▼──────────┐  ┌────▼──────────────┐
│  Vision Service  │  │  Fractal Service  │
│                  │  │                   │
│  • ONNX Runtime  │  │  • Box Counting   │
│  • ArUco Scale   │  │  • Dimension Calc │
│  • YOLO Inference│  │  • Severity Score │
└────────┬─────────┘  └───────────────────┘
         │
    ┌────▼─────────────────┐
    │  MongoDB (pymongo)   │
    │  - Users             │
    │  - Locations         │
    │  - Images            │
    │  - Detections        │
    └──────────────────────┘
```

### Technology Stack

**Backend**
- Flask 3.0.3 - Lightweight web framework
- pymongo 4.7.2 - Synchronous MongoDB driver
- ONNX Runtime 1.19.2 - ML model inference (GPU/CPU)
- OpenCV 4.10.0 - Image processing
- JWT helpers built on `python-jose`
- Gunicorn 22.0.0 - Production WSGI server

**Frontend** (Pending)
- React + JavaScript - UI framework
- Axios - HTTP client
- Tailwind CSS - Styling
- Vite - Build tool

**Database**
- MongoDB - NoSQL document store

**Infrastructure**
- Docker & Docker Compose - Containerization
- Python 3.x - Runtime

---

## Installation

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- MongoDB instance (local or cloud)
- ONNX model file (`rust_detector_yolo.onnx`)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/BeauBryanDev/FractoRust-AI.git
   cd FractoRust-AI
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root:
   ```env
   # Flask
   SECRET_KEY=your_secret_key_here
   FLASK_ENV=development

   # JWT
   JWT_SECRET_KEY=your_jwt_secret_key
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRES=3600
   JWT_REFRESH_TOKEN_EXPIRES=86400

   # MongoDB
   MONGODB_URI=mongodb://localhost:27017
   MONGODB_DB=rust_db
   MONGODB_USERNAME=user
   MONGODB_PASSWORD=password
   MONGODB_AUTH_SOURCE=admin

   # Vision Model
   ONNX_MODEL_PATH=ml/rust_detector_yolo.onnx
   ONNX_MODEL_NAME=rust_detector_yolo
   ONNX_MODEL_INPUT_NAME=images
   ONNX_MODEL_OUTPUT_NAME=output0

   # File Uploads
   UPLOAD_FOLDER=outputs
   MODEL_PATH=ml/rust_detector_yolo.onnx
   ```

5. **Run the application**
   ```bash
   python app/app.py
   # or with Gunicorn
   gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 app.wsgi:app
   ```

---

## Docker Deployment

### Quick Start with Docker Compose

```bash
docker compose up --build
```

Services:
- Backend API: `http://localhost:5000`
- MongoDB on host: `localhost:27018`
- MongoDB inside the compose network: `mongorust:27017`

### Compose Layout

The `docker-compose.yml` file provides:
- `rustral-api` for the Flask backend
- `mongorust` for MongoDB persistence
- `rsutnet` as the shared bridge network
- A bind mount for `outputs/` so generated images are preserved on the host
- A baked-in ONNX model inside the backend image

### Environment Notes

The compose file reads `.env` values, then overrides the runtime Mongo URI so the backend connects to the containerized database instead of `localhost`.
The host Mongo port is mapped to `27018` to avoid conflicts with any other local MongoDB instance.

---

## 🔌 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and obtain JWT token

### Users
- `POST /api/v1/users/` - Create a user
- `GET /api/v1/users/<user_id>` - Retrieve a user by ID
- `GET /api/v1/users/email/<email>` - Retrieve a user by email
- `PUT /api/v1/users/<user_id>` - Replace user fields
- `PATCH /api/v1/users/<user_id>` - Partially update a user
- `DELETE /api/v1/users/<user_id>` - Delete a user

### Detections
- `POST /api/v1/detections/analyze` - Submit image for corrosion analysis
- `GET /api/v1/detections/<detection_id>` - Retrieve a detection by ID
- `GET /api/v1/detections/user/<user_id>` - Retrieve detections for the authenticated user
- `GET /api/v1/detections/location/<location_id>` - Retrieve detections for an owned location
- `GET /api/v1/detections/image/<image_id>` - Retrieve detections for an owned image
- `GET /api/v1/detections/severity/<severity>` - Retrieve detections by severity
- `DELETE /api/v1/detections/<detection_id>` - Remove a detection record

### Images
- `GET /api/v1/images/<image_id>` - Retrieve an image by ID
- `GET /api/v1/images/user/me` - Retrieve the authenticated user's images
- `GET /api/v1/images/location/<location_id>` - Retrieve images for an owned location
- `GET /api/v1/images/` - List all images for admin users
- `DELETE /api/v1/images/<image_id>` - Delete an image

### Locations
- `POST /api/v1/locations/` - Create an inspection location
- `GET /api/v1/locations/<location_id>` - Get location details
- `GET /api/v1/locations/user/me` - Retrieve the authenticated user's locations
- `PUT /api/v1/locations/<location_id>` - Replace location fields
- `PATCH /api/v1/locations/<location_id>` - Partially update a location
- `DELETE /api/v1/locations/<location_id>` - Delete a location

### Analytics
- `GET /api/v1/analytics/summary` - Admin-only system summary
- `GET /api/v1/analytics/user/me` - Current user analytics
- `GET /api/v1/analytics/location/<location_id>` - Location analytics for an owned location
- `GET /api/v1/analytics/severity-distribution` - Current user severity distribution
- `GET /api/v1/analytics/detections/fractal-dimension` - User detections filtered by fractal dimension
- `GET /api/v1/analytics/last-detections` - Current user's last detections
- `GET /api/v1/analytics/admin/recent-detections` - Admin-only recent detections
- `GET /api/v1/analytics/recent-detections` - Admin-only compatibility alias

### Health
- `GET /api/v1/health` - System status check
- `GET /api/v1/health/db` - Database connection status
- `GET /api/v1/version` - API version information

---

##  API Response Format

### Detection Response

```json
{
  "user_id": "ObjectId",
  "location_id": "ObjectId",
  "image_id": "ObjectId",
  "detections": [
    {
      "detection_id": "uuid",
      "box": [x1, y1, x2, y2],
      "confidence": 0.89,
      "area_px": 15420,
      "area_cm2": 45.32,
      "fractal_dimension": 1.67,
      "severity_level": "High",
      "pixel_count": 15420
    }
  ],
  "aruco_metadata": {
    "detected": true,
    "marker_id": 10,
    "reference_scale_cm": 30,
    "cm_per_pixel": 0.00195
  },
  "inference_time_ms": 145.23,
  "timestamp": "2024-04-21T10:30:45Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | ObjectId | MongoDB reference to analyzing user |
| `location_id` | ObjectId | MongoDB reference to inspection location |
| `image_id` | ObjectId | MongoDB reference to analyzed image |
| `box` | `[x1, y1, x2, y2]` | Bounding box coordinates in pixels |
| `confidence` | float | YOLO model confidence (0.0-1.0) |
| `area_px` | int | Corrosion area in pixels (audit data) |
| `area_cm2` | float | Corrosion area in cm² (calculated via ArUco calibration) |
| `fractal_dimension` | float | Geometric complexity score (1.0-2.0) |
| `severity_level` | string | `Low` \| `Medium` \| `High` - Inferred from dimension & area |
| `pixel_count` | int | Total pixels in detection mask |
| `marker_id` | int | ArUco marker ID for calibration |
| `reference_scale_cm` | float | ArUco physical reference size (default: 30cm) |

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app tests/

# Run specific test file
pytest tests/test_endpoints.py -v

# Run the test suite
pytest tests/test_services.py -v
```

### Test Files
- `test_endpoints.py` - API endpoint integration tests
- `test_services.py` - Vision and Fractal service unit tests
- `test_image_utils.py` - Image processing utility tests

---

## 📊 Database Schema

### Users Collection
```json
{
  "_id": ObjectId,
  "email": "user@example.com",
  "hash_password": "bcrypt_hash",
  "full_name": "User Name",
  "gender": "male",
  "phone_number": "+1...",
  "country": "USA",
  "city": "Austin",
  "is_active": true,
  "is_admin": false,
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### Locations Collection
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "name": "Factory A",
  "city": "Austin",
  "country": "USA",
  "address": "100 Industrial Way",
  "description": "Main inspection site",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### Images Collection
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "location_id": ObjectId,
  "stored_filename": "inspection_20240421.jpg",
  "stored_path": "outputs/mask_loc_....jpg",
  "mime_type": "image/jpeg",
  "size_bytes": 123456,
  "width_px": 640,
  "height_px": 640,
  "total_detections": 3,
  "created_at": ISODate
}
```

### Detections Collection
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "location_id": ObjectId,
  "image_id": ObjectId,
  "detections": [...],
  "aruco_metadata": {...},
  "inference_time_ms": 145.23,
  "detected_at": ISODate
}
```

---

##  Security Considerations

- **JWT Authentication**: All API routes protected with JWT tokens
- **Password Hashing**: BCrypt hashing for user credentials
- **CORS Configuration**: Restricted cross-origin requests
- **Environment Variables**: Sensitive data stored in `.env` (never commit)
- **Input Validation**: Request sanitization and validation
- **Rate Limiting**: (Recommended for production)

---

##  Performance Optimization

### Vision Service
- **CUDA Support**: Automatically utilizes GPU if available
- **Model Caching**: ONNX session loaded once at startup
- **Batch Processing**: Support for multiple image analysis

### Database
- **Indexing**: Recommended indexes on `user_id`, `location_id`, `detected_at`
- **Connection Pooling**: Handled by `pymongo`

### Inference
- **Average Inference Time**: ~145ms per image (GPU-accelerated)
- **Preprocessing**: Optimized OpenCV operations

---

##  Project Structure

```
FractoRust-AI/
├── app/
│   ├── __init__.py
│   ├── config.py                 # Configuration management
│   ├── app.py                    # Flask application factory / local entrypoint
│   ├── core/
│   │   ├── database.py           # MongoDB connection
│   │   ├── logging.py            # Logging setup
│   │   └── security.py           # JWT & auth utilities
│   ├── models/                   # MongoDB schemas
│   │   ├── users.py
│   │   ├── images.py
│   │   ├── locations.py
│   │   └── detections.py
│   ├── routes/                   # API endpoints
│   │   ├── auth.py
│   │   ├── detections.py
│   │   ├── images.py
│   │   ├── locations.py
│   │   ├── analytics.py
│   │   └── health.py
│   ├── services/                 # Business logic
│   │   ├── vision_service.py     # YOLO + ArUco pipeline
│   │   ├── fractal_service.py    # Dimension calculation
│   │   └── mongo_db_service.py   # Database helper wrapper
│   └── utils/
│       └── image_utils.py        # Image processing utilities
├── ml/
│   └── rust_detector_yolo.onnx   # Pre-trained YOLO v8 model
├── frontend/                      # React application (Pending)
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
├── tests/
│   ├── conftest.py
│   ├── test_endpoints.py
│   ├── test_services.py
│   └── test_image_utils.py
├── outputs/                       # Analysis results storage
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🔧 Configuration Guide

### Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `MONGODB_URI` | - | MongoDB connection string |
| `MONGODB_DB` | `rust_db` | Default database name |
| `ONNX_MODEL_PATH` | `ml/rust_detector_yolo.onnx` | Path to YOLO model |
| `ARUCO_REAL_SIZE` | `30.00` | ArUco reference marker size in cm |
| `JWT_ACCESS_TOKEN_EXPIRES` | `3600` | Token expiry in seconds (1 hour) |
| `UPLOAD_FOLDER` | `outputs` | Directory for storing results |

---

##  Future Enhancements

- [ ] Web-based dashboard (React + Vite frontend)
- [ ] Real-time WebSocket updates for long-running analyses
- [ ] Multi-model ensemble for improved accuracy
- [ ] Automated report generation (PDF export)
- [ ] S3/Cloud storage integration for images
- [ ] Advanced filtering and search capabilities
- [ ] Mobile app for field inspectors
- [ ] Machine learning model versioning and A/B testing

---

##  Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

##  Author

**BeauBryanDev**  
GitHub: [@BeauBryanDev](https://github.com/BeauBryanDev)

### Start Development Server
```bash
source venv/bin/activate
python app/app.py
```

### Run Tests
```bash
pytest --cov=app tests/
```

### Build Docker Image
```bash
docker build -t fractorust-ai:latest .
```

### MongoDB Access
If you want to inspect the database directly:

```bash
docker exec -it mongorust bash
mongosh
```

- MongoDB is exposed on host port `27018`
- Inside the compose network, the MongoDB service name is `mongorust`
- From the backend container, the database is reached through `mongorust:27017`

### Access API Documentation
Once running, visit `http://localhost:5000/api/v1/health` to verify connectivity.

---

**Last Updated**: April 2026  
**Status**: Active Development
