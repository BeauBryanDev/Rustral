import axios from 'axios';

/**
 * Core Axios instance configured for the Rustral API.
 * The baseURL relies on Vite's proxy configuration in development.
 */
const apiClient = axios.create({
    baseURL: '/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000, 
});

/**
 * Request Interceptor: Automatically injects the JWT Bearer token into every request.
 */
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('rustral_access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

/**
 * Response Interceptor: Handles global error states, such as 401 Unauthorized.
 */
apiClient.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        if (error.response && error.response.status === 401) {
            console.warn("Authentication token expired or invalid. removing local storage.");
            localStorage.removeItem('rustral_access_token');
            localStorage.removeItem('rustral_user_id');
            
            // Redirect to login only if we are not already on the auth routes
            if (!window.location.pathname.includes('/login')) {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default apiClient;