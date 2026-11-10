"""Application factory. Importing this module has no database side effects."""
from contextlib import asynccontextmanager
from threading import Event, Thread
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .config import Settings
from .errors import DomainError
from .database import Database
from .api import router
from sqlalchemy.exc import OperationalError


def create_app(settings: Settings | None = None):
    settings = settings or Settings.from_env()
    @asynccontextmanager
    async def lifespan(app):
        stop=Event()
        worker=None
        if settings.environment != 'test':
            from .receipt_worker import loop
            worker=Thread(target=loop,args=(app.state.database,stop),daemon=True)
            worker.start()
        yield
        stop.set()
        if worker:
            import asyncio
            await asyncio.to_thread(worker.join,50)
    app = FastAPI(title="PigPen API", version="1.0.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.database = Database(settings)

    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        return JSONResponse(exc.body(), status_code=exc.status)

    @app.exception_handler(OperationalError)
    async def storage_error(request, exc):
        return JSONResponse(DomainError('storage_unavailable', 'Storage unavailable; verify migrations and retry', 503).body(), status_code=503)

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
    if settings.static_dir:
        from .static import AppFiles
        app.mount('/', AppFiles(directory=settings.static_dir, html=True))
    return app
