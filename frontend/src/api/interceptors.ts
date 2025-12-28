/**
 * API Interceptors - Handle auth tokens and CSRF protection
 */

import axios from 'axios';

const AUTH_TOKEN_KEY = 'solarpunk_auth_token';
const CSRF_TOKEN_KEY = 'solarpunk_csrf_token';

// Methods that require CSRF protection
const CSRF_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

// Fetch CSRF token from server
async function fetchCsrfToken(): Promise<string> {
  const response = await axios.post('/auth/csrf-token', {}, {
    // Skip the interceptor for this request to avoid infinite loop
    headers: { 'X-Skip-CSRF': 'true' }
  });
  const token = response.data.csrf_token;
  sessionStorage.setItem(CSRF_TOKEN_KEY, token);
  return token;
}

// Get cached CSRF token or fetch new one
async function getCsrfToken(): Promise<string> {
  let token = sessionStorage.getItem(CSRF_TOKEN_KEY);
  if (!token) {
    token = await fetchCsrfToken();
  }
  return token;
}

// Add auth token and CSRF token to requests
axios.interceptors.request.use(
  async (config) => {
    // Add auth token
    const authToken = localStorage.getItem(AUTH_TOKEN_KEY);
    if (authToken) {
      config.headers.Authorization = `Bearer ${authToken}`;
    }

    // Add CSRF token for state-changing methods (skip if marked)
    const method = config.method?.toUpperCase() || 'GET';
    if (CSRF_METHODS.includes(method) && !config.headers['X-Skip-CSRF']) {
      try {
        const csrfToken = await getCsrfToken();
        config.headers['X-CSRF-Token'] = csrfToken;
      } catch (error) {
        console.warn('Failed to get CSRF token:', error);
      }
    }

    // Remove the skip marker so it doesn't get sent to server
    delete config.headers['X-Skip-CSRF'];

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle 401 and 403 responses
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error.response?.status;

    if (status === 401) {
      // Clear invalid token
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem('solarpunk_auth_user');

      // Redirect to login if not already there
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    } else if (status === 403 && error.response?.data?.detail?.includes('CSRF')) {
      // CSRF token expired or invalid, clear and retry once
      sessionStorage.removeItem(CSRF_TOKEN_KEY);

      // Retry the original request with a fresh token
      const config = error.config;
      if (!config._csrfRetry) {
        config._csrfRetry = true;
        const newToken = await fetchCsrfToken();
        config.headers['X-CSRF-Token'] = newToken;
        return axios(config);
      }
    }

    return Promise.reject(error);
  }
);

export default axios;
