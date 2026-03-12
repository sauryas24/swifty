from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from . import models
from .database import engine
from .routers import venues, auth, finances
import os


# Create the database tables automatically when the server starts
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Swifty API", version="1.0")

# Mount static files to serve receipt images/PDFs
if not os.path.exists("static/receipts"):
    os.makedirs("static/receipts")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Plug the routers into the main app
app.include_router(venues.router)
app.include_router(auth.router)
app.include_router(finances.router)

@app.get("/")
def root():
    return {"message": "Swifty Backend is running!"}