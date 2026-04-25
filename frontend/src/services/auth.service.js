import apiClient from './api';

/**
 * Service handling all authentication-related HTTP requests.
 */
export const AuthService = {
    /**
     * Authenticates a user and retrieves the JWT token.
     * * @param {string} email - The user's email address.
     * @param {string} password - The user's raw password.
     * @returns {Promise<Object>} The API response containing the access_token.
     */
    login: async (email, password) => {
        const response = await apiClient.post('/auth/login', { email, password });
        
        if (response.data && response.data.access_token) {
            localStorage.setItem('rustral_access_token', response.data.access_token);
            localStorage.setItem('rustral_user_id', response.data.user_id);
        }
        
        return response.data;
    },

    /**
     * Registers a new user in the Rustral system.
     * * @param {Object} userData - Dictionary containing user details (email, hash_password, etc.).
     * @returns {Promise<Object>} The API response containing the new user ID.
     */
    register: async (userData) => {
        const response = await apiClient.post('/auth/register', userData);
        return response.data;
    },

    /**
     * Clears local authentication state.
     */
    logout: () => {
        localStorage.removeItem('rustral_access_token');
        localStorage.removeItem('rustral_user_id');
    }
};