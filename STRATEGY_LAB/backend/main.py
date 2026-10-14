"""
NIFTY Strategy Lab — FastAPI Backend
Serves the React dashboard with strategy data, backtest execution, and analytics.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import CORS_ORIGINS, API_HOST, API_PORT
from .api.strategies import router as strategies_router
from .api.results import router as results_router
from .api.data import router as data_router
from .api.agents import router as agents_router
from .results.store import init_db

# Initialize database
init_db()

app = FastAPI(
    title="NIFTY Strategy Lab",
    description="Multi-strategy options backtesting platform",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(strategies_router, prefix="/api")
app.include_router(results_router, prefix="/api")
app.include_router(data_router, prefix="/api")
app.include_router(agents_router, prefix="/api")

# Serve frontend static files in production
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "NIFTY Strategy Lab"}


def start():
    """Entry point for running the server."""
    import uvicorn
    uvicorn.run(
        "STRATEGY_LAB.backend.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
    )


if __name__ == "__main__":
    start()
