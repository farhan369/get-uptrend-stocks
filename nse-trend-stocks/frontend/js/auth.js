// Authentication utilities

/**
 * Get the current user's JWT token
 */
function getAuthToken() {
    return localStorage.getItem('access_token');
}

/**
 * Get the current user info
 */
function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!getAuthToken();
}

/**
 * Logout user
 */
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = './index.html';
}

/**
 * Get Axios config with auth header
 */
function getAuthHeader() {
    const token = getAuthToken();
    return token ? { headers: { 'Authorization': `Bearer ${token}` } } : {};
}

/**
 * Handle authentication errors
 */
function handleAuthError(error) {
    if (error.response && error.response.status === 401) {
        // Unauthorized - redirect to login
        logout();
    }
}

// Add axios interceptor for auth errors
if (typeof axios !== 'undefined') {
    axios.interceptors.response.use(
        response => response,
        error => {
            handleAuthError(error);
            return Promise.reject(error);
        }
    );
}

