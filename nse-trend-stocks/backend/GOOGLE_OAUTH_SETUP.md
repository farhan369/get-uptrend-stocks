# Google OAuth 2.0 Setup Guide

This guide walks you through setting up Google OAuth 2.0 authentication for the NSE Stock Screener application.

## Why Use Google OAuth?

- **Better User Experience**: Users can sign in with their existing Google account
- **Increased Security**: No need to remember another password
- **Email Verification**: Google-authenticated users are automatically verified
- **Profile Information**: Automatically get user's name and profile picture

## Prerequisites

- Google Account
- Access to Google Cloud Console
- Backend server running (for testing the redirect URI)

## Step-by-Step Setup

### 1. Go to Google Cloud Console

Visit: [https://console.cloud.google.com/](https://console.cloud.google.com/)

### 2. Create a New Project

1. Click on the project dropdown at the top
2. Click "New Project"
3. Enter project details:
   - **Name**: "Stock Trading Platform" (or any name you prefer)
   - **Organization**: Leave as default or select your organization
4. Click "Create"
5. Wait for the project to be created and select it

### 3. Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Select **External** (unless you have a Google Workspace account)
3. Click "Create"
4. Fill in the required information:
   - **App name**: Stock Trading Platform
   - **User support email**: Your email
   - **App logo**: (Optional) Upload your app logo
   - **App domain**: (Optional for development)
   - **Authorized domains**: (Optional for development)
   - **Developer contact information**: Your email
5. Click "Save and Continue"
6. **Scopes**: Click "Add or Remove Scopes"
   - Select: `openid`, `email`, `profile`
   - These are automatically added when using Google OAuth
7. Click "Save and Continue"
8. **Test users** (Optional for development):
   - Add email addresses of users who can test the app
   - In production, you'll publish the app
9. Click "Save and Continue"
10. Review and click "Back to Dashboard"

### 4. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Select **Web application**
4. Configure:
   - **Name**: "Stock Trading Web Client"
   - **Authorized JavaScript origins**:
     - `http://localhost:8000` (for development)
     - `https://yourdomain.com` (for production)
   - **Authorized redirect URIs**:
     - `http://localhost:8000/api/v2/auth/google/callback` (development)
     - `https://yourdomain.com/api/v2/auth/google/callback` (production)
5. Click "Create"
6. **Important**: Copy the Client ID and Client Secret

### 5. Update Your Backend Configuration

Add the credentials to your `.env` file:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v2/auth/google/callback
FRONTEND_URL=http://localhost:3000
```

**Security Notes:**
- ⚠️ Never commit `.env` file to version control
- ⚠️ Keep your Client Secret secure
- ⚠️ Use different credentials for development and production

### 6. Install Required Dependencies

Make sure you have the required packages:

```bash
pip install authlib==1.3.0 httpx==0.27.0
```

Or install from requirements.txt:

```bash
pip install -r requiewments.txt
```

### 7. Start Your Backend Server

```bash
python main.py
```

You should see:
```
✓ Google OAuth configured successfully
```

If you see a warning, double-check your `.env` file.

## Testing the Integration

### Method 1: Using Browser

1. Start your backend server
2. Open your browser
3. Navigate to: `http://localhost:8000/api/v2/auth/google/login`
4. You'll be redirected to Google's login page
5. Sign in with your Google account
6. Grant permissions to the app
7. You'll be redirected back with authentication data

### Method 2: Using Postman/Thunder Client

1. Open Postman
2. Create a new GET request to: `http://localhost:8000/api/v2/auth/google/login`
3. Send the request
4. Follow the OAuth flow in the browser that opens
5. Check the response for the JWT token

### Method 3: From Frontend

Add a "Sign in with Google" button:

```html
<button onclick="loginWithGoogle()">
  Sign in with Google
</button>

<script>
function loginWithGoogle() {
  window.location.href = 'http://localhost:8000/api/v2/auth/google/login';
}
</script>
```

## API Endpoints

### Initiate Google Login
```
GET /api/v2/auth/google/login
```
Redirects user to Google's OAuth consent screen.

### Handle OAuth Callback
```
GET /api/v2/auth/google/callback
```
Google redirects here after authentication. Returns JWT token and user info.

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@gmail.com",
    "username": "user_abc123",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": true,
    "oauth_provider": "google",
    "profile_picture": "https://lh3.googleusercontent.com/...",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

## User Flow

1. **New User (First Time with Google)**:
   - Clicks "Sign in with Google"
   - Authenticates with Google
   - New account is created automatically
   - Username is generated from email (e.g., `john_abc123`)
   - Default portfolio is created with ₹10 lakh
   - Email is automatically verified
   - JWT token is returned

2. **Existing User (Has Password Account)**:
   - If email already exists in the system
   - Google account is linked to existing account
   - User can now login with both Google and password

3. **Returning Google User**:
   - Clicks "Sign in with Google"
   - Authenticates with Google
   - JWT token is returned immediately
   - Profile info is updated if changed

## Frontend Integration

### React Example

```javascript
// Login component
import React from 'react';

function LoginPage() {
  const handleGoogleLogin = () => {
    window.location.href = 'http://localhost:8000/api/v2/auth/google/login';
  };

  return (
    <div>
      <button onClick={handleGoogleLogin}>
        <img src="/google-icon.svg" alt="Google" />
        Sign in with Google
      </button>
    </div>
  );
}

// Callback handler (optional - if using redirect method)
function GoogleCallback() {
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    if (token) {
      localStorage.setItem('access_token', token);
      window.location.href = '/dashboard';
    }
  }, []);

  return <div>Authenticating...</div>;
}
```

### Vue.js Example

```javascript
// Login component
export default {
  methods: {
    loginWithGoogle() {
      window.location.href = 'http://localhost:8000/api/v2/auth/google/login';
    }
  }
}
```

### Plain JavaScript

```javascript
function loginWithGoogle() {
  window.location.href = 'http://localhost:8000/api/v2/auth/google/login';
}

// On callback page
window.onload = function() {
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get('token');
  
  if (token) {
    localStorage.setItem('access_token', token);
    window.location.href = '/dashboard';
  }
};
```

## Production Deployment

### 1. Update Redirect URIs

In Google Cloud Console, add production URLs:
- `https://yourdomain.com/api/v2/auth/google/callback`

### 2. Update Environment Variables

```env
GOOGLE_REDIRECT_URI=https://yourdomain.com/api/v2/auth/google/callback
FRONTEND_URL=https://yourdomain.com
```

### 3. Publish OAuth Consent Screen

1. Go to "OAuth consent screen" in Google Cloud Console
2. Click "Publish App"
3. Submit for verification if needed (for apps requesting sensitive scopes)

### 4. Update Frontend URLs

Replace all `localhost:8000` references with your production API URL.

## Troubleshooting

### Error: "Google OAuth is not configured"

**Solution**: Check that `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in `.env`

### Error: "redirect_uri_mismatch"

**Solution**: 
1. Check that the redirect URI in `.env` matches exactly with Google Cloud Console
2. Make sure there are no trailing slashes
3. Protocol must match (http vs https)

### Error: "invalid_client"

**Solution**: 
1. Verify Client ID and Client Secret are correct
2. Make sure there are no extra spaces in `.env` file
3. Restart your backend server after changing `.env`

### User Can't Login After Google Auth

**Solution**:
- OAuth users don't have passwords
- They must use Google login only
- To add password login, implement a "Set Password" feature

### Profile Picture Not Showing

**Solution**:
- Check if the `profile_picture` URL is being returned
- Google profile pictures are hosted by Google (external URLs)
- Make sure your frontend can load external images

## Security Best Practices

1. **Environment Variables**: Never commit `.env` to git
2. **HTTPS in Production**: Always use HTTPS for production
3. **Client Secret**: Keep it secret, never expose in frontend code
4. **Token Storage**: Store JWT tokens securely (httpOnly cookies preferred)
5. **Token Expiration**: Current setup: 7 days (configurable in `auth.py`)
6. **CORS**: Configure proper CORS settings for production

## FAQ

**Q: Can users have both Google and password login?**  
A: Yes! If a user first registers with email/password, they can later link their Google account by logging in with Google using the same email.

**Q: What happens if a user changes their Google email?**  
A: The `oauth_id` (Google's internal user ID) remains the same, so the user can still login. However, their email in our database won't update automatically. Consider adding a "sync Google profile" feature.

**Q: Can I add more OAuth providers (GitHub, Facebook)?**  
A: Yes! The architecture is designed to support multiple OAuth providers. Just follow a similar pattern as Google OAuth.

**Q: Is Google OAuth free?**  
A: Yes, Google OAuth is free for most use cases. Check Google's pricing if you expect millions of users.

**Q: Do I need to verify my app with Google?**  
A: For development and private use, no. For public apps requesting sensitive scopes, yes. For basic profile access (email, name), verification is optional but recommended.

## Support

If you encounter issues:
1. Check the backend logs for detailed error messages
2. Verify all environment variables are set correctly
3. Test with the Google OAuth Playground: https://developers.google.com/oauthplayground/
4. Review Google's OAuth documentation: https://developers.google.com/identity/protocols/oauth2

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Authlib Documentation](https://docs.authlib.org/)
- [FastAPI OAuth Tutorial](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)

