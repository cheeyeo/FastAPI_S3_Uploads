from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    upload_dir: str = "uploads"
    s3_region: str
    s3_profile: str
    s3_bucket: str
    model_config = SettingsConfigDict(env_file=".env")
