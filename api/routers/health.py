from fastapi import APIRouter

from api.dependencies import SettingsDep
from api.schemas import HealthResponse

router = APIRouter(tags=["System"])


@router.get("/health")
def health_check(settings: SettingsDep) -> HealthResponse:
    """Return service liveness and runtime environment metadata."""
    return HealthResponse(status="ok", app=settings.APP_NAME, environment=settings.APP_ENV)
