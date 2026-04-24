
import time 
import logging
from flask import Blueprint, request, jsonify, g 

from app.core.error_handlers import handle_api_exceptions, success_response
from app.core.exceptions import ValidationException, ForbiddenException

from app.services.detection_service import detection_service
from app.services.vision_service import vision_service_instance
from app.services.image_service import image_service
from app.services.storage_service import storage_service
from app.core.database import db_instance
from app.models.detections import DetectionDocument
from app.services.location_CRUD_service import location_service
from app.utils.image_utils import decode_image_bytes, draw_corrosion_analysis
from app.routes.dependencies import jwt_required
"""
Flask Blueprint for Detection Management Routes
IT Provides RESTful endpoints for all detection CRUD operations:
- POST /ap1/v1/detections   - Make detections -> | Full Inferecne Pipeline 
- GET /api/v1/detections/<detection_id> - Retrieve detection by ID
- GET /api/v1/detections/user/<user_id> - Get detections by user
- GET /api/v1/detections/location/<location_id> - Get detections by location
- GET /api/v1/detections/image/<image_id> - Get detections by image
- GET /api/v1/detections/severity/<severity> - Get detections by severity
- DELETE /api/v1/detections/<detection_id> - Delete detection
"""

logger = logging.getLogger(__name__)

detections_bp = Blueprint(
    'detections',
    __name__,
    url_prefix='/api/v1/detections'
)

@detections_bp.route('/analyze', methods=['POST'])
@jwt_required
def analyze_image_endpoint():
    """
    Main inference endpoint.
    Expects multipart/form-data with an 'image' file and a 'location_id'.
    Processes the image through YOLOv8, calculates metrics, saves the file, and stores the document.
    
    Returns:
        JSON response with detection metadata and database ID.
    """
    request_start_time = time.perf_counter()
    
    try:
        #  Validate incoming payload
        if 'image' not in request.files:
            
            return jsonify({"error": "No image file provided in request"}), 400
            
        location_id = request.form.get('location_id')
        
        if not location_id:
            
            return jsonify({"error": "Missing location_id in form data"}), 400

        file = request.files['image']
        # TODO:  apply better HTTP Errro handling in order to make easier frotnend debugging with ReactJS
        if file.filename == '':
            
            return jsonify({"error": "Empty filename"}), 400

        #  Decode image to numpy array
        image_bytes = file.read()
        
        try:
            
            image_np = decode_image_bytes(image_bytes)
            
        except ValueError as e:
            
            return jsonify({"error": str(e)}), 400

        #  Execute Vision Pipeline (Inference, Metrology, Fractals)
        analysis_results = vision_service_instance.analyze_corrosion(image_np)
        #  Draw corrosion bounding box on annotated_img 
        detections_list = analysis_results.get("detections", [])
        annotated_image = draw_corrosion_analysis(image_np, detections_list)
        #  Save the processed image (assuming vision_service drew the masks on image_np)
        saved_path = storage_service.save_masked_image(annotated_image, location_id)

        #  Build and save the Detection Document to MongoDB
        user_id = g.user_id  # Extracted from JWT token
        
        detection_doc = DetectionDocument(
            user_id=user_id,
            location_id=location_id,
            image_id=None, # Update this if an ImageDocument is created prior to this step
            detections=analysis_results.get("detections", []),
            aruco_metadata=analysis_results.get("aruco_metadata", {}),
            inference_time_ms=analysis_results.get("inference_time_ms", 0.0)
        )
        
        insert_result = db_instance.db.detections.insert_one(detection_doc.to_dict())
        document_id = str(insert_result.inserted_id)
        
        total_request_time = (time.perf_counter() - request_start_time) * 1000.0
        logger.info(f"Full inference cycle completed for location {location_id} in {total_request_time:.2f}ms")

        # 6. Return structured response
        return jsonify({
            "message": "Analysis successful",
            "detection_id": document_id,
            "saved_image_path": saved_path,
            "metrics": analysis_results
        }), 201

    except Exception as error:
        
        logger.error(f"Inference endpoint failed: {error}", exc_info=True)
        
        return jsonify({"error": "Internal server error during image analysis"}), 500


@detections_bp.route('/<detection_id>', methods=['GET'])
@jwt_required
@handle_api_exceptions
def get_detection(detection_id):
    """
    Retrieve a detection by its unique ID.
    
    URL Parameters:
        detection_id (str): MongoDB ObjectId of the detection
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "Detection retrieved successfully",
                "data": {
                    "_id": "507f1f77bcf86cd799439015",
                    "image_id": "507f1f77bcf86cd799439011",
                    "user_id": "507f1f77bcf86cd799439012",
                    "location_id": "507f1f77bcf86cd799439014",
                    "severity": "high",
                    "fractal_dimension": 2.45,
                    "created_at": "2026-04-23T10:30:00"
                }
            }
    
    Raises:
        400 Bad Request: If detection_id is not a valid ObjectId
        404 Not Found: If detection does not exist
        500 Internal Server Error: Database errors
    """
    detection = detection_service.get_detection_by_id(detection_id)

    if str(detection.get("user_id")) != str(g.user_id):
        raise ForbiddenException(
            message="You do not have permission to access this detection",
            error_code="DETECTION_ACCESS_DENIED",
            details={"detection_id": detection_id}
        )
    
    return success_response(
        data=detection,
        status_code=200,
        message="Detection retrieved successfully"
    )


@detections_bp.route('/user/<user_id>', methods=['GET'])
@jwt_required
@handle_api_exceptions
def get_user_detections(user_id):
    """
    Get all detections for a specific user.
    
    URL Parameters:
        user_id (str): MongoDB ObjectId of the user
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "User detections retrieved successfully",
                "data": {
                    "detections": [...],
                    "count": 8
                }
            }
    
    Raises:
        403 Forbidden: If the requested user_id does not match the authenticated user
        500 Internal Server Error: Database errors
    """
    authenticated_user_id = str(g.user_id)

    if str(user_id) != authenticated_user_id:
        raise ForbiddenException(
            message="You do not have permission to access another user's detections",
            error_code="USER_DETECTIONS_ACCESS_DENIED",
            details={"user_id": user_id}
        )

    detections = detection_service.get_all_detection_by_user(authenticated_user_id)
    
    return success_response(
        data={"detections": detections, "count": len(detections)},
        status_code=200,
        message="User detections retrieved successfully"
    )


@detections_bp.route('/location/<location_id>', methods=['GET'])
@jwt_required
@handle_api_exceptions
def get_location_detections(location_id):
    """
    Get all detections for a specific location.
    
    URL Parameters:
        location_id (str): MongoDB ObjectId of the location
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "Location detections retrieved successfully",
                "data": {
                    "detections": [...],
                    "count": 3
                }
            }
    
    Raises:
        400 Bad Request: If location_id is not a valid ObjectId
        403 Forbidden: If the location does not belong to the authenticated user
        500 Internal Server Error: Database errors
    """
    location = location_service.get_location_by_id(location_id)

    if str(location.get("user_id")) != str(g.user_id):
        raise ForbiddenException(
            message="You do not have permission to access detections for this location",
            error_code="LOCATION_ACCESS_DENIED",
            details={"location_id": location_id}
        )

    detections = detection_service.get_detections_by_location(location_id)
    
    return success_response(
        data={"detections": detections, "count": len(detections)},
        status_code=200,
        message="Location detections retrieved successfully"
    )


@detections_bp.route('/image/<image_id>', methods=['GET'])
@jwt_required
@handle_api_exceptions
def get_image_detections(image_id):
    """
    Get all detections for a specific image.
    
    URL Parameters:
        image_id (str): MongoDB ObjectId of the image
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "Image detections retrieved successfully",
                "data": {
                    "detections": [...],
                    "count": 2
                }
            }
    
    Raises:
        400 Bad Request: If image_id is not a valid ObjectId
        500 Internal Server Error: Database errors
    """
    image = image_service.get_image_by_id(image_id)

    if str(image.get("user_id")) != str(g.user_id):
        raise ForbiddenException(
            message="You do not have permission to access detections for this image",
            error_code="IMAGE_DETECTIONS_ACCESS_DENIED",
            details={"image_id": image_id}
        )

    detections = detection_service.get_detections_by_image(image_id)
    
    return success_response(
        data={"detections": detections, "count": len(detections)},
        status_code=200,
        message="Image detections retrieved successfully"
    )


@detections_bp.route('/severity/<severity>', methods=['GET'])
@handle_api_exceptions
def get_detections_by_severity(severity):
    """
    Get all detections with a specific severity level.
    
    URL Parameters:
        severity (str): One of 'low', 'medium', 'high', 'critical'
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "Detections with severity 'high' retrieved successfully",
                "data": {
                    "detections": [...],
                    "count": 5,
                    "severity": "high"
                }
            }
    
    Raises:
        422 Validation Error: Invalid severity level
        500 Internal Server Error: Database errors
    """
    valid_severities = ['low', 'medium', 'high', 'critical']
    if severity not in valid_severities:
        raise ValidationException(
            field="severity",
            reason=f"Invalid severity. Must be one of {valid_severities}"
        )
    
    detections = detection_service.get_all_detection_by_severity(severity)
    
    return success_response(
        data={"detections": detections, "count": len(detections), "severity": severity},
        status_code=200,
        message=f"Detections with severity '{severity}' retrieved successfully"
    )


@detections_bp.route('/<detection_id>', methods=['DELETE'])
@jwt_required
@handle_api_exceptions
def delete_detection(detection_id):
    """
    Delete a detection by its ID.
    
    URL Parameters:
        detection_id (str): MongoDB ObjectId of the detection
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "Detection deleted successfully",
                "data": {}
            }
    
    Raises:
        400 Bad Request: If detection_id is not a valid ObjectId
        404 Not Found: If detection does not exist
        500 Internal Server Error: Database errors
    
    Warning:
        This operation is permanent and cannot be undone.
    """
    detection = detection_service.get_detection_by_id(detection_id)

    if str(detection.get("user_id")) != str(g.user_id):
        raise ForbiddenException(
            message="You do not have permission to delete this detection",
            error_code="DETECTION_DELETE_DENIED",
            details={"detection_id": detection_id}
        )

    detection_service.delete_detection(detection_id)
    
    return success_response(
        data={},
        status_code=200,
        message="Detection deleted successfully"
    )
