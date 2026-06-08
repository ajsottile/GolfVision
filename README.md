# Golf Swing Analysis POC

This project compares a user golf swing video against a professional reference
video and generates synchronized playback plus coaching recommendations.

## Features

- YOLO pose inference with `ultralytics`
- Keypoint and video tooling via `supervision`
- Swing phase detection (address, takeaway, top, impact, follow-through)
- Phase-aware alignment with dynamic time warping (DTW)
- Rule-based coaching tips from metric deviations
- Streamlit interface for upload + comparison workflow

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (requires at least one pro clip in `data/pros/`).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app** → select this repo, branch `main`, main file `app.py`.
4. In **Advanced settings → Secrets**, add:

```toml
OPENAI_API_KEY = "your_api_key_here"
OPENAI_MODEL = "gpt-4o-mini"
```

5. Deploy. The first run may take a few minutes while dependencies install and
   YOLO downloads model weights.

6. **Important:** In Streamlit Cloud **Advanced settings**, set **Python version
   to 3.12 or 3.11** (not 3.14). OpenCV and YOLO do not reliably support 3.14
   on Community Cloud yet. If your app is already deployed, change this under
   **Manage app → Settings → Python version**, then reboot.

**Note:** Streamlit Community Cloud free tier deploys from **public** GitHub repos.
Pro reference clips must be committed under `data/pros/` (or the app will show a
setup warning). Generated outputs are not persisted between sessions.

## OpenAI setup (optional, recommended)

To enable AI-generated recommendations and tailored practice plans:

```bash
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_MODEL="gpt-4o-mini"  # optional override
```

If `OPENAI_API_KEY` is not set (or the API call fails), the app automatically
falls back to a deterministic rule-based coaching plan.

## Data layout

- Place professional reference clips in `data/pros/`
- Upload your swing video through the Streamlit UI
- Outputs are written to `outputs/`

## Notes

- This POC is body-pose-only (no club/ball tracking yet)
- Down-the-line view is implemented first
- Face-on support is stubbed in the view profile system
- AI coaching plans use OpenAI when configured, with rule-based fallback
