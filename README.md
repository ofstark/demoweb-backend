# FloodGuard AI — Backend (Tier 1)

A FastAPI backend that computes flash-flood risk using a documented,
explainable **weighted-scoring model** over live, free, keyless public
data sources. No trained ML model yet — see "Upgrading to Tier 2" below
for the path to one.

## 1. What this does

For each monitored location it:

1. Fetches last-6h rainfall and trend from **Open-Meteo** (forecast API)
2. Fetches near-surface soil moisture from **Open-Meteo** (soil moisture variable)
3. Fetches river discharge and its rate of change from the **Open-Meteo Flood API**
4. Fetches a terrain-steepness proxy from **Open-Elevation**
5. Normalizes each signal to 0–1 and combines them with fixed weights
   (see `app/services/scoring.py`) into a 0–100 flood probability and
   a LOW/MODERATE/HIGH/CRITICAL classification
6. Returns it in the exact shape the FloodGuard AI frontend expects

No API keys are required for any of these services.

## 2. Setup

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # adjust CORS origin if your frontend runs elsewhere
```

### Set Astra's login password

There's a single operator account — username `Astra`. Set your own
password (never committed in plaintext):

```bash
python scripts/generate_hash.py "your-chosen-password"
```

Copy the printed hash into `.env` as `ASTRA_PASSWORD_HASH`.

Then generate a random JWT signing secret:

```bash
python scripts/generate_jwt_secret.py
```

Copy that into `.env` as `JWT_SECRET_KEY`. Without both of these set, login
will always fail (by design — there's no default password).

## 3. Run

```bash
./run.sh
# or directly:
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive Swagger docs.

## 4. Connect the frontend

In the frontend project, create `.env`:

```
VITE_API_BASE_URL=http://localhost:8000/api
```

Then in `src/services/api.ts`, flip:

```ts
export const USE_MOCK_DATA = false;
```

The response shapes in `app/models/schemas.py` are written to match
`src/types/index.ts` field-for-field, so no frontend component changes
are needed.

## 5. Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/login` | `{username, password}` → JWT access token |
| GET | `/api/auth/me` | Returns the current authenticated username |
| GET | `/api/predictions` | Live prediction for every configured zone |
| POST | `/api/predict` | On-demand prediction for an arbitrary `{latitude, longitude}` |
| GET | `/api/locations` | Zones enriched with current risk (for the GIS map) |
| GET | `/api/risk-map` | Same as `/locations` — kept separate so it can diverge later |
| GET | `/api/alerts` | Alerts derived live from zones currently at MODERATE+ risk |
| GET | `/api/geography` | Static basin geometry — river course(s), roads, settlements, map center |

All routes except `/api/auth/login` require an `Authorization: Bearer <token>`
header. The frontend's auth service handles attaching this automatically
once you're logged in.

## 6. Where to edit things

- **Monitoring locations**: `app/data/zones.py` — replace with your real
  region's coordinates.
- **Basin geometry** (river course, roads, settlements): `app/data/geography.py`
  — this is now the single source of truth the frontend map draws from,
  instead of duplicating it in a frontend data file.
- **Scoring weights/thresholds**: `app/services/scoring.py` — the
  `WEIGHTS` dict and `classify()` thresholds are the whole model; tune
  them against local knowledge of your basin.
- **Data sources**: `app/services/open_meteo.py` and
  `app/services/elevation.py` — swap in a real river-gauge API for your
  region here if one exists (the Open-Meteo Flood API's discharge data
  has limited coverage and is a *proxy*, not real gauge height).

## 7. Known limitations (be upfront about these in your pitch)

- **River level is a discharge proxy**, not an actual gauge height in
  meters. Real river stage data (e.g. India's CWC, USGS in the US)
  should replace this for anything beyond a prototype.
- **Slope is a crude 5-point elevation sample**, not a proper DEM-based
  slope raster. Fine for demoing terrain-awareness; not hydrologically
  rigorous.
- **The scoring model is hand-weighted (Tier 1), not trained** on
  historical flood outcomes. It's explainable and defensible as a
  starting point, but it is not a validated predictive model.
- **Alerts have no persistence** — they're recomputed live from current
  risk each request, so there's no real "resolved" history across
  restarts. Add a database (even SQLite) to log risk-level transitions
  if you want real alert history.
- **Auth is single-account and stateless** — one hardcoded operator
  (`Astra`), JWT tokens with no refresh/revocation flow, no rate
  limiting on login attempts. Fine for a small team prototype; add
  proper user management, refresh tokens, and login throttling before
  any wider or public deployment.

## 8. Upgrading to Tier 2 (trained ML model)

Once you have a historical dataset of
`[rainfall, river_discharge, soil_moisture, slope] -> flood_occurred`
rows for your region (from government flood records, NDMA, or your own
labeled event log):

1. Train a classifier (XGBoost/RandomForest) offline on that dataset.
2. Export it (`joblib.dump(model, "model.pkl")`).
3. In `app/services/scoring.py`, replace the body of `compute_risk`
   with `model.predict_proba([[rainfall_n, river_n, soil_n, slope_n]])`.
4. Everything upstream (data fetching) and downstream (API responses,
   frontend) stays identical — this is the only file that needs to change.
