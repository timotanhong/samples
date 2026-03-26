"""Semantic Scholar candidate sourcing for academic/research talent."""

import json
import logging
import time
from dataclasses import dataclass

import httpx

from src.config import settings
from src.db.models import CandidateProfile, CandidateSource, get_session

logger = logging.getLogger(__name__)

# Research topics relevant to DSTA domains
DOMAIN_RESEARCH_TOPICS = {
    "cybersecurity": [
        "network security",
        "intrusion detection",
        "malware analysis",
        "cyber threat intelligence",
    ],
    "ai_ml": [
        "deep learning",
        "reinforcement learning",
        "computer vision",
        "natural language processing",
        "autonomous systems",
    ],
    "data_analytics": [
        "data mining",
        "big data analytics",
        "predictive analytics",
    ],
    "robotics": [
        "robotics",
        "unmanned aerial vehicles",
        "autonomous navigation",
        "SLAM",
    ],
    "iot": [
        "Internet of Things",
        "wireless sensor networks",
        "edge computing",
    ],
    "signal_processing": [
        "signal processing",
        "radar systems",
        "image processing",
        "sensor fusion",
    ],
}


@dataclass
class ScholarCandidate:
    author_id: str
    name: str
    affiliations: list[str]
    paper_count: int
    citation_count: int
    h_index: int
    top_papers: list[dict]
    research_areas: list[str]
    profile_url: str
    raw_data: dict


class SemanticScholarSourcer:
    """Sources research candidates from the Semantic Scholar API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self):
        headers = {}
        if settings.semantic_scholar_api_key:
            headers["x-api-key"] = settings.semantic_scholar_api_key

        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=30,
        )

    def search_candidates(
        self,
        domain: str | None = None,
        query: str | None = None,
        min_citations: int = 10,
        max_results: int | None = None,
    ) -> list[ScholarCandidate]:
        """Search for research candidates by domain or query."""
        max_results = max_results or settings.semantic_scholar_max_results

        if query:
            queries = [query]
        elif domain and domain in DOMAIN_RESEARCH_TOPICS:
            queries = DOMAIN_RESEARCH_TOPICS[domain]
        else:
            queries = ["artificial intelligence"]

        all_candidates: dict[str, ScholarCandidate] = {}

        for q in queries:
            authors = self._search_by_topic(q, max_results=max_results // len(queries))
            for a in authors:
                if a.author_id not in all_candidates and a.citation_count >= min_citations:
                    all_candidates[a.author_id] = a

            if len(all_candidates) >= max_results:
                break

            # Be polite with rate limits (100 req/s unauthenticated)
            time.sleep(1)

        result = list(all_candidates.values())[:max_results]
        logger.info(f"Found {len(result)} scholar candidates for domain={domain}, query={query}")
        return result

    def _search_by_topic(self, query: str, max_results: int = 20) -> list[ScholarCandidate]:
        """Search for papers by topic and extract authors."""
        candidates = []

        try:
            # Search for relevant papers
            resp = self.client.get(
                "/paper/search",
                params={
                    "query": query,
                    "limit": min(max_results * 2, 100),
                    "fields": "title,authors,citationCount,year,fieldsOfStudy",
                    "year": "2020-",
                },
                timeout=15,
            )

            if resp.status_code == 403:
                logger.warning(
                    "Semantic Scholar returned 403. This may be due to network restrictions. "
                    "Try running from a different network or add a Semantic Scholar API key."
                )
                return []

            if resp.status_code == 429:
                logger.warning("Semantic Scholar rate limit, waiting 30s...")
                time.sleep(30)
                return []

            if resp.status_code != 200:
                logger.warning(f"Semantic Scholar search returned {resp.status_code}")
                return []

            data = resp.json()
            papers = data.get("data", [])

            # Collect unique author IDs from top papers
            author_ids: dict[str, list[dict]] = {}
            for paper in papers:
                for author in paper.get("authors", []):
                    aid = author.get("authorId")
                    if aid:
                        if aid not in author_ids:
                            author_ids[aid] = []
                        author_ids[aid].append({
                            "title": paper.get("title", ""),
                            "year": paper.get("year"),
                            "citations": paper.get("citationCount", 0),
                            "fields": paper.get("fieldsOfStudy") or [],
                        })

            # Fetch detailed author profiles for top authors
            for author_id, papers_list in list(author_ids.items())[:max_results]:
                candidate = self._fetch_author_details(author_id, papers_list)
                if candidate:
                    candidates.append(candidate)
                time.sleep(0.5)

        except httpx.ConnectError as e:
            logger.warning(f"Cannot connect to Semantic Scholar API: {e}")
        except httpx.ProxyError as e:
            logger.warning(f"Semantic Scholar blocked by proxy: {e}")
        except httpx.TimeoutException:
            logger.warning(f"Semantic Scholar request timed out for query: {query}")
        except Exception as e:
            logger.error(f"Semantic Scholar search error: {e}")

        return candidates

    def _fetch_author_details(
        self, author_id: str, known_papers: list[dict]
    ) -> ScholarCandidate | None:
        """Fetch detailed author profile."""
        try:
            resp = self.client.get(
                f"/author/{author_id}",
                params={
                    "fields": "name,affiliations,paperCount,citationCount,hIndex,papers.title,papers.year,papers.citationCount,papers.fieldsOfStudy",
                },
            )

            if resp.status_code != 200:
                return None

            data = resp.json()

            # Extract top papers
            papers = data.get("papers") or []
            top_papers = sorted(
                [p for p in papers if isinstance(p, dict)],
                key=lambda p: p.get("citationCount", 0),
                reverse=True,
            )[:5]

            top_papers_clean = [
                {
                    "title": p.get("title", ""),
                    "year": p.get("year"),
                    "citations": p.get("citationCount", 0),
                }
                for p in top_papers
            ]

            # Extract research areas from papers
            research_areas_set: set[str] = set()
            for p in papers[:20]:
                if isinstance(p, dict):
                    for field in p.get("fieldsOfStudy") or []:
                        research_areas_set.add(field)

            return ScholarCandidate(
                author_id=author_id,
                name=data.get("name", ""),
                affiliations=data.get("affiliations") or [],
                paper_count=data.get("paperCount", 0),
                citation_count=data.get("citationCount", 0),
                h_index=data.get("hIndex", 0),
                top_papers=top_papers_clean,
                research_areas=sorted(research_areas_set),
                profile_url=f"https://www.semanticscholar.org/author/{author_id}",
                raw_data=data,
            )

        except Exception as e:
            logger.error(f"Error fetching author {author_id}: {e}")
            return None

    def save_candidates(self, candidates: list[ScholarCandidate]) -> dict:
        """Save scholar candidates to the database."""
        session = get_session()
        stats = {"new": 0, "updated": 0, "skipped": 0}

        try:
            for sc in candidates:
                existing_source = (
                    session.query(CandidateSource)
                    .filter_by(source_type="semantic_scholar", source_id=sc.author_id)
                    .first()
                )

                if existing_source:
                    existing_source.raw_data = json.dumps(sc.raw_data, default=str)
                    stats["updated"] += 1
                    continue

                affiliations_str = ", ".join(sc.affiliations) if sc.affiliations else ""
                profile = CandidateProfile(
                    name=sc.name,
                    headline=f"Researcher | h-index: {sc.h_index} | {affiliations_str}",
                    location=affiliations_str,
                    bio=f"{sc.paper_count} papers, {sc.citation_count} citations. Research areas: {', '.join(sc.research_areas[:5])}",
                    profile_url=sc.profile_url,
                    skills=json.dumps(sc.research_areas),
                    experience_summary=json.dumps({
                        "paper_count": sc.paper_count,
                        "citation_count": sc.citation_count,
                        "h_index": sc.h_index,
                        "top_papers": sc.top_papers,
                        "affiliations": sc.affiliations,
                    }, default=str),
                )
                session.add(profile)
                session.flush()

                source = CandidateSource(
                    candidate_id=profile.id,
                    source_type="semantic_scholar",
                    source_id=sc.author_id,
                    source_url=sc.profile_url,
                    raw_data=json.dumps(sc.raw_data, default=str),
                )
                session.add(source)
                stats["new"] += 1

            session.commit()
            logger.info(f"Scholar candidate sync: {stats}")
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        return stats

    def run(self, domains: list[str] | None = None) -> dict:
        """Full search-and-save pipeline."""
        if domains is None:
            domains = list(DOMAIN_RESEARCH_TOPICS.keys())

        all_candidates: dict[str, ScholarCandidate] = {}
        for domain in domains:
            candidates = self.search_candidates(domain=domain)
            for c in candidates:
                if c.author_id not in all_candidates:
                    all_candidates[c.author_id] = c

        return self.save_candidates(list(all_candidates.values()))

    def close(self):
        self.client.close()
