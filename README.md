# Online-Judge-System(Project 2)
Project Homework II for the Python course in Summer semester

Minimal Online Judge built with FastAPI.

## Setup

```bash
cd project2
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://127.0.0.1:8000/ and http://127.0.0.1:8000/docs

Default admin (created in Stage C): `admin` / `admin123456`

## Persistence

JSON files under `data/` (atomic writes). Temp judge files under `temp/`.

## Tests

```bash
pytest -q
```

## Structure

See `app/` for backend layers: routers → services → repositories / judge.
