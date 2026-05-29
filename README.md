# SELA Website

Standalone website project for Sela Construction, LLC.

## Run locally

1. Create a virtual environment.
2. Install the project dependencies.
3. Start the app.

Example:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python app.py
```

The site runs on `http://127.0.0.1:5101` by default.

## Environment

Copy `.env.example` to `.env` and fill in any values you need.

`GOOGLE_PLACES_API_KEY`
: Enables the live 5-star Google Places review feed.

`SELA_GOOGLE_PLACE_QUERY`
: Text query used to resolve the Google Places listing.

`SELA_GOOGLE_PLACE_ID`
: Optional explicit Google Place ID to avoid query ambiguity.

`SELA_HOST`, `SELA_PORT`, `SELA_DEBUG`
: Local development server settings.