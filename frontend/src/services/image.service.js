import apiClient from './api';

/**
 * Service handling image retrieval and management endpoints.
 */
export const ImageService = {
    /**
     * Retrieves a single image by its ID.
     * @param {string} imageId - The MongoDB ObjectId of the image.
     * @returns {Promise<Object>} The image document.
     */
    getImageById: async (imageId) => {
        const response = await apiClient.get(`/images/${imageId}`);
        return response.data;
    },

    /**
     * Retrieves all images belonging to the authenticated user.
     * @returns {Promise<Object>} Object containing images array and count.
     */
    getUserImages: async () => {
        const response = await apiClient.get('/images/user/me');
        return response.data;
    },

    /**
     * Retrieves all images associated with a specific location.
     * @param {string} locationId - The MongoDB ObjectId of the location.
     * @returns {Promise<Object>} Object containing images array and count.
     */
    getLocationImages: async (locationId) => {
        const response = await apiClient.get(`/images/location/${locationId}`);
        return response.data;
    },

    /**
     * Retrieves all images in the system. Admin only.
     * @param {number} [page=1] - Page number for pagination.
     * @param {number} [limit=20] - Number of results per page.
     * @returns {Promise<Object>} Object containing images array, count, page, and limit.
     */
    getAllImages: async (page = 1, limit = 20) => {
        const response = await apiClient.get('/images/', { params: { page, limit } });
        return response.data;
    },

    /**
     * Deletes an image by its ID.
     * @param {string} imageId - The MongoDB ObjectId of the image.
     * @returns {Promise<Object>} Success response.
     */
    deleteImage: async (imageId) => {
        const response = await apiClient.delete(`/images/${imageId}`);
        return response.data;
    },
};
