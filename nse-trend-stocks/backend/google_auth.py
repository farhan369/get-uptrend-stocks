"""
Google OAuth2 authentication module
Handles Google Sign-In flow for user authentication
"""
from typing import Optional, Dict, Any
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import os
import secrets
from dotenv import load_dotenv

from models import User, Portfolio
from auth import create_access_token

load_dotenv()

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v2/auth/google/callback")

# Initialize OAuth
oauth = OAuth()

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile',
            'prompt': 'select_account',  # Always show account selection
        }
    )


def is_google_oauth_configured() -> bool:
    """Check if Google OAuth is properly configured"""
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


def generate_username_from_email(email: str, db: Session) -> str:
    """
    Generate a unique username from email
    If username exists, append random string
    """
    base_username = email.split('@')[0]
    username = base_username
    counter = 1
    
    # Check if username exists and generate unique one
    while db.query(User).filter(User.username == username).first():
        if counter == 1:
            username = f"{base_username}_{secrets.token_hex(4)}"
        else:
            username = f"{base_username}_{secrets.token_hex(4)}"
        counter += 1
    
    return username


async def get_or_create_google_user(
    google_user_info: Dict[str, Any],
    db: Session
) -> User:
    """
    Get existing user by Google ID or create new user from Google profile
    
    Args:
        google_user_info: User information from Google
        db: Database session
        
    Returns:
        User object
    """
    google_id = google_user_info.get('sub')
    email = google_user_info.get('email')
    name = google_user_info.get('name', '')
    picture = google_user_info.get('picture')
    email_verified = google_user_info.get('email_verified', False)
    
    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google user information"
        )
    
    # Check if user exists with this Google ID
    user = db.query(User).filter(User.oauth_id == google_id).first()
    
    if user:
        # Update existing user info if changed
        if user.full_name != name:
            user.full_name = name
        if user.profile_picture != picture:
            user.profile_picture = picture
        if email_verified and not user.is_verified:
            user.is_verified = True
        
        db.commit()
        db.refresh(user)
        return user
    
    # Check if user exists with this email (might have registered with password)
    user = db.query(User).filter(User.email == email).first()
    
    if user:
        # Link existing account with Google
        user.oauth_provider = 'google'
        user.oauth_id = google_id
        user.profile_picture = picture
        if email_verified:
            user.is_verified = True
        
        db.commit()
        db.refresh(user)
        return user
    
    # Create new user
    username = generate_username_from_email(email, db)
    
    new_user = User(
        email=email,
        username=username,
        full_name=name,
        oauth_provider='google',
        oauth_id=google_id,
        profile_picture=picture,
        is_active=True,
        is_verified=email_verified,
        hashed_password=None  # OAuth users don't have passwords
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create default portfolio for new user
    portfolio = Portfolio(
        user_id=new_user.id,
        name="Default Portfolio",
        cash_balance=1000000.0,
        initial_balance=1000000.0,
        is_default=True
    )
    
    db.add(portfolio)
    db.commit()
    
    return new_user


def create_google_user_token(user: User) -> str:
    """
    Create JWT access token for Google authenticated user
    
    Args:
        user: User object
        
    Returns:
        JWT access token string
    """
    from datetime import timedelta
    from auth import ACCESS_TOKEN_EXPIRE_MINUTES
    
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return access_token

