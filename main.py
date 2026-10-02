from pathlib import Path
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from proyecto2 import match_project_with_metrics

app = FastAPI(title="Project Name Matcher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MatchRequest(BaseModel):
    dirty_name: str
    known_projects: list[str]
    threshold: float = Field(default=80.0, ge=0.0, le=100.0)


class MatchResponse(BaseModel):
    best_match: str | None
    confidence_score: float
    metrics: dict[str, float] | None
    candidates: list[dict[str, object]]


@app.post("/api/match", response_model=MatchResponse)
def match_project_endpoint(request: MatchRequest) -> MatchResponse:
    best_match, confidence_score, metrics, candidates = match_project_with_metrics(
        request.dirty_name,
        request.known_projects,
        threshold=request.threshold,
    )
    return MatchResponse(
        best_match=best_match,
        confidence_score=confidence_score,
        metrics=metrics,
        candidates=candidates,
    )


frontend_directory = Path(__file__).parent / "dist"
if os.path.isdir(frontend_directory):
    app.mount("/", StaticFiles(directory=frontend_directory, html=True), name="frontend")
