import apiClient from './api';

/**
 * Service handling location CRUD endpoints.
 */
export const LocationService = {
    /**
     * Creates a new inspection location.
     * @param {Object} locationData - Fields: name, latitude, longitude, address.
     * @returns {Promise<Object>} The new location_id.
     */
    createLocation: async (locationData) => {
        const response = await apiClient.post('/locations/', locationData);
        return response.data;
    },

    /**
     * Retrieves a single location by its ID.
     * @param {string} locationId - The MongoDB ObjectId of the location.
     * @returns {Promise<Object>} The location document.
     */
    getLocationById: async (locationId) => {
        const response = await apiClient.get(`/locations/${locationId}`);
        return response.data;
    },

    /**
     * Retrieves all locations belonging to the authenticated user.
     * @returns {Promise<Object>} Object containing locations array and count.
     */
    getUserLocations: async () => {
        const response = await apiClient.get('/locations/user/me');
        return response.data;
    },

    /**
     * Fully replaces a location document (PUT).
     * @param {string} locationId - The MongoDB ObjectId of the location.
     * @param {Object} locationData - Full replacement fields.
     * @returns {Promise<Object>} Success response.
     */
    updateLocation: async (locationId, locationData) => {
        const response = await apiClient.put(`/locations/${locationId}`, locationData);
        return response.data;
    },

    /**
     * Partially updates a location document (PATCH).
     * @param {string} locationId - The MongoDB ObjectId of the location.
     * @param {Object} fields - Only the fields to update.
     * @returns {Promise<Object>} Success response.
     */
    patchLocation: async (locationId, fields) => {
        const response = await apiClient.patch(`/locations/${locationId}`, fields);
        return response.data;
    },

    /**
     * Deletes a location by its ID.
     * @param {string} locationId - The MongoDB ObjectId of the location.
     * @returns {Promise<Object>} Success response.
     */
    deleteLocation: async (locationId) => {
        const response = await apiClient.delete(`/locations/${locationId}`);
        return response.data;
    },
};
