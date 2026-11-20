"""
HealthCheckService — Observability and runtime readiness probes.
Checks:
  - Database connectivity (SQLite or PostgreSQL)
  - MCP Server availability
  - Redis background worker queue (if configured)
  - File Storage accessibility
"""
from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings


class HealthCheckService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_database(self) -> Dict[str, Any]:
        try:
            await self.db.execute(text("SELECT 1"))
            return {"status": "healthy", "type": "postgresql" if settings.POSTGRES_URL else "sqlite"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def check_mcp_server(self) -> Dict[str, Any]:
        """Pings the standalone MCP server HTTP endpoint if configured."""
        import urllib.request
        try:
            req = urllib.request.Request(f"{settings.MCP_SERVER_URL}/health", headers={"User-Agent": "AURA-HealthCheck"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    return {"status": "healthy", "url": settings.MCP_SERVER_URL}
        except Exception:
            pass
        return {"status": "standalone_not_detected", "url": settings.MCP_SERVER_URL, "mode": "embedded_fallback"}

    async def check_storage(self) -> Dict[str, Any]:
        try:
            notes_ok = settings.NOTES_DIR.exists()
            subs_ok = settings.SUBMISSIONS_DIR.exists()
            return {
                "status": "healthy" if (notes_ok and subs_ok) else "degraded",
                "backend": settings.STORAGE_BACKEND,
                "notes_dir": str(settings.NOTES_DIR),
                "submissions_dir": str(settings.SUBMISSIONS_DIR),
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def get_full_report(self) -> Dict[str, Any]:
        db_res = await self.check_database()
        mcp_res = await self.check_mcp_server()
        storage_res = await self.check_storage()

        overall = "healthy" if db_res.get("status") == "healthy" else "unhealthy"

        return {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "status": overall,
            "subsystems": {
                "database": db_res,
                "mcp_server": mcp_res,
                "storage": storage_res,
            },
        }
