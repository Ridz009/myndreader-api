from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import Base
from .routes import books, users, recommendations

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MyndReader API",
    description="A personalized book recommendation API with comfort level controls",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(books.router)
app.include_router(users.router)
app.include_router(recommendations.router)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to MyndReader API!",
        "description": "A personalized book recommendation system with comfort level controls",
        "features": [
            "Personalized recommendations based on reading history",
            "Comfort level control (same old to completely new)",
            "Book and user management",
            "Reading progress tracking",
            "Genre and author filtering"
        ],
        "comfort_levels": [
            "same_old - Very similar to your previous reads",
            "comfort_zone - Somewhat similar with gentle variety",
            "balanced - Mix of familiar and new",
            "adventurous - Venturing into new territory",
            "completely_new - Completely different experiences"
        ],
        "endpoints": {
            "books": "/books - Book management and search",
            "users": "/users - User management and preferences",
            "recommendations": "/recommendations - Personalized recommendations"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "MyndReader API"}

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
