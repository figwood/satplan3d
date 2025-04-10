from fastapi import FastAPI
from .database import engine
from . import models
from .routers import auth, satellites, tracks, coverage

# Configure logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SatPlan3D API",
    description="提供用户认证、权限管理以及卫星轨道计算功能的 API 文档。",
    version="1.0.0",
)

# Register routers
app.include_router(auth.router, tags=["Authentication"])  # Removed prefix
app.include_router(satellites.router, prefix="/api", tags=["satellites"])
app.include_router(tracks.router, prefix="/api", tags=["tracks"])
app.include_router(coverage.router, prefix="/api", tags=["coverage"])

@app.get("/api")
def read_root():
    return {"message": "Hello, World!"}

# Create tables
models.Base.metadata.create_all(bind=engine)