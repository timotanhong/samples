# DSTA Talent Recruitment Intelligence System

AI-powered system that identifies talent needs from DSTA's career page and sources matching candidates from GitHub, Semantic Scholar, and other public sources. Uses Claude for semantic matching and scoring.

## Architecture

```
DSTA Career Page ──► Job Scraper ──► Job Requirements (Claude extraction)
                                              │
GitHub API ──────►                            ▼
                   Candidate Pool ──► AI Matching Engine (Claude) ──► Streamlit Dashboard
Semantic Scholar ──►                          │
                                              ▼
                                    Ranked Recommendations
                                    with scores & rationale
```

## Quick Start

### 1. Install dependencies

```bash
cd talent-recruitment-system
pip install -e .
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys:
#   TRS_ANTHROPIC_API_KEY=sk-ant-...   (required for matching)
#   TRS_GITHUB_TOKEN=ghp_...           (recommended for higher rate limits)
```

### 3. Initialize the database

```bash
python -c "from src.db.models import init_db; init_db()"
```

### 4. Run the pipeline (one-shot)

```bash
python -m src.scheduler.pipeline --once
```

### 5. Launch the dashboard

```bash
streamlit run src/dashboard/app.py
```

The dashboard provides:
- **Job Postings** — Active DSTA positions with extracted requirements
- **Candidates** — Sourced profiles from GitHub and Semantic Scholar
- **Match Results** — AI-scored candidate-job matches with rationale
- **Pipeline** — Manual controls to run each stage independently

## Project Structure

```
talent-recruitment-system/
├── src/
│   ├── config.py                 # Settings from .env
│   ├── db/
│   │   └── models.py             # SQLAlchemy models (JobPosting, CandidateProfile, MatchResult)
│   ├── scrapers/
│   │   └── dsta_careers.py       # DSTA career page scraper (Greenhouse API + HTML fallback)
│   ├── sourcing/
│   │   ├── github.py             # GitHub candidate sourcing via REST API
│   │   └── semantic_scholar.py   # Academic candidate sourcing via Semantic Scholar API
│   ├── matching/
│   │   └── engine.py             # Claude-powered job requirement extraction and candidate scoring
│   ├── dashboard/
│   │   └── app.py                # Streamlit recruiter dashboard
│   └── scheduler/
│       └── pipeline.py           # Daily pipeline orchestrator and APScheduler config
├── pyproject.toml                # Python dependencies
├── .env.example                  # Environment variable template
├── FEASIBILITY_REPORT.md         # Full feasibility study
└── TECHNICAL_ARCHITECTURE.md     # Detailed technical architecture
```

## Pipeline Stages

| Stage | Description | Trigger |
|-------|-------------|---------|
| **1. Job Scraper** | Fetches DSTA job listings via Greenhouse API (with HTML fallback) | Daily 6:00 AM + every 6 hours |
| **2a. GitHub Sourcing** | Searches GitHub for developers in cybersecurity, AI/ML, robotics, etc. | Daily |
| **2b. Scholar Sourcing** | Searches Semantic Scholar for researchers in relevant domains | Daily |
| **3. Requirement Extraction** | Uses Claude to extract structured skills/requirements from job descriptions | After new jobs found |
| **4. Candidate Matching** | Uses Claude to score and rank candidates against each job | Daily |

## Configuration

All settings are configured via environment variables (prefix `TRS_`):

| Variable | Description | Default |
|----------|-------------|---------|
| `TRS_DATABASE_URL` | Database connection string | `sqlite:///talent_recruitment.db` |
| `TRS_ANTHROPIC_API_KEY` | Claude API key (required for matching) | — |
| `TRS_GITHUB_TOKEN` | GitHub PAT (recommended) | — |
| `TRS_CLAUDE_MODEL` | Claude model for matching | `claude-sonnet-4-20250514` |
| `TRS_MATCH_TOP_N` | Max candidates to match per job | `20` |
| `TRS_MIN_MATCH_SCORE` | Minimum score threshold | `0.3` |
| `TRS_DAILY_SCAN_HOUR` | Daily pipeline hour (24h, SGT) | `6` |

## Running the Scheduler (Continuous)

```bash
python -m src.scheduler.pipeline
```

This starts APScheduler with:
- **Daily pipeline** at the configured hour (default 6 AM)
- **Job refresh** every 6 hours

## Data Sources

| Source | API | Cost | Coverage |
|--------|-----|------|----------|
| DSTA Careers | Greenhouse board API | Free | DSTA job listings |
| GitHub | REST/GraphQL API | Free (5,000 req/hr with token) | 100M+ developer profiles |
| Semantic Scholar | REST API | Free (1,000 req/s) | 200M+ academic papers |

## Next Steps (Post-MVP)

- [ ] Add LinkedIn Recruiter integration (official API)
- [ ] Add patent database sourcing (USPTO/Lens.org)
- [ ] PostgreSQL + pgvector for production deployment
- [ ] Embedding-based pre-filtering before Claude scoring
- [ ] Email digest notifications for new top matches
- [ ] PDPA compliance engine (consent, audit logs, data TTL)
- [ ] Bias detection and fairness monitoring
- [ ] React dashboard for multi-user production use
