from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from . import models
from .database import engine
from .routers import venues, auth, finances
import os
from fastapi.middleware.cors import CORSMiddleware
# Import your routers
from .routers import venues
from .routers import auth
from .routers import announcements
from .routers import approvals
from .routers import requests
from .routers import finances
from .routers import permission
from .routers import MoU
from .routers import calendar # Add this to your imports
# from .routers import otp


# Add this below your existing app.include_router() calls
# Create the database tables automatically when the server starts
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Swifty API", version="1.0")
# Mount static files to serve receipt images/PDFs
if not os.path.exists("static/receipts"):
    os.makedirs("static/receipts")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Plug the routers into the main app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow your Live Server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Plug the routers into the main app
app.include_router(venues.router)
app.include_router(auth.router)

app.include_router(finances.router)
app.include_router(announcements.router)

app.include_router(MoU.router)
app.include_router(approvals.router)
app.include_router(requests.router)
app.include_router(finances.router)
app.include_router(permission.router)
# app.include_router(otp.router)

app.include_router(calendar.router)

@app.get("/")
def root():
    return {"message": "Swifty Backend is running!"}