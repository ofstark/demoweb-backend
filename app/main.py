from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import predictions, locations, alerts, geography, auth

app = FastAPI(
    title="FloodGuard AI API",
    description=(
        "Flash-flood risk prediction backend — Tier 1 weighted scoring "
        "over live rainfall, soil moisture, river discharge and terrain data."
    ),
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://demoweb-cybh.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(predictions.router)
app.include_router(locations.router)
app.include_router(alerts.router)
app.include_router(geography.router)


@app.get("/")
async def root():
    return {"status": "ok", "service": "FloodGuard AI API"}


@app.get("/health")
async def health():
    return {"status": "operational"}
