from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_path: str = "data_engineering/data/curated/supply_chain.db"
    model_path: str = "machine_learning/artifacts/delay_model.joblib"
    dq_report_path: str = "data_engineering/data/reports/dq_report.json"
    gemini_api_key: str = ""
    app_env: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
