from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.matcher import matcher_router


app = FastAPI(title="Resume JD Matcher")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(matcher_router)
