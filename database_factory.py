import logging
import asyncio
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from .config import BaseInfraSettings
from .exceptions import DatabaseConfigurationError

logger = logging.getLogger(__name__)

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.pool import QueuePool

class BaseConnectionFactory:

    def __init__(self, settings: BaseInfraSettings):
        self.settings = settings
        self._engines: Dict[str, Any] = {}
        self._is_async: Dict[str, bool] = {}
        self._lock = asyncio.Lock()

    def _validate_url(self, url: str):
        if not url:
            raise DatabaseConfigurationError("DATABASE_URL is missing or empty.")
        if "://" not in url:
            raise DatabaseConfigurationError(f"Malformed database URL: '{url}'. Missing protocol.")

    def is_async_url(self, url: str) -> bool:
        if "libsql" in url: return False
        if url.startswith("sqlite") and "aiosqlite" not in url: return False
        return True

    async def get_engine(self, url: Optional[str] = None, **kwargs) -> Any:
        target_url = url or self.settings.DATABASE_URL
        self._validate_url(target_url)

        if target_url in self._engines:
            return self._engines[target_url]

        async with self._lock:
            if target_url in self._engines:
                return self._engines[target_url]

            is_async = self.is_async_url(target_url)
            self._is_async[target_url] = is_async

            engine_kwargs = {
                "pool_pre_ping": kwargs.get("pool_pre_ping", True),
                "pool_recycle": kwargs.get("pool_recycle", 300),
                "connect_args": kwargs.get("connect_args", {}),
                "pool_timeout": kwargs.get("pool_timeout", 60),
                "connect_timeout": kwargs.get("connect_timeout", 30)
            }

            if "mysql" in target_url or "tidb" in target_url:
                if self.settings.DB_SSL or "tidb" in target_url:
                    ca_path = self.settings.DB_SSL_CA
                    if not ca_path:
                        import os
                        import certifi
                        ca_path = certifi.where()
                        for path in ["/etc/ssl/certs/ca-certificates.crt", "/etc/ssl/cert.pem"]:
                            if os.path.exists(path):
                                ca_path = path
                                break
                    if ca_path:
                        import ssl
                        engine_kwargs["connect_args"]["ssl"] = ssl.create_default_context(cafile=ca_path)
                        engine_kwargs["connect_args"]["ssl"].check_hostname = False
                    else:
                        engine_kwargs["connect_args"]["ssl"] = True

            if "sqlite" in target_url or "libsql" in target_url:
                engine_kwargs["poolclass"] = QueuePool
                engine_kwargs["pool_size"] = kwargs.get("pool_size", 10)
                engine_kwargs["max_overflow"] = kwargs.get("max_overflow", 5)

                if "check_same_thread" not in engine_kwargs["connect_args"]:
                    engine_kwargs["connect_args"]["check_same_thread"] = False
            else:
                engine_kwargs["pool_size"] = kwargs.get("pool_size", self.settings.DB_POOL_SIZE)
                engine_kwargs["max_overflow"] = kwargs.get("max_overflow", 10)

            if "creator" in kwargs:
                engine_kwargs["creator"] = kwargs["creator"]
                engine_kwargs.pop("connect_args", None)

            try:
                sqlalchemy_url = target_url
                if not is_async and ("libsql" in target_url or ".turso.io" in target_url):
                    sqlalchemy_url = "sqlite:///libsql_connection"

                if is_async:
                    engine = create_async_engine(sqlalchemy_url, **engine_kwargs)
                else:
                    engine = create_engine(sqlalchemy_url, **engine_kwargs)

                self._engines[target_url] = engine
                logger.info(f"[DatabaseFactory] Engine created ({'Async' if is_async else 'Sync'}) for {target_url.split('@')[-1] if '@' in target_url else 'local db'}")
                return engine
            except Exception as e:
                raise DatabaseConfigurationError(f"Failed to create engine for {target_url}", details=str(e))

    async def check_health(self, url: Optional[str] = None) -> bool:
        try:
            target_url = url or self.settings.DATABASE_URL
            engine = await self.get_engine(target_url)
            is_async = self._is_async.get(target_url, True)

            if is_async:
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
            else:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"[DatabaseFactory] Health check failed for {url or 'default'}: {e}")
            return False

    async def get_raw_pool(self, url: Optional[str] = None, **kwargs) -> Any:
        target_url = url or self.settings.DATABASE_URL
        self._validate_url(target_url)
        from urllib.parse import urlparse
        parsed = urlparse(target_url.replace("tidb://", "mysql://").replace("+aiomysql", "").replace("+asyncpg", ""))

        driver = ""
        if "mysql" in target_url or "mariadb" in target_url: driver = "mysql"
        elif "postgres" in target_url or "pgsql" in target_url: driver = "pgsql"
        elif "libsql" in target_url or ".turso.io" in target_url: driver = "libsql"
        elif "sqlite" in target_url: driver = "sqlite"

        try:
            if driver == "mysql":
                import aiomysql
                import ssl
                import os
                db_name = parsed.path.lstrip('/')
                ssl_ctx = None
                if self.settings.DB_SSL or "tidb" in target_url:
                    ssl_ctx = ssl.create_default_context()
                    ca_path = self.settings.DB_SSL_CA
                    if not ca_path:
                        import certifi
                        ca_path = certifi.where()
                        for path in ["/etc/ssl/certs/ca-certificates.crt", "/etc/ssl/cert.pem"]:
                            if os.path.exists(path):
                                ca_path = path
                                break
                    if ca_path:
                        ssl_ctx.load_verify_locations(ca_path)
                    else:
                        ssl_ctx.check_hostname = False

                if db_name:
                    try:
                        conn_args = {
                            "host": parsed.hostname,
                            "user": parsed.username,
                            "password": parsed.password,
                            "port": parsed.port or 4000,
                            "autocommit": True,
                            "charset": "utf8mb4",
                            "ssl": ssl_ctx,
                            "connect_timeout": 30
                        }
                        try:
                            test_conn = await aiomysql.connect(db=db_name, **conn_args)
                            test_conn.close()
                        except Exception:
                            for sys_db in ["test", "mysql", None]:
                                try:
                                    logger.info(f"[DatabaseFactory] Attempting to create database '{db_name}' via '{sys_db or 'ROOT'}'...")
                                    tmp_conn = await aiomysql.connect(db=sys_db, **conn_args)
                                    async with tmp_conn.cursor() as cur:
                                        await cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
                                    tmp_conn.close()
                                    break
                                except: continue
                    except Exception as db_err:
                        logger.warning(f"[DatabaseFactory] DB discovery warning: {db_err}")

                cfg = {
                    "host": parsed.hostname,
                    "user": parsed.username,
                    "password": parsed.password,
                    "port": parsed.port or 3306,
                    "db": db_name,
                    "autocommit": True,
                    "charset": "utf8mb4",
                    "minsize": 2,
                    "maxsize": kwargs.get("maxsize", self.settings.DB_POOL_SIZE),
                    "pool_recycle": 1800,
                    "ssl": ssl_ctx,
                    "connect_timeout": 30
                }
                return await aiomysql.create_pool(**cfg)

            elif driver == "pgsql":
                import asyncpg
                return await asyncpg.create_pool(target_url, min_size=5, max_size=kwargs.get("maxsize", 50))
            elif driver == "sqlite":
                import aiosqlite
                path = parsed.path.lstrip('/') or "suite.sqlite"
                conn = await aiosqlite.connect(path, timeout=30, check_same_thread=False)
                conn.row_factory = aiosqlite.Row
                return conn
            elif driver == "libsql":
                import libsql_client
                token = getattr(self.settings, "DB_AUTH_TOKEN", None)
                return libsql_client.create_client(target_url, auth_token=token)
            raise DatabaseConfigurationError(f"Unsupported raw driver for URL: {target_url}")
        except Exception as e:
            raise DatabaseConfigurationError(f"Failed to create raw pool for {target_url}", details=str(e))

    async def close_all(self):
        async with self._lock:
            for url, engine in self._engines.items():
                if self._is_async.get(url, True):
                    if hasattr(engine, "dispose"): await engine.dispose()
                else:
                    if hasattr(engine, "dispose"): engine.dispose()
            self._engines.clear()
            self._is_async.clear()
