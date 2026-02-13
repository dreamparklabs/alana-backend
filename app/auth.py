from datetime import datetime, timedelta
from typing import Optional
import httpx
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import uuid

from app.config import get_settings
from app.database import get_db
from app.models.user import User

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

# Cache for OIDC JWKS
_jwks_cache: dict = {}
_jwks_cache_time: Optional[datetime] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


async def get_oidc_jwks() -> dict:
    """Fetch and cache OIDC JWKS from the issuer."""
    global _jwks_cache, _jwks_cache_time
    
    # Return cached JWKS if still valid (cache for 1 hour)
    if _jwks_cache and _jwks_cache_time and (datetime.utcnow() - _jwks_cache_time).seconds < 3600:
        return _jwks_cache
    
    if not settings.oidc_issuer:
        return {}
    
    try:
        # Fetch OIDC discovery document
        async with httpx.AsyncClient() as client:
            discovery_url = f"{settings.oidc_issuer.rstrip('/')}/.well-known/openid-configuration"
            discovery_resp = await client.get(discovery_url)
            discovery_resp.raise_for_status()
            discovery = discovery_resp.json()
            
            # Fetch JWKS
            jwks_uri = discovery.get("jwks_uri")
            if jwks_uri:
                jwks_resp = await client.get(jwks_uri)
                jwks_resp.raise_for_status()
                _jwks_cache = jwks_resp.json()
                _jwks_cache_time = datetime.utcnow()
                return _jwks_cache
    except Exception as e:
        print(f"Failed to fetch OIDC JWKS: {e}")
    
    return {}


async def validate_oidc_token(token: str) -> Optional[dict]:
    """Validate an OIDC access token and return the claims."""
    if not settings.oidc_issuer:
        return None
    
    try:
        jwks = await get_oidc_jwks()
        if not jwks:
            return None
        
        # Decode without verification first to get the header
        unverified_header = jwt.get_unverified_header(token)
        
        # Find the matching key
        rsa_key = {}
        for key in jwks.get("keys", []):
            if key.get("kid") == unverified_header.get("kid"):
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key.get("use", "sig"),
                    "n": key["n"],
                    "e": key["e"],
                }
                break
        
        if not rsa_key:
            return None
        
        # Validate the token
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=settings.oidc_client_id if settings.oidc_client_id else None,
            issuer=settings.oidc_issuer,
            options={"verify_aud": bool(settings.oidc_client_id)}
        )
        
        return payload
    except JWTError as e:
        print(f"OIDC token validation failed: {e}")
        return None


async def get_or_create_user_from_oidc(claims: dict, db: Session) -> User:
    """Get or create a user from OIDC claims."""
    # Extract user info from claims
    sub = claims.get("sub")
    email = claims.get("email")
    email_verified = claims.get("email_verified", False)
    given_name = claims.get("given_name", "")
    family_name = claims.get("family_name", "")
    name = claims.get("name", "")
    
    # Build full name from given_name and family_name, or fall back to name
    if given_name or family_name:
        full_name = f"{given_name} {family_name}".strip()
    else:
        full_name = name or email.split("@")[0] if email else "User"
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required from SSO provider"
        )
    
    # Check email verification requirement
    if settings.require_email_verified and not email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email must be verified. Please verify your email in the SSO provider."
        )
    
    # Check MFA requirement (authentik uses acr_values or amr claims)
    if settings.require_mfa:
        amr = claims.get("amr", [])
        acr = claims.get("acr", "")
        # Check if MFA was used (common values: mfa, otp, totp, webauthn)
        mfa_methods = {"mfa", "otp", "totp", "webauthn", "hwk"}
        has_mfa = any(method in mfa_methods for method in amr) or "mfa" in acr.lower()
        
        if not has_mfa:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Multi-factor authentication is required. Please set up MFA in your account settings."
            )
    
    # Look up user by email (or SSO subject ID)
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create new user from SSO
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            full_name=full_name,
            hashed_password="",  # No password for SSO users
            is_active=True,
            is_verified=email_verified,
            sso_subject_id=sub,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update user info from SSO if changed
        updated = False
        if user.full_name != full_name and full_name:
            user.full_name = full_name
            updated = True
        if not user.sso_subject_id and sub:
            user.sso_subject_id = sub
            updated = True
        if user.is_verified != email_verified:
            user.is_verified = email_verified
            updated = True
        if updated:
            db.commit()
            db.refresh(user)
    
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    # First, try to validate as OIDC token (from SSO)
    if settings.oidc_issuer:
        oidc_claims = await validate_oidc_token(token)
        if oidc_claims:
            return await get_or_create_user_from_oidc(oidc_claims, db)
    
    # Fall back to local JWT validation
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
