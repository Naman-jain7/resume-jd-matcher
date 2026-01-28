from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.matcher import matcher_router

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="Resume JD Matcher")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(matcher_router)

# app.mount("/static", StaticFiles(directory = BASE_DIR / "frontend"), name="static")


# @app.get("/")
# def serve_frontend():
#     return FileResponse(BASE_DIR / "frontend" / "index.html")