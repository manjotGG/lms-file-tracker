from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import files, auth
import database
import models

# Create all tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="LMS File Version Management", version="1.0.0")

# CORS middleware for frontend connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(files.router, prefix="/files", tags=["Files"])

@app.get("/")
def home():
    return {
        "message": "LMS File Version Management System",
        "status": "running",
        "version": "1.0.0"
    }
