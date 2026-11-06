"""Application factory. Importing this module has no database side effects."""
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .config import Settings
from .errors import DomainError
from .database import Database
from .api import router


def create_app(settings: Settings | None = None):
    settings = settings or Settings.from_env()
    app = FastAPI(title="PigPen API", version="1.0.0")
    app.state.settings = settings
    app.state.database = Database(settings)

    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        return JSONResponse(exc.body(), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        # Pydantic's default input field can contain financials or push secrets.
        details = [{"loc": e["loc"], "type": e["type"], "message": e["msg"]} for e in exc.errors()]
        return JSONResponse({"error": {"code": "validation", "message": "Invalid request", "details": details}}, status_code=422)

    @app.get("/api/v1/health")
    def health():
        ready = app.state.database.ready()
        return JSONResponse({"status": "ok" if ready else "not_ready"}, status_code=200 if ready else 503)

    app.include_router(router(app.state.database))
    return app
