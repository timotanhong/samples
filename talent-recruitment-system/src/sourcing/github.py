"""GitHub candidate sourcing using the GitHub REST API."""

import json
import logging
import time
from dataclasses import dataclass

import httpx

from src.config import settings
from src.db.models import CandidateProfile, CandidateSource, get_session

logger = logging.getLogger(__name__)

# Maps DSTA domains to GitHub search queries
DOMAIN_SEARCH_QUERIES = {
    "cybersecurity": [
        "cybersecurity",
        "security researcher",
        "penetration testing",
        "threat detection",
    ],
    "ai_ml": [
        "machine learning engineer",
        "deep learning",
        "computer vision",
        "natural language processing",
    ],
    "data_analytics": [
        "data engineer",
        "data scientist",
        "analytics",
    ],
    "robotics": [
        "robotics engineer",
        "autonomous systems",
        "ROS robotics",
    ],
    "iot": [
        "IoT engineer",
        "embedded systems",
        "sensor networks",
    ],
    "software_engineering": [
        "software engineer",
        "systems engineer",
        "full stack developer",
    ],
    "cloud_infrastructure": [
        "cloud engineer",
        "DevOps",
        "infrastructure engineer",
    ],
}


@dataclass
class GitHubCandidate:
    username: str
    name: str
    bio: str
    location: str
    email: str
    profile_url: str
    company: str
    public_repos: int
    followers: int
    top_languages: list[str]
    recent_repos: list[dict]
    raw_data: dict


class GitHubSourcer:
    """Sources developer candidates from GitHub using the REST API."""

    BASE_URL = "https://api.github.com"

    def __init__(self):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if settings.github_token_valid:
            headers["Authorization"] = f"Bearer {settings.github_token}"

        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=30,
        )
        self.rate_limit_remaining = 100

    def search_candidates(
        self,
        domain: str | None = None,
        query: str | None = None,
        location: str = "Singapore",
        min_followers: int = 5,
        max_results: int | None = None,
    ) -> list[GitHubCandidate]:
        """Search GitHub for candidates matching criteria."""
        max_results = max_results or settings.github_search_max_results

        if query:
            queries = [query]
        elif domain and domain in DOMAIN_SEARCH_QUERIES:
            queries = DOMAIN_SEARCH_QUERIES[domain]
        else:
            queries = ["engineer"]

        all_candidates = {}

        for q in queries:
            search_q = f"{q} location:{location}" if location else q
            candidates = self._search_users(search_q, max_results=max_results // len(queries))
            for c in candidates:
                if c.username not in all_candidates:
                    all_candidates[c.username] = c

            if len(all_candidates) >= max_results:
                break

        result = list(all_candidates.values())[:max_results]
        logger.info(f"Found {len(result)} GitHub candidates for domain={domain}, query={query}")
        return result

    def _search_users(self, query: str, max_results: int = 30) -> list[GitHubCandidate]:
        """Search GitHub users API."""
        candidates = []
        page = 1
        per_page = min(max_results, 30)

        while len(candidates) < max_results:
            self._check_rate_limit()

            try:
                resp = self.client.get(
                    "/search/users",
                    params={"q": query, "per_page": per_page, "page": page, "sort": "followers"},
                )

                # Track rate limit from response headers
                remaining = resp.headers.get("x-ratelimit-remaining")
                if remaining is not None:
                    self.rate_limit_remaining = int(remaining)

                if resp.status_code == 403 or resp.status_code == 429:
                    reset_time = resp.headers.get("x-ratelimit-reset")
                    if reset_time:
                        import time as _time
                        wait_secs = max(int(reset_time) - int(_time.time()), 1)
                        wait_secs = min(wait_secs, 120)  # Cap at 2 minutes
                    else:
                        wait_secs = 60
                    logger.warning(f"GitHub rate limit hit, waiting {wait_secs}s...")
                    time.sleep(wait_secs)
                    continue

                if resp.status_code != 200:
                    logger.warning(f"GitHub search returned {resp.status_code}: {resp.text[:200]}")
                    break

                data = resp.json()
                items = data.get("items", [])
                if not items:
                    break

                for user_data in items:
                    candidate = self._fetch_user_details(user_data["login"])
                    if candidate:
                        candidates.append(candidate)

                    if len(candidates) >= max_results:
                        break

                page += 1
                if page > 3:  # Limit pagination for MVP
                    break

            except Exception as e:
                logger.error(f"GitHub search error: {e}")
                break

        return candidates

    def _fetch_user_details(self, username: str) -> GitHubCandidate | None:
        """Fetch detailed user profile and recent repos."""
        self._check_rate_limit()

        try:
            resp = self.client.get(f"/users/{username}")
            remaining = resp.headers.get("x-ratelimit-remaining")
            if remaining is not None:
                self.rate_limit_remaining = int(remaining)

            if resp.status_code == 403 or resp.status_code == 429:
                logger.warning(f"Rate limited on user fetch for {username}, skipping")
                time.sleep(10)
                return None

            if resp.status_code != 200:
                return None

            user = resp.json()

            # Fetch top repos for language analysis
            repos_resp = self.client.get(
                f"/users/{username}/repos",
                params={"sort": "updated", "per_page": 10, "type": "owner"},
            )
            repos = repos_resp.json() if repos_resp.status_code == 200 else []

            # Extract top languages
            lang_counts: dict[str, int] = {}
            recent_repos = []
            for repo in repos:
                if isinstance(repo, dict) and not repo.get("fork"):
                    lang = repo.get("language")
                    if lang:
                        lang_counts[lang] = lang_counts.get(lang, 0) + 1
                    recent_repos.append({
                        "name": repo.get("name", ""),
                        "description": (repo.get("description") or "")[:200],
                        "language": lang or "",
                        "stars": repo.get("stargazers_count", 0),
                        "updated": repo.get("updated_at", ""),
                    })

            top_languages = sorted(lang_counts, key=lang_counts.get, reverse=True)[:5]

            return GitHubCandidate(
                username=username,
                name=user.get("name") or username,
                bio=user.get("bio") or "",
                location=user.get("location") or "",
                email=user.get("email") or "",
                profile_url=user.get("html_url", ""),
                company=user.get("company") or "",
                public_repos=user.get("public_repos", 0),
                followers=user.get("followers", 0),
                top_languages=top_languages,
                recent_repos=recent_repos[:5],
                raw_data=user,
            )

        except Exception as e:
            logger.error(f"Error fetching user {username}: {e}")
            return None

    def _check_rate_limit(self):
        """Rate limit awareness — pause when running low."""
        if self.rate_limit_remaining < 3:
            logger.info(f"Rate limit low ({self.rate_limit_remaining} remaining), sleeping 60s...")
            time.sleep(60)
            self.rate_limit_remaining = 10  # Conservative reset
        elif self.rate_limit_remaining < 10:
            # Slow down when approaching limit
            time.sleep(3)

    def save_candidates(self, candidates: list[GitHubCandidate]) -> dict:
        """Save GitHub candidates to the database."""
        session = get_session()
        stats = {"new": 0, "updated": 0, "skipped": 0}

        try:
            for gc in candidates:
                existing_source = (
                    session.query(CandidateSource)
                    .filter_by(source_type="github", source_id=gc.username)
                    .first()
                )

                if existing_source:
                    # Update raw data
                    existing_source.raw_data = json.dumps(gc.raw_data, default=str)
                    stats["updated"] += 1
                    continue

                profile = CandidateProfile(
                    name=gc.name,
                    headline=f"{gc.company} | {', '.join(gc.top_languages[:3])}" if gc.company else ", ".join(gc.top_languages[:3]),
                    location=gc.location,
                    bio=gc.bio,
                    profile_url=gc.profile_url,
                    email=gc.email,
                    skills=json.dumps(gc.top_languages),
                    experience_summary=json.dumps({
                        "public_repos": gc.public_repos,
                        "followers": gc.followers,
                        "recent_repos": gc.recent_repos,
                    }, default=str),
                )
                session.add(profile)
                session.flush()

                source = CandidateSource(
                    candidate_id=profile.id,
                    source_type="github",
                    source_id=gc.username,
                    source_url=gc.profile_url,
                    raw_data=json.dumps(gc.raw_data, default=str),
                )
                session.add(source)
                stats["new"] += 1

            session.commit()
            logger.info(f"GitHub candidate sync: {stats}")
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        return stats

    def run(self, domains: list[str] | None = None, location: str = "Singapore") -> dict:
        """Full search-and-save pipeline for specified domains."""
        if domains is None:
            domains = list(DOMAIN_SEARCH_QUERIES.keys())

        all_candidates: dict[str, GitHubCandidate] = {}
        for domain in domains:
            candidates = self.search_candidates(domain=domain, location=location)
            for c in candidates:
                if c.username not in all_candidates:
                    all_candidates[c.username] = c

        return self.save_candidates(list(all_candidates.values()))

    def close(self):
        self.client.close()
