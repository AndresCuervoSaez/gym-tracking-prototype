# Gym MVP Local Prototype

Runnable local prototype (CPU-only) with mocked detector/tracker/VLM but production-like data flow:
`edge_service -> backend_api (SQLite + media) -> mm_worker -> ui`.

## Components
- `edge_service`: reads a local MP4, runs mock CV and rule engine, exports clips, posts events with retry + outbox.
- `backend_api`: FastAPI ingestion + event/media query API backed by SQLite.
- `mm_worker`: polls pending multimodal events and fills mock VLM output.
- `ui`: Streamlit dashboard to browse events and play clips.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r gym-mvp-local/requirements.txt
mkdir -p gym-mvp-local/data/media
```

## Run (4 terminals)

### Terminal 1 — Backend
```bash
source .venv/bin/activate
python gym-mvp-local/backend_api/main.py --db ./gym-mvp-local/data/app.db --media-dir ./gym-mvp-local/data/media
```

### Terminal 2 — MM worker
```bash
source .venv/bin/activate
python gym-mvp-local/mm_worker/worker.py --db ./gym-mvp-local/data/app.db --seed 123
```

### Terminal 3 — UI
```bash
source .venv/bin/activate
streamlit run gym-mvp-local/ui/app.py
```

### Terminal 4 — Edge service
```bash
source .venv/bin/activate
python gym-mvp-local/edge_service/main.py --video ./sample.mp4 --camera-id cam_01 --store-id gym_demo --seed 42
```

## What this prototype demonstrates
- Real-time-ish frame loop from a local video file.
- Deterministic mock detections/tracks with gym-specific event transitions:
  - `MACHINE_OCCUPIED_START`
  - `MACHINE_OCCUPIED_END`
  - `CLEANING_WINDOW_OPEN`
  - `CLEANING_ATTEMPT` (with `needs_mm=true`)
- Event clip export around timestamps to `gym-mvp-local/data/media/<event_id>.mp4`.
- Resilient delivery via retries + JSONL outbox flush when backend recovers.
- Backend idempotency using unique `event_id`.
- Worker enrichment from `PENDING` to `DONE` with mock multimodal outputs.
- Streamlit list/detail UI including embedded video playback from `/media/{event_id}`.

## Notes
- Config is in `gym-mvp-local/edge_service/config.yaml`.
- DB path: `./gym-mvp-local/data/app.db`
- Media path: `./gym-mvp-local/data/media`
