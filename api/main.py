from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time

from api.routers import images, tasks

app = FastAPI(
    title="Poster Maker API",
    description="Backend API for Poster Maker application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],  # Explicitly allow frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(images.router)
app.include_router(tasks.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok", 
        "message": "Poster Maker API is running",
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    # Use the string reference "api.main:app" for reload support
    # But when running normally, we can pass the app object
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
