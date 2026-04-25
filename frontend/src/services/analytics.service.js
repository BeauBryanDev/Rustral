import apiClient from './api';

/**
 * Service handling analytics and dashboard data endpoints.
 */
export const AnalyticsService = {
    /**
     * Retrieves a system-wide dashboard summary. Admin only.
     * @returns {Promise<Object>} Aggregated platform statistics.
     */
    getSummary: async () => {
        const response = await apiClient.get('/analytics/summary');
        return response.data;
    },

    /**
     * Retrieves analytics for the authenticated user.
     * @returns {Promise<Object>} Detection stats, severity distribution, and location counts.
     */
    getUserAnalytics: async () => {
        const response = await apiClient.get('/analytics/user/me');
        return response.data;
    },

    /**
     * Retrieves analytics for a specific location owned by the authenticated user.
     * @param {string} locationId - The MongoDB ObjectId of the location.
     * @returns {Promise<Object>} Detection stats and severity distribution for that location.
     */
    getLocationAnalytics: async (locationId) => {
        const response = await apiClient.get(`/analytics/location/${locationId}`);
        return response.data;
    },

    /**
     * Retrieves severity distribution for the authenticated user's detections.
     * @param {string} [locationId] - Optional location filter.
     * @returns {Promise<Object>} Counts per severity level (low, medium, high, critical) plus total.
     */
    getSeverityDistribution: async (locationId = null) => {
        const params = locationId ? { location_id: locationId } : {};
        const response = await apiClient.get('/analytics/severity-distribution', { params });
        return response.data;
    },

    /**
     * Retrieves the authenticated user's most recent detection documents.
     * @param {number} [limit=10] - Maximum number of records to return.
     * @returns {Promise<Object>} Object containing detections array, count, and user_id.
     */
    getLastDetections: async (limit = 10) => {
        const response = await apiClient.get('/analytics/last-detections', { params: { limit } });
        return response.data;
    },

    /**
     * Retrieves recent detection documents for the admin dashboard. Admin only.
     * @param {number} [limit=10] - Maximum number of records to return.
     * @returns {Promise<Object>} Object containing detections array and count.
     */
    getAdminRecentDetections: async (limit = 10) => {
        const response = await apiClient.get('/analytics/admin/recent-detections', { params: { limit } });
        return response.data;
    },

    /**
     * Retrieves flattened detection entries filtered by fractal dimension range.
     * @param {Object} [filters={}]
     * @param {number} [filters.min=0.0] - Minimum fractal dimension.
     * @param {number} [filters.max] - Maximum fractal dimension (optional).
     * @param {number} [filters.limit=50] - Maximum number of results.
     * @param {string} [filters.locationId] - Optional owned location filter.
     * @returns {Promise<Object>} Object containing detections array, count, and applied filters.
     */
    getDetectionsByFractalDimension: async ({ min = 0.0, max, limit = 50, locationId } = {}) => {
        const params = { min, limit };
        if (max !== undefined) params.max = max;
        if (locationId) params.location_id = locationId;
        const response = await apiClient.get('/analytics/detections/fractal-dimension', { params });
        return response.data;
    },
};
