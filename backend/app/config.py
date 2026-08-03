"""Backend application configuration — reads from environment variables."""
import os


DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:localdev@localhost:5432/postgres",
)

CORS_ORIGINS: list[str] = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173",
).split(",")

MODEL_ARTIFACT_PATH: str = os.getenv(
    "MODEL_ARTIFACT_PATH",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts"),
)
