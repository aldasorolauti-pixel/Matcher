# Project Name Matcher

A deterministic project-name matcher for reconciling inconsistent names across systems. It compares an incoming name with a list of official project names and returns the strongest match and a confidence score. It returns no match when the score is below the threshold, critical identifiers conflict, or multiple candidates are too close to call.

Example:

```text
2460 North Australian  ->  2460 N Australian Ave
```

The project includes a Python matching module, a FastAPI service, and a React frontend. The matcher itself uses only the Python standard library.

## Features

- Expands common street and direction abbreviations such as `N`, `Ave`, and `Blvd`.
- Ignores selected noise words while calculating the similarity score.
- Rejects candidates with conflicting numbers, phase/tower/building identifiers, or opposite cardinal directions.
- Rejects low-confidence and ambiguous matches instead of always choosing a candidate.
- Returns a metric breakdown that drives the frontend's match-analysis bars.

## Project Structure

| File or directory | Purpose |
| --- | --- |
| `proyecto2.py` | Matching algorithm and metrics. |
| `main.py` | FastAPI endpoint and production static-file serving. |
| `test_proyecto2.py` | Unit and regression tests for the active matcher. |
| `src/App.jsx` | React UI and the UI's built-in project catalog. |
| `src/index.css` | Frontend styles. |
| `package.json` | Frontend dependencies and npm scripts. |
| `package-lock.json` | Locked npm dependency versions. |
| `vite.config.js` | Vite, React, and Tailwind configuration. |

The UI's initial catalog is `INITIAL_PROJECTS` in `src/App.jsx`. The API does not read that constant directly: the frontend sends its project list in each request.

## Requirements

- Python 3.10 or newer.
- Node.js and npm compatible with Vite 7.
- Python packages: FastAPI and Uvicorn.
- Frontend packages are declared in `package.json` and locked in `package-lock.json`.

## Installation

Install the frontend dependencies from the project root:

```bash
npm ci
```

Install the Python service dependencies:

```bash
python -m pip install fastapi uvicorn
```

Use `python3` instead of `python` on systems where that is the Python 3 command.

## Run in Development

The Vite frontend calls the API at `http://127.0.0.1:8000/api/match`. Run the backend and frontend in separate terminals from the project root.

Terminal 1, start FastAPI:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Terminal 2, start Vite:

```bash
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

## Build and Run as a Single Service

FastAPI serves the compiled frontend from `dist/`, so build it before starting the backend:

```bash
npm run build
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000`. The API is available at the same origin under `/api/match`.

## Run Tests

Run the tests for the matcher used by the application:

```bash
python -m unittest test_proyecto2 -v
```

The suite covers abbreviation and name matching, 20 expected matches, 20 rejected near-misses, critical identifier conflicts, the confidence threshold, ambiguous candidates, and returned metrics.

## API

### `POST /api/match`

Request:

```json
{
  "dirty_name": "2460 North Australian",
  "known_projects": [
    "2460 N Australian Ave",
    "500 Broadway"
  ],
  "threshold": 80.0
}
```

`threshold` is optional and defaults to `80.0`; valid values are from `0` to `100`.

Response:

```json
{
  "best_match": "2460 N Australian Ave",
  "confidence_score": 83.57,
  "metrics": {
    "normalization": 85.71,
    "word_overlap": 75.0,
    "text_similarity": 85.71,
    "identifier_compatibility": 100.0,
    "noise_retention": 100.0
  }
}
```

`best_match` is `null` when the matcher declines to select a project. `confidence_score` is the best eligible candidate's score (or `0.0` when there is no eligible candidate). `metrics` describes the top-scoring comparison and can be `null` when there is no usable input or candidate.

The scoring formula is:

```text
score = (0.8 * text_similarity + 0.2 * word_overlap) * 100
```

The score is rounded to two decimal places. A candidate is rejected if it falls below the threshold. By default, if a second distinct candidate also clears the threshold and is less than 5 points behind the best score, the result is considered ambiguous and no match is returned.

The metrics are:

| Metric | Meaning |
| --- | --- |
| `normalization` | Text similarity after lowercasing, punctuation cleanup, and abbreviation expansion, before noise removal. |
| `word_overlap` | Jaccard overlap of the two sets of noise-filtered words. |
| `text_similarity` | `difflib.SequenceMatcher` similarity of the noise-filtered strings. |
| `identifier_compatibility` | `100` when no hard identifier conflict is found, otherwise `0`. |
| `noise_retention` | Percentage of combined tokens retained after noise-word removal. |

Only `word_overlap` and `text_similarity` contribute to the confidence score. The other metrics are diagnostic.

## Python Usage

```python
from proyecto2 import match_project, match_project_with_metrics

match_project("2460 North Australian", ["2460 N Australian Ave"])
# ("2460 N Australian Ave", 83.57)

match_project_with_metrics(
    "2460 North Australian",
    ["2460 N Australian Ave"],
    threshold=80.0,
    ambiguity_margin=5.0,
)
# (best_match, confidence_score, metrics)
```

## Current Matching Rules and Limitations

- Abbreviations are limited to the mappings declared in `ABREVIATURAS` in `proyecto2.py`.
- Noise words (`addition`, `construction`, `project`, and `renovation`) are removed before scoring. Consequently, differences consisting only of these words do not distinguish project scopes.
- Critical identifier checks compare sets of standalone numbers, phase/tower/building labels, and selected opposite direction pairs. They are intentionally conservative and can reject valid comparisons when unrelated numbers appear in the two names.
- The score and default threshold are heuristic, not calibrated against a production-labeled dataset. Validate them on representative project names before relying on the result for financial or operational decisions.
- CORS currently allows requests from any origin. Restrict allowed origins before exposing the service outside a trusted local environment.

## License

No license is currently specified. Add a license before redistributing this project publicly.