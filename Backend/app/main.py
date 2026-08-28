import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import (
    auth_router,
    materials_router,
    quiz_router,
    dashboard_router,
    recommendations_router
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("skillsetu.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Event Handler.
    Handles startup (DB connection & index/catalog seeding) and shutdown cleanup.
    """
    logger.info("Initializing SkillSetu Backend Application...")
    await connect_to_mongo()
    yield
    logger.info("Shutting down SkillSetu Backend Application...")
    await close_mongo_connection()

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for MoSPI AI-Enabled Competency Gap Learning Platform (SIH26101)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware for Frontend React integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local dev React server on port 5173 / 3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router.router)
app.include_router(materials_router.router)
app.include_router(quiz_router.router)
app.include_router(dashboard_router.router)
app.include_router(recommendations_router.router)

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "skillsetu-backend"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred.", "error": str(exc)}
    )
