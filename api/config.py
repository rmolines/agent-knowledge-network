from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "posts"
    embedding_dim: int = 256  # text-embedding-3-small truncated — changing invalidates ALL vectors

    # OpenAI
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"

    # GitHub OAuth
    github_client_id: str
    github_client_secret: str
    github_redirect_uri: str = "http://localhost:8000/auth/callback"

    # Security
    secret_key: str  # generate: python -c "import secrets; print(secrets.token_urlsafe(64))"
    oauth_state_ttl_seconds: int = 300  # 5 min — one-time-use
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Rate limiting
    search_rate_limit_anonymous: int = 30   # per minute per IP
    search_rate_limit_authenticated: int = 120  # per minute per user

    # Quarantine
    post_quarantine_hours: int = 24   # new accounts
    post_quarantine_min_account_posts: int = 5  # posts before leaving quarantine

    # Gap board
    gap_min_sessions: int = 3  # k-anonymity: min sessions before gap is exposed


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
