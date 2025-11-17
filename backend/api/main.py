"""FastAPI application for clinical decision support system."""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .dependencies import cleanup_kg_service, get_kg_service
from .routes import scenarios, workflow, knowledge_graph, rag, variants

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:     %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks."""
    logger.info("=" * 80)
    logger.info("🚀 Starting Clinical Decision Support API")
    logger.info("=" * 80)

    # Check environment variables
    logger.info("🔧 Environment Configuration:")
    logger.info(f"   NEO4J_URI: {os.getenv('NEO4J_URI', 'NOT SET')}")
    logger.info(f"   NEO4J_USER: {os.getenv('NEO4J_USER', 'NOT SET')}")
    logger.info(f"   NEO4J_PASSWORD: {'***' if os.getenv('NEO4J_PASSWORD') else 'NOT SET'}")
    logger.info(f"   NEO4J_DATABASE: {os.getenv('NEO4J_DATABASE', 'NOT SET')}")
    logger.info(f"   ENABLE_CLINVAR: {os.getenv('ENABLE_CLINVAR', 'false')}")
    logger.info(f"   NCBI_API_KEY: {'***' if os.getenv('NCBI_API_KEY') else 'NOT SET'}")

    # Startup: Initialize knowledge graph service
    kg_service = get_kg_service()

    # Log data source information
    info = kg_service.get_data_source_info()
    logger.info("")
    logger.info("📊 Data Source Status:")
    logger.info(f"   Neo4j Connected: {info['neo4j_connected']}")
    logger.info(f"   Monarch Service: {info['monarch_service']}")
    logger.info(f"   In-Memory Store: {info['in_memory_store']}")
    logger.info(f"   Database Type: {info['database_type']}")
    logger.info(f"   Active Source: {info['active_source']}")
    if info.get('database_labels'):
        logger.info(f"   Database Labels (first 10): {', '.join(info['database_labels'][:10])}")
    logger.info("=" * 80)

    yield

    # Shutdown: Clean up connections
    logger.info("🛑 Shutting down Clinical Decision Support API")
    cleanup_kg_service()


# Create FastAPI application
app = FastAPI(
    title="Clinical Decision Support API",
    description="Knowledge graph-driven clinical decision support system for rare muscular dystrophies",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scenarios.router, prefix="/api", tags=["scenarios"])
app.include_router(workflow.router, prefix="/api", tags=["workflow"])
app.include_router(knowledge_graph.router, prefix="/api", tags=["knowledge-graph"])
app.include_router(rag.router, prefix="/api", tags=["rag"])
app.include_router(variants.router, prefix="/api", tags=["variants"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    kg_service = get_kg_service()
    data_source = kg_service.get_data_source_info()
    return {
        "status": "healthy",
        "service": "Clinical Decision Support API",
        "data_source": data_source,
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Clinical Decision Support API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
