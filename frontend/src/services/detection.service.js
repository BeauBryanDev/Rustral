import apiClient from './api';

/**
 * Service handling corrosion detection and image analysis endpoints.
 */
export const DetectionService = {
    /**
     * Submits an image to the YOLOv8 ONNX model for corrosion analysis.
     * * @param {File} imageFile - The raw image file object from an input element.
     * @param {string} locationId - The ID of the physical location being inspected.
     * @returns {Promise<Object>} The structured analysis results and fractal dimensions.
     */
    analyzeImage: async (imageFile, locationId) => {
        const formData = new FormData();
        formData.append('image', imageFile);
        formData.append('location_id', locationId);

        // We must override the default JSON content type for multipart file uploads
        const response = await apiClient.post('/detections/analyze', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        
        return response.data;
    },

    /**
     * Retrieves all detection records for the currently authenticated user.
     * * @param {string} userId - The unique identifier of the user.
     * @returns {Promise<Array>} List of detection documents.
     */
    getUserDetections: async (userId) => {
        const response = await apiClient.get(`/detections/user/${userId}`);
        return response.data;
    },
    
    /**
     * Retrieves a specific detection analysis by its ID.
     * @param {string} detectionId - The unique identifier of the detection record.
     * @returns {Promise<Object>} The detailed detection document.
     */
    getDetectionById: async (detectionId) => {
        const response = await apiClient.get(`/detections/${detectionId}`);
        return response.data;
    },

    /**
     * Retrieves all detections associated with a specific location owned by the authenticated user.
     * @param {string} locationId - The MongoDB ObjectId of the location.
     * @returns {Promise<Object>} Object containing detections array and count.
     */
    getLocationDetections: async (locationId) => {
        const response = await apiClient.get(`/detections/location/${locationId}`);
        return response.data;
    },

    /**
     * Retrieves all detections associated with a specific image owned by the authenticated user.
     * @param {string} imageId - The MongoDB ObjectId of the image.
     * @returns {Promise<Object>} Object containing detections array and count.
     */
    getImageDetections: async (imageId) => {
        const response = await apiClient.get(`/detections/image/${imageId}`);
        return response.data;
    },

    /**
     * Retrieves all detections matching a given severity level.
     * @param {'low'|'medium'|'high'|'critical'} severity - The severity level to filter by.
     * @returns {Promise<Object>} Object containing detections array, count, and severity.
     */
    getDetectionsBySeverity: async (severity) => {
        const response = await apiClient.get(`/detections/severity/${severity}`);
        return response.data;
    },

    /**
     * Deletes a detection record by its ID.
     * @param {string} detectionId - The MongoDB ObjectId of the detection to delete.
     * @returns {Promise<Object>} Success response.
     */
    deleteDetection: async (detectionId) => {
        const response = await apiClient.delete(`/detections/${detectionId}`);
        return response.data;
    },
};