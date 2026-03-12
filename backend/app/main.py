from fastapi import FastAPI
from . import models
from .database import engine

# Import your routers
from .routers import venues
from .routers import auth
from .routers import announcements
from .routers import approvals
from .routers import requests
from .routers import finances
from .routers import permission


# Create the database tables automatically when the server starts
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Swifty API", version="1.0")

# Plug the routers into the main app
app.include_router(venues.router)
app.include_router(auth.router)
# app.include_router(announcements.router)
# app.include_router(approvals.router)
# app.include_router(requests.router)
# app.include_router(finances.router)
# app.include_router(permission.router)


@app.get("/")
def root():
    return {"message": "Swifty Backend is running!"}