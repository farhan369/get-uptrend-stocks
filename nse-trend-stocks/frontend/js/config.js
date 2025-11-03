// API Configuration
// Change this to your production URL when deploying
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : window.location.origin; // Use same origin in production

console.log('API URL:', API_URL);

