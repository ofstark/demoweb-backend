from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    weather_cache_ttl: int = 600  # 10 minutes
    elevation_cache_ttl: int = 2_592_000  # 30 days — terrain doesn't change

    open_meteo_forecast_url: str = "https://api.open-meteo.com/v1/forecast"
    open_meteo_flood_url: str = "https://flood-api.open-meteo.com/v1/flood"
    open_elevation_url: str = "https://api.open-elevation.com/api/v1/lookup"

    # --- Auth: single hardcoded operator account ---
    astra_username: str = "Astra"
    astra_password_hash: str = ""  # set via .env — generate with scripts/generate_hash.py
    jwt_secret_key: str = "CHANGE_ME"  # set via .env — generate a random string
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 720  # 12 hours

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def model_post_init(self, __context) -> None:
        # Guard against trailing whitespace/newlines from copy-pasting
        # secrets into a hosting provider's env var UI.
        self.astra_password_hash = self.astra_password_hash.strip()
        self.jwt_secret_key = self.jwt_secret_key.strip()
        self.astra_username = self.astra_username.strip()

    class Config:
        env_file = ".env"


settings = Settings()
