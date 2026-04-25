import apiClient from './api';

/**
 * Service handling user account CRUD endpoints.
 */
export const UserService = {
    /**
     * Creates a new user account.
     * @param {Object} userData - Fields: email, hash_password, full_name, role (optional).
     * @returns {Promise<Object>} The created user document.
     */
    createUser: async (userData) => {
        const response = await apiClient.post('/users/', userData);
        return response.data;
    },

    /**
     * Retrieves a user by their unique ID.
     * @param {string} userId - The MongoDB ObjectId of the user.
     * @returns {Promise<Object>} The user document.
     */
    getUserById: async (userId) => {
        const response = await apiClient.get(`/users/${userId}`);
        return response.data;
    },

    /**
     * Retrieves a user by their email address.
     * @param {string} email - The user's email address.
     * @returns {Promise<Object>} The user document.
     */
    getUserByEmail: async (email) => {
        const response = await apiClient.get(`/users/email/${email}`);
        return response.data;
    },

    /**
     * Fully replaces a user document (PUT). Note: email is immutable and will be ignored.
     * @param {string} userId - The MongoDB ObjectId of the user.
     * @param {Object} userData - Full replacement fields: full_name, hash_password, role.
     * @returns {Promise<Object>} The updated user document.
     */
    updateUser: async (userId, userData) => {
        const response = await apiClient.put(`/users/${userId}`, userData);
        return response.data;
    },

    /**
     * Partially updates a user document (PATCH). Note: email is immutable and will be ignored.
     * @param {string} userId - The MongoDB ObjectId of the user.
     * @param {Object} fields - Only the fields to update.
     * @returns {Promise<Object>} The updated user document.
     */
    patchUser: async (userId, fields) => {
        const response = await apiClient.patch(`/users/${userId}`, fields);
        return response.data;
    },

    /**
     * Permanently deletes a user account.
     * @param {string} userId - The MongoDB ObjectId of the user.
     * @returns {Promise<Object>} The deleted user document.
     */
    deleteUser: async (userId) => {
        const response = await apiClient.delete(`/users/${userId}`);
        return response.data;
    },
};
