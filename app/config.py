import os


class Settings:
    app_name = "AI Cloud Resource Optimizer"
    secret_key = os.getenv("SECRET_KEY", "change-me-for-production")
    database_url = os.getenv("DATABASE_URL", "sqlite:///./cloud_optimizer.sqlite3")
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    metrics_api_token = os.getenv("METRICS_API_TOKEN", "")


settings = Settings()
