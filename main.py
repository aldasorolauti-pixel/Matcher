from pathlib import Path

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


@app.post("/api/match", response_model=MatchResponse)
def match_project_endpoint(request: MatchRequest) -> MatchResponse:
    best_match, confidence_score, metrics = match_project_with_metrics(
        request.dirty_name,
        request.known_projects,
        threshold=request.threshold,
    )
    return MatchResponse(
        best_match=best_match,
        confidence_score=confidence_score,
        metrics=metrics,
    )


frontend_directory = Path(__file__).parent / "dist"
app.mount("/", StaticFiles(directory=frontend_directory, html=True), name="frontend")
