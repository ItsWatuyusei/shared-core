import logging
from typing import Optional, Any, List
from fastapi import HTTPException, status, Header
from .config import BaseInfraSettings

logger = logging.getLogger(__name__)

class BaseAuthService:
    """
    Centralized Authentication and Authorization service.
    Provides logic for admin keys and role-based access validation.
    """
    def __init__(self, settings: BaseInfraSettings):
        self.settings = settings

    def verify_infra_key(self, x_key: Optional[str]) -> bool:
        """
        Verifies if the provided key matches any of the infrastructure management keys.
        """
        if not x_key:
            return False

        authorized_keys = [
            self.settings.INFRA_ADMIN_KEY,
            self.settings.CSRF_SECRET,
            self.settings.INFRA_CORE_KEY,
            getattr(self.settings, "MANAGEMENT_API_KEY", None) 
        ]
        
        if any(x_key == k for k in authorized_keys if k):
            return True
            
        return False

    def validate_admin_access(self, x_key: Optional[str]):
        """
        Standalone validation logic for FastAPI Headers.
        """
        if not self.verify_infra_key(x_key):
            logger.warning(f"[SECURITY] Unauthorized access attempt with key: {x_key[:4] if x_key else 'None'}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Unauthorized Infrastructure Access"
            )
        return True

    def is_platform_admin(self, role: str, tenant_id: Optional[Any] = None) -> bool:
        """
        Strategic definition of a Platform Administrator.
        Must have an administrative role and operate in the Master/Root context (tenant_id is None).
        """
        is_admin_role = role in ["SuperAdmin", "platform_admin", "admin"]
        is_global_scope = tenant_id is None or str(tenant_id).lower() in ["none", "master", "0"]
        return is_admin_role and is_global_scope

    def check_permissions(self, user_permissions: str, required: List[str]) -> bool:
        """
        Standardized permission parsing (comma-separated string).
        """
        if not user_permissions:
            return False
            
        perms = set(p.strip() for p in user_permissions.split(",") if p.strip())
        return all(r in perms for r in required)
