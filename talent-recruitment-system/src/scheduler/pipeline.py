"""Daily pipeline orchestrator and scheduler."""

import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from src.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_job_scraper():
    """Stage 1: Scrape DSTA career page for job postings."""
    logger.info("=== Stage 1: Scraping DSTA jobs ===")
    from src.scrapers.dsta_careers import DSTACareersScraper

    scraper = DSTACareersScraper()
    try:
        stats = scraper.run()
        logger.info(f"Job scraper results: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Job scraper failed: {e}")
        return None
    finally:
        scraper.close()


def run_github_sourcing():
    """Stage 2a: Source candidates from GitHub."""
    logger.info("=== Stage 2a: GitHub candidate sourcing ===")
    from src.sourcing.github import GitHubSourcer

    sourcer = GitHubSourcer()
    try:
        stats = sourcer.run(
            domains=["cybersecurity", "ai_ml", "software_engineering", "robotics"],
            location="Singapore",
        )
        logger.info(f"GitHub sourcing results: {stats}")
        return stats
    except Exception as e:
        logger.error(f"GitHub sourcing failed: {e}")
        return None
    finally:
        sourcer.close()


def run_scholar_sourcing():
    """Stage 2b: Source candidates from Semantic Scholar."""
    logger.info("=== Stage 2b: Semantic Scholar sourcing ===")
    from src.sourcing.semantic_scholar import SemanticScholarSourcer

    sourcer = SemanticScholarSourcer()
    try:
        stats = sourcer.run(
            domains=["cybersecurity", "ai_ml", "robotics", "signal_processing"],
        )
        logger.info(f"Scholar sourcing results: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Scholar sourcing failed: {e}")
        return None
    finally:
        sourcer.close()


def run_requirement_extraction():
    """Stage 3: Extract structured requirements from job descriptions using Claude."""
    logger.info("=== Stage 3: Extracting job requirements ===")
    from src.matching.engine import MatchingEngine

    engine = MatchingEngine()
    try:
        engine.extract_and_save_requirements()
        logger.info("Requirement extraction complete")
    except Exception as e:
        logger.error(f"Requirement extraction failed: {e}")


def run_matching():
    """Stage 4: Score and rank candidates against active jobs using Claude."""
    logger.info("=== Stage 4: Running candidate matching ===")
    from src.matching.engine import MatchingEngine

    engine = MatchingEngine()
    try:
        engine.run_full_matching()
        logger.info("Matching complete")
    except Exception as e:
        logger.error(f"Matching failed: {e}")


def run_full_pipeline():
    """Run the complete daily pipeline end-to-end."""
    start_time = datetime.now()
    logger.info(f"=== Starting full pipeline at {start_time} ===")

    # Initialize database
    from src.db.models import init_db
    init_db()

    # Stage 1: Scrape jobs
    run_job_scraper()

    # Stage 2: Source candidates (both sources)
    run_github_sourcing()
    run_scholar_sourcing()

    # Stage 3: Extract requirements
    run_requirement_extraction()

    # Stage 4: Match candidates
    run_matching()

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"=== Pipeline complete in {elapsed:.1f}s ===")


def start_scheduler():
    """Start the daily scheduler."""
    from src.db.models import init_db
    init_db()

    scheduler = BlockingScheduler()

    # Daily full pipeline
    scheduler.add_job(
        run_full_pipeline,
        "cron",
        hour=settings.daily_scan_hour,
        minute=0,
        id="daily_pipeline",
        name="Daily Talent Pipeline",
    )

    # Quick job check every 6 hours
    scheduler.add_job(
        run_job_scraper,
        "cron",
        hour="*/6",
        minute=30,
        id="job_refresh",
        name="Job Posting Refresh",
    )

    logger.info(
        f"Scheduler started. Daily pipeline at {settings.daily_scan_hour}:00, "
        f"job refresh every 6 hours."
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_full_pipeline()
    else:
        start_scheduler()
