from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.matcher import router as match_router
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

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

app.mount("/static", StaticFiles(directory = BASE_DIR / "frontend"), name="static")


@app.get("/")
def serve_frontend():
    return FileResponse(BASE_DIR / "frontend" / "index.html")