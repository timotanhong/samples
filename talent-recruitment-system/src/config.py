"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///talent_recruitment.db"

    # Anthropic / Claude
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # GitHub (leave empty for unauthenticated access, 60 req/hr)
    github_token: str = ""

    @property
    def github_token_valid(self) -> bool:
        return bool(self.github_token) and self.github_token not in ("", "ghp_...", "ghp_")
    github_search_max_results: int = 50

    # Semantic Scholar
    semantic_scholar_api_key: str = ""
    semantic_scholar_max_results: int = 50

    # DSTA Careers
    dsta_careers_url: str = "https://careersearch.dsta.gov.sg/gh/en/listing/"
    dsta_base_url: str = "https://www.dsta.gov.sg"

    # Matching
    match_top_n: int = 20
    min_match_score: float = 0.3

    # Scheduler
    daily_scan_hour: int = 6
    daily_match_hour: int = 8

    model_config = {"env_file": ".env", "env_prefix": "TRS_"}


settings = Settings()
