from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    upload_dir: str = "uploads"
    s3_region: str
    s3_profile: str
    s3_bucket: str
    mongo_db_root_username: str
    mongo_db_root_password: str
    mongo_db_user: str
    mongo_db_password: str
    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings():
    return Settings()
