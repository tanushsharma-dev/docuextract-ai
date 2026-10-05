import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import User
from app.services.email_service import generate_otp, send_otp_email

logger = logging.getLogger(__name__)
router = APIRouter()

ALGORITHM = "HS256"

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


# ---------- Password Hashing (PBKDF2 + legacy bcrypt support) ----------
def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000)
    return f"{salt}${dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        # Legacy bcrypt hashes (purane accounts) bhi chalen
        if stored.startswith(("$2b$", "$2a$", "$2y$")):
            try:
                import bcrypt
                return bcrypt.checkpw(password.encode("utf-8")[:72], stored.encode("utf-8"))
            except Exception:
                return False
        salt, dk = stored.split("$")
        calc = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000)
        return secrets.compare_digest(calc.hex(), dk)
    except Exception:
        return False


class SignupRequest(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: str
    password: str


class VerifyOtpRequest(BaseModel):
    email: str
    otp: str


class EmailOnlyRequest(BaseModel):
    email: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def create_access_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username or user.full_name or user.email.split("@")[0],
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(auth[7:], settings.JWT_SECRET, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")
        user = db.query(User).filter(User.id == payload["sub"]).first()
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
    if not user:
        raise HTTPException(401, "User not found")
    return user


def _issue_tokens(user: User):
    return {
        "access_token": create_access_token(user),
        "refresh_token": create_refresh_token(user),
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_verified": user.is_verified,
            "auth_provider": user.auth_provider,
        },
    }


def _send_new_otp(db: Session, user: User) -> bool:
    otp = generate_otp()
    user.otp_code = otp
    user.otp_expires = datetime.utcnow() + timedelta(minutes=10)
    db.commit()
    return send_otp_email(user.email, otp)


@router.post("/signup")
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    logger.info("AUTH v6 - signup request")
    email = body.email.strip().lower()
    try:
        existing = db.query(User).filter(func.lower(User.email) == email).first()
        if existing:
            if existing.is_verified:
                raise HTTPException(400, "Email already registered. Please login.")
            # Unverified purana account: password refresh kar do
            existing.hashed_password = _hash_password(body.password)
            existing.username = body.username or existing.username
            existing.full_name = body.full_name or existing.full_name
            user = existing
        else:
            user = User(
                username=body.username,
                full_name=body.full_name,
                email=email,
                hashed_password=_hash_password(body.password),
                auth_provider="local",
                is_verified=False,
            )
            db.add(user)
        db.commit()
        db.refresh(user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Signup DB error: {e}")
        raise HTTPException(500, f"Database error: {e}")

    ok = _send_new_otp(db, user)
    if not ok:
        raise HTTPException(500, "OTP email failed. Check SMTP_PASS in .env")
    return {"message": "OTP sent to email", "email": user.email}


@router.post("/verify-otp")
def verify_otp(body: VerifyOtpRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user or not user.otp_code:
        raise HTTPException(400, "Invalid request. Signup again.")
    if user.otp_expires and datetime.utcnow() > user.otp_expires:
        raise HTTPException(400, "OTP expired. Resend OTP.")
    if user.otp_code != body.otp:
        raise HTTPException(400, "Wrong OTP. Check your email again.")

    user.is_verified = True
    user.otp_code = None
    user.otp_expires = None
    db.commit()
    return _issue_tokens(user)


@router.post("/resend-otp")
def resend_otp(body: EmailOnlyRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user:
        raise HTTPException(404, "User not found. Signup first.")
    ok = _send_new_otp(db, user)
    if not ok:
        raise HTTPException(500, "OTP email failed. Check SMTP settings.")
    return {"message": "New OTP sent"}


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    try:
        identifier = body.username.strip().lower()
        logger.info(f"LOGIN ATTEMPT: identifier='{identifier}' | password_len={len(body.password)}")
        
        user = db.query(User).filter(
            (func.lower(User.email) == identifier) | (func.lower(User.username) == identifier)
        ).first()

        if not user:
            logger.info("LOGIN FAIL: No user found")
            raise HTTPException(401, "No account found. Please Sign Up first.")
        
        logger.info(f"LOGIN: Found user id={user.id} email={user.email}")
        
        if not user.hashed_password:
            raise HTTPException(401, "Ye account Google se bana hai — 'Sign in with Google' use karo.")
        
        stored = user.hashed_password
        logger.info(f"LOGIN: Stored hash starts with: '{stored[:30]}...'")
        logger.info(f"LOGIN: Stored hash length: {len(stored)}")
        
        verified = _verify_password(body.password, stored)
        logger.info(f"LOGIN: Password verification result: {verified}")
        
        if not verified:
            # Debug: manually test
            salt, dk = stored.split("$")
            calc = hashlib.pbkdf2_hmac("sha256", body.password.encode("utf-8"), bytes.fromhex(salt), 100_000)
            logger.info(f"LOGIN DEBUG: Salt={salt}")
            logger.info(f"LOGIN DEBUG: Stored dk={dk[:30]}...")
            logger.info(f"LOGIN DEBUG: Calc dk ={calc.hex()[:30]}...")
            logger.info(f"LOGIN DEBUG: Match? {calc.hex() == dk}")
            raise HTTPException(401, "Wrong password. Dobara try karo.")
        
        if not user.is_verified:
            _send_new_otp(db, user)
            raise HTTPException(403, "Email verification required. OTP sent to your email.")
        
        logger.info("LOGIN SUCCESS!")
        return _issue_tokens(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(500, f"Login error: {e}")


@router.post("/refresh")
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(body.refresh_token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(401, "Invalid token type")
        user = db.query(User).filter(User.id == payload["sub"]).first()
    except Exception:
        raise HTTPException(401, "Invalid refresh token")
    if not user:
        raise HTTPException(401, "User not found")
    return _issue_tokens(user)


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_verified": user.is_verified,
        "auth_provider": user.auth_provider,
    }


@router.get("/google")
def google_login():
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.FRONTEND_URL + "/api/v1/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "prompt": "select_account",
    }
    return RedirectResponse(GOOGLE_AUTH_URL + "?" + urlencode(params))


@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    try:
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(GOOGLE_TOKEN_URL, data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.FRONTEND_URL + "/api/v1/auth/google/callback",
                "grant_type": "authorization_code",
            })
            tokens = token_resp.json()
            if "access_token" not in tokens:
                raise HTTPException(400, f"Google token error: {tokens}")

            userinfo = (await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )).json()

        email = (userinfo.get("email") or "").strip().lower()
        if not email:
            raise HTTPException(400, "Email not received from Google")

        user = db.query(User).filter(func.lower(User.email) == email).first()
        if not user:
            user = User(
                username=email.split("@")[0],
                full_name=userinfo.get("name"),
                email=email,
                hashed_password=None,
                auth_provider="google",
                google_id=userinfo.get("sub"),
                is_verified=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google login error: {e}")
        raise HTTPException(500, f"Google login error: {e}")

    access = create_access_token(user)
    refresh_tk = create_refresh_token(user)
    username = user.username or user.full_name or email.split("@")[0]
    return RedirectResponse(
        f"{settings.FRONTEND_URL}/ui/login.html#google_token={access}&refresh={refresh_tk}&user={username}"
    )