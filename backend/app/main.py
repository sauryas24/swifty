from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from . import models
from .database import engine
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
from .routers import calendar
from .routers import otp
from .routers import clubs  # <--- Added new clubs router

# Initialize database schemas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Swifty API", version="1.0")

# Configure directories for images/PDFs and MoU documents
if not os.path.exists("static/receipts"):
    os.makedirs("static/receipts")
if not os.path.exists("static/mou_documents"):      
    os.makedirs("static/mou_documents")               

app.mount("/static", StaticFiles(directory="static"), name="static")


# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://swifty-tau.vercel.app",  
        "http://localhost:5500",          
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,               
    allow_methods=["*"],
    allow_headers=["*"],
)

# Plug the routers into the main app
app.include_router(venues.router)
app.include_router(auth.router)
app.include_router(announcements.router)
app.include_router(finances.router)
app.include_router(MoU.router)
app.include_router(approvals.router)
app.include_router(requests.router)
app.include_router(permission.router)
app.include_router(otp.router)
app.include_router(calendar.router)
app.include_router(clubs.router)  

@app.get("/")
def root():
    return {"message": "Swifty Backend is running!"}