import logging
from typing import Any, Optional, Type, Protocol
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class BaseTenantService:
    """
    Centralized service for Tenant operations: Search -> Log -> Cache Invalidation.
    Designed to be used via composition.
    """
    def __init__(self, tenant_model: Type, log_model: Type, cache_service: Any = None):
        self.tenant_model = tenant_model
        self.log_model = log_model
        self.cache = cache_service

    async def find_tenant(self, db: AsyncSession, identifier: Any) -> Any:
        """
        Generic search by ID or Domain (case-insensitive).
        """
        
        stmt = select(self.tenant_model).filter(self.tenant_model.id == str(identifier))
        tenant = (await db.execute(stmt)).scalars().first()

        if not tenant:
            stmt = select(self.tenant_model).filter(func.lower(self.tenant_model.domain) == str(identifier).lower())
            tenant = (await db.execute(stmt)).scalars().first()
            
        if not tenant:
            raise HTTPException(status_code=404, detail=f"Tenant '{identifier}' not found.")
            
        return tenant

    async def log_action(self, db: AsyncSession, tenant_id: Any, action: str, message: str, status: str = "SUCCESS"):
        """
        Standardized logging to TenantLog.
        """
        try:
            log_entry = self.log_model(
                tenant_id=tenant_id,
                action=action,
                status=status,
                message=message
            )
            db.add(log_entry)
            logger.info(f"[TENANT-LOG] {action} for {tenant_id}: {message}")
        except Exception as e:
            logger.error(f"Failed to log tenant action: {e}")

    async def invalidate_cache(self, tenant_id: Any):
        """
        Invalidates tenant cache if provider is available.
        """
        if self.cache and hasattr(self.cache, "invalidate_tenant"):
            try:
                self.cache.invalidate_tenant(tenant_id)
                logger.debug(f"[CACHE] Invalidated tenant {tenant_id}")
            except Exception as e:
                logger.warning(f"Cache invalidation failed: {e}")
