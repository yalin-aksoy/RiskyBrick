from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RiskyBrick API"
    app_env: str = "development"
    debug: bool = False
    bag_search_url: str = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free"
    bag_request_timeout: float = 5.0
    zaanstad_wms_url: str = "https://maps.zaanstad.nl/geoserver/wms"
    zaanstad_wfs_url: str = "https://maps.zaanstad.nl/geoserver/wfs"
    regional_map_request_timeout: float = 5.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
