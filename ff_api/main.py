import uvicorn
import argparse
from fastapi import FastAPI
from contextlib import asynccontextmanager

from ff_api.config.settings import settings
from ff_api.api.routes import router
from ff_api.api.middleware import RequestIDMiddleware, RateLimitMiddleware, error_handler_middleware
from ff_api.core.transport import transport

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print(f"🚀 FF-API v3.0 starting for {settings.OB_VERSION}")
    yield
    # Shutdown logic
    await transport.close()
    print("👋 FF-API shutdown gracefully")

app = FastAPI(
    title="Free Fire UID Verification API — APEX v3.0",
    description="Multi-region Free Fire player data fetcher",
    version="3.0.0",
    lifespan=lifespan
)

# Add Middlewares
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware, rpm=settings.RATE_LIMIT_RPM)
app.middleware("http")(error_handler_middleware)

# Add Routes
app.include_router(router)

def start_server(port: int):
    uvicorn.run(app, host="0.0.0.0", port=port, log_level=settings.LOG_LEVEL.lower())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FF-API v3.0")
    parser.add_argument("--serve", action="store_true", help="Start FastAPI web server")
    parser.add_argument("--port", type=int, default=settings.SERVER_PORT, help="Port to run the server on")

    args = parser.parse_args()

    if args.serve:
        start_server(args.port)
    else:
        print("Use --serve to start the API server, or use cli.py for command line interface.")
