"""Scraper for DSTA career page to extract job postings."""

import hashlib
import json
import logging
from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup

from src.config import settings
from src.db.models import JobPosting, get_session

logger = logging.getLogger(__name__)


@dataclass
class ScrapedJob:
    title: str
    department: str = ""
    location: str = ""
    description: str = ""
    url: str = ""
    external_id: str = ""
    content_hash: str = ""


class DSTACareersScraper:
    """Scrapes DSTA's Greenhouse-hosted career page for job listings."""

    # DSTA uses Greenhouse ATS — try the JSON board API first (most reliable)
    GREENHOUSE_BOARD_API = "https://boards-api.greenhouse.io/v1/boards/dsta/jobs"
    CAREERS_PAGE = settings.dsta_careers_url

    def __init__(self):
        self.client = httpx.Client(
            timeout=30,
            headers={"User-Agent": "DSTA-TalentSystem/0.1 (internal recruitment tool)"},
            follow_redirects=True,
        )

    def scrape_jobs(self) -> list[ScrapedJob]:
        """Scrape jobs, trying Greenhouse API first, then falling back to HTML."""
        jobs = self._try_greenhouse_api()
        if jobs:
            logger.info(f"Fetched {len(jobs)} jobs from Greenhouse API")
            return jobs

        jobs = self._try_html_scrape()
        if jobs:
            logger.info(f"Scraped {len(jobs)} jobs from HTML career page")
            return jobs

        logger.warning("No jobs found from any source")
        return []

    def _try_greenhouse_api(self) -> list[ScrapedJob]:
        """Try fetching jobs from Greenhouse board API (JSON)."""
        try:
            resp = self.client.get(self.GREENHOUSE_BOARD_API, params={"content": "true"})
            if resp.status_code != 200:
                logger.info(f"Greenhouse API returned {resp.status_code}, falling back to HTML")
                return []

            data = resp.json()
            jobs = []
            for item in data.get("jobs", []):
                content = item.get("content", "")
                # Strip HTML from content
                if content:
                    content = BeautifulSoup(content, "html.parser").get_text(separator="\n").strip()

                location_name = ""
                if item.get("location"):
                    location_name = item["location"].get("name", "")

                departments = []
                for dept in item.get("departments", []):
                    departments.append(dept.get("name", ""))

                job = ScrapedJob(
                    title=item.get("title", ""),
                    department=", ".join(departments),
                    location=location_name,
                    description=content,
                    url=item.get("absolute_url", ""),
                    external_id=str(item.get("id", "")),
                    content_hash=self._hash_content(content),
                )
                jobs.append(job)
            return jobs

        except Exception as e:
            logger.info(f"Greenhouse API failed: {e}")
            return []

    def _try_html_scrape(self) -> list[ScrapedJob]:
        """Fallback: scrape the HTML career page."""
        try:
            resp = self.client.get(self.CAREERS_PAGE)
            if resp.status_code != 200:
                logger.warning(f"Career page returned {resp.status_code}")
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            jobs = []

            # Common patterns for Greenhouse-hosted career pages
            for opening in soup.select(".opening, .job-post, [data-job-id], .career-listing"):
                title_el = opening.select_one("a, h3, h4, .job-title")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                url = ""
                if title_el.name == "a" and title_el.get("href"):
                    href = title_el["href"]
                    url = href if href.startswith("http") else f"{settings.dsta_base_url}{href}"

                location_el = opening.select_one(".location, .job-location")
                location = location_el.get_text(strip=True) if location_el else ""

                dept_el = opening.select_one(".department, .job-department")
                department = dept_el.get_text(strip=True) if dept_el else ""

                job = ScrapedJob(
                    title=title,
                    department=department,
                    location=location,
                    url=url,
                    external_id=opening.get("data-job-id", ""),
                    content_hash=self._hash_content(title + location + department),
                )
                jobs.append(job)

            return jobs

        except Exception as e:
            logger.error(f"HTML scrape failed: {e}")
            return []

    def _hash_content(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def save_jobs(self, scraped_jobs: list[ScrapedJob]) -> dict:
        """Save scraped jobs to the database. Returns stats."""
        session = get_session()
        stats = {"new": 0, "updated": 0, "unchanged": 0}

        try:
            for sj in scraped_jobs:
                existing = None
                if sj.external_id:
                    existing = session.query(JobPosting).filter_by(external_id=sj.external_id).first()

                if existing:
                    if existing.content_hash != sj.content_hash:
                        existing.title = sj.title
                        existing.department = sj.department
                        existing.location = sj.location
                        existing.description = sj.description
                        existing.url = sj.url
                        existing.content_hash = sj.content_hash
                        existing.status = "active"
                        stats["updated"] += 1
                    else:
                        stats["unchanged"] += 1
                    import datetime
                    existing.last_seen_at = datetime.datetime.utcnow()
                else:
                    job = JobPosting(
                        external_id=sj.external_id or None,
                        title=sj.title,
                        department=sj.department,
                        location=sj.location,
                        description=sj.description,
                        url=sj.url,
                        content_hash=sj.content_hash,
                        status="active",
                    )
                    session.add(job)
                    stats["new"] += 1

            session.commit()
            logger.info(f"Job sync complete: {stats}")
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        return stats

    def run(self) -> dict:
        """Full scrape-and-save pipeline."""
        jobs = self.scrape_jobs()
        if not jobs:
            return {"new": 0, "updated": 0, "unchanged": 0}
        return self.save_jobs(jobs)

    def close(self):
        self.client.close()
