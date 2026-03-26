# DSTA Talent Recruitment Intelligence System — Technical Architecture

**Date:** 2026-03-26
**Companion to:** [FEASIBILITY_REPORT.md](./FEASIBILITY_REPORT.md)

---

## 1. System Overview

The system operates as a continuous pipeline with four major stages:
**Job Discovery** → **Candidate Sourcing** → **AI Matching** → **Recommendation Delivery**

It runs on a daily cycle, refreshing job requirements and candidate pools, then producing ranked recommendations for recruiters.

---

## 2. Detailed Component Architecture

### 2.1 Job Discovery Pipeline (Web Scraping)

**Design:**
- A **seed URL manager** maintains career page entry points (e.g., `careersearch.dsta.gov.sg/gh/en/listing/`)
- A **crawler** follows pagination and category links to discover all active listings
- A **page parser** extracts structured fields: job title, department, location, description, qualifications, dates
- A **change detector** compares each crawl against the previous snapshot via content hash diffing

**Technology Selection:**

| Concern | Recommended | Rationale |
|---------|-------------|-----------|
| Static HTML pages | **Scrapy** | Async, built-in throttling, middleware ecosystem |
| JS-rendered pages (React/Angular portals) | **Playwright** (via scrapy-playwright) | Headless Chromium renders JS; supports request interception |
| Simple one-off pages | **BeautifulSoup + httpx** | Lightweight for pages not needing a full crawl framework |
| ATS API integration | **Direct REST clients** | Many ATS platforms (Greenhouse, Lever) expose public job board APIs returning JSON — far more reliable than scraping |

**Anti-Scraping Mitigation:**
- Respect `robots.txt` and `Crawl-delay` directives
- Randomize request intervals (Poisson distribution, 5–15s between requests)
- Rotate User-Agent strings from a curated pool of real browser UAs
- Playwright with stealth plugins for Cloudflare/Akamai-protected sites
- Exponential backoff on 429/503 responses

### 2.2 Candidate Data Ingestion Pipeline

**Sources (ranked by data quality and accessibility):**

| Priority | Source | Access Method | Data Available |
|----------|--------|---------------|----------------|
| 1 | **GitHub** | REST/GraphQL API (5,000 req/hr) | Profiles, repos, languages, contributions |
| 2 | **Semantic Scholar** | Official API | Papers, citations, research areas, co-authors |
| 3 | **arXiv** | OAI-PMH API | Preprints, topics, affiliations |
| 4 | **Stack Overflow** | Public API | Reputation, tag scores, answer quality |
| 5 | **ORCID** | Public API | Career history, publications, education |
| 6 | **Kaggle** | Public API | Competition rankings, notebooks |
| 7 | **LinkedIn** | Talent Solutions API (partner license required) | Professional profiles, skills, experience |
| 8 | **Patent databases** | Google Patents | Inventions, technology areas |

**Pipeline Design:**

```
┌─────────────┐    ┌──────────────┐    ┌────────────────┐    ┌──────────────┐
│  Source      │    │  Staging     │    │ Normalization  │    │ Deduplication│
│  Connectors │───>│  Area        │───>│ Layer          │───>│ Engine       │
│  (adapters) │    │  (raw JSON)  │    │ (canonical     │    │ (merge/link) │
│             │    │              │    │  schema)       │    │              │
└─────────────┘    └──────────────┘    └────────────────┘    └──────────────┘
```

- Each source has a dedicated **connector** (adapter pattern) handling auth, pagination, rate limiting
- Raw data lands in a **staging area** (raw JSON in object storage) for auditability
- A **normalization layer** maps to canonical `CandidateProfile` schema
- **Deduplication** uses multi-signal approach:
  - Exact match on email (when available)
  - Fuzzy match on (normalized name + location + company) using Jaro-Winkler similarity
  - Graph-based clustering for transitive merge decisions
  - Soft links (likely same person) vs. hard merges (confirmed), with recruiter adjudication

### 2.3 AI Matching Engine (Detailed)

The matching engine operates in two phases:

#### Phase 1: Offline Enrichment (Daily Batch)

**Job Posting Parsing (LLM-powered):**
- Claude API extracts structured requirements from free-text descriptions:
  - Required vs. preferred skills (with confidence scores)
  - Minimum years of experience
  - Education requirements
  - Location constraints
  - Seniority level
  - Domain keywords
- System prompt instructs JSON output; validated against Pydantic models

**Candidate Profile Enrichment (LLM-powered):**
- Inferred skill list from job titles, project descriptions, repo languages
- Estimated years of experience per skill
- Career trajectory summary (growing, stable, transitioning)
- Domain expertise areas
- Runs incrementally (only new/updated profiles); results cached
- Smaller model handles straightforward profiles; Claude reserved for ambiguous cases

#### Phase 2: Matching and Scoring (Hybrid Approach)

```
Step 1: Embedding Recall (Top-N retrieval)
    ├── Generate embeddings for job requirements & candidate profiles
    ├── Store in pgvector (PostgreSQL extension)
    └── Retrieve top 200 candidates by cosine similarity

Step 2: Structured Re-Ranking
    ├── Hard filters: location, work authorization, min experience
    └── Weighted scoring across dimensions:
        ├── skill_match_score    (0-1): fraction of required skills present
        ├── experience_score     (0-1): experience vs. required range
        ├── seniority_fit        (0-1): career level alignment
        ├── recency_score        (0-1): decay by profile freshness
        ├── semantic_similarity  (0-1): embedding cosine similarity
        └── domain_relevance     (0-1): defence tech domain alignment

Step 3: LLM Qualitative Assessment (Top 20-30 only)
    ├── Claude generates 2-3 sentence rationale per candidate
    ├── Identifies gaps and risks
    └── Assigns confidence level (high/medium/low)
```

**Scoring Formula:**
```
Final Score = w1 × skill_match + w2 × experience + w3 × seniority_fit
            + w4 × recency + w5 × semantic_sim + w6 × domain_relevance
```

Weights are tunable per job category (engineering roles weight `skill_match` higher; leadership roles weight `experience` and `seniority_fit` higher).

**Calibration:** Recruiter feedback (accepted/rejected) feeds into weight tuning via logistic regression on the feature vector.

### 2.4 Pipeline Orchestration (Apache Airflow)

**DAG Structure:**

```
[Stage 1] Scrape job postings  ──┐
[Stage 2] Ingest candidate data ─┤──> [Stage 3] Run matching ──> [Stage 4] Generate recommendations
[Stage 2b] Enrich new profiles ──┘
```

**Schedule:**
- **Primary DAG (02:00 SGT daily):** Full pipeline execution
- **Quick Refresh DAG (every 6 hours):** Lightweight check for new job postings only

**Monitoring:**
- Data quality checks after each stage: row counts, schema validation, null-rate thresholds
- Scraper health: success rate per target site; alert if zero results (layout change or block)
- LLM cost tracking: token usage per call; daily budget caps with circuit breakers
- Latency tracking: wall-clock time per stage; alert if pipeline exceeds SLA

---

## 3. Data Architecture

### 3.1 Database Schema (PostgreSQL + pgvector)

```sql
-- Core tables
job_postings (
    id, url, title, department, location, description,
    content_hash, status ENUM('active','closed','draft'),
    first_seen_at, last_seen_at, created_at, updated_at
)

job_requirements (
    id, job_posting_id FK,
    required_skills JSONB, preferred_skills JSONB,
    min_experience_years, education_level,
    seniority_level, location_constraints JSONB,
    domain_keywords TEXT[], extracted_by_model VARCHAR,
    created_at
)

candidate_profiles (
    id (candidate_id), name, normalized_name,
    headline, location, current_company,
    skills JSONB, experience JSONB, education JSONB,
    source_urls TEXT[], profile_hash,
    created_at, updated_at
)

candidate_sources (
    id, candidate_id FK, source_type ENUM,
    source_url, raw_data JSONB,
    ingested_at
)

candidate_embeddings (
    candidate_id FK, embedding vector(1536),
    model_version, generated_at
)

match_results (
    id, job_posting_id FK, candidate_id FK,
    overall_score FLOAT, score_breakdown JSONB,
    llm_rationale TEXT, confidence ENUM,
    generated_at
)

recruiter_feedback (
    id, match_result_id FK, recruiter_id,
    action ENUM('contacted','interviewed','hired','rejected'),
    reason TEXT, created_at
)

compliance_audit_log (
    id, action, entity_type, entity_id,
    actor, details JSONB, created_at
)

candidate_blocklist (
    candidate_id, reason, requested_at, purged_at
)
```

### 3.2 Data Freshness Strategy

| Data Type | Full Refresh | Incremental | Retention |
|-----------|-------------|-------------|-----------|
| Job postings | Daily | Every 6 hours | Until closed + 90 days |
| Candidate profiles | Weekly per source | Daily (new only) | 12 months inactive |
| Embeddings | On profile change | On model update | Follows profile |
| Match results | Daily for active jobs | — | Follows job + 90 days |

### 3.3 Scaling Path

- **< 1M profiles:** PostgreSQL + pgvector handles everything
- **1–10M profiles:** Add Elasticsearch as read-optimized secondary index via CDC (Debezium)
- **> 10M profiles:** Consider dedicated vector DB (Qdrant/Weaviate) for embedding search

---

## 4. Dashboard Design

### 4.1 MVP (Streamlit)

Single Python app with views:
- Job board listing with match counts
- Ranked candidate cards per job with scores
- Accept/reject feedback buttons

### 4.2 Production (React + FastAPI)

**Key Views:**

1. **Job Board** — Active jobs with status, candidate count, freshness timestamp
2. **Candidate Rankings** — Per-job ranked list with:
   - Score breakdown (radar chart)
   - LLM-generated match rationale
   - Source profile links
   - Sortable by any scoring dimension
3. **Candidate Detail** — Full profile with experience timeline, skill cloud, match explanation
4. **Pipeline Health** — DAG run status, scraper success rates, LLM cost burn-down
5. **Feedback Loop** — Recruiters mark candidates as contacted/interviewed/hired/rejected

**Auth:** OAuth2/OIDC with role-based access (recruiters see only their roles' candidates)

---

## 5. Cost Estimation

| Component | Cost Driver | Monthly Estimate |
|-----------|------------|-----------------|
| LLM — Job parsing | ~100 jobs × ~2K tokens | < $5 |
| LLM — Profile enrichment | ~10K profiles × ~3K tokens | $50–$150 |
| LLM — Candidate rationale | ~100 jobs × 25 candidates × ~4K tokens | $50–$200 |
| Embeddings generation | ~10K profiles × ~500 tokens | $5–$20 |
| Infrastructure (K8s/VMs) | Airflow + DB + app servers | $200–$500 |
| LinkedIn Recruiter (optional) | Commercial license | $8,000–$12,000 |
| **Total (without LinkedIn)** | | **$310–$875/month** |
| **Total (with LinkedIn)** | | **$8,310–$12,875/month** |

Scales linearly with candidate volume and number of active jobs.

---

## 6. Privacy & Compliance Architecture

### 6.1 Privacy by Design

- **Data minimization:** Only store professional qualification data; no photos, social posts, personal opinions
- **Encryption:** At rest (database TDE) and in transit (TLS everywhere)
- **Access control:** RBAC in dashboard; audit logging on all data access
- **LLM data handling:** Anthropic API does not use input data for training (favorable for compliance)

### 6.2 PDPA Compliance Features

- **Consent tracking:** Record legal basis for processing each candidate's data
- **DSAR workflow:** Given email/name, export or delete all associated data
- **Auto-retention:** Delete profiles inactive > 12 months (configurable)
- **Opt-out mechanism:** Public-facing form; blocklist enforcement within 72 hours
- **Bias auditing:** Score distribution analysis across demographic groups; matching prompts explicitly evaluate only professional qualifications

### 6.3 Singapore AI Governance Alignment

- Align with Model AI Governance Framework
- AI Verify toolkit integration for algorithm audits
- Fair Consideration Framework compliance (merit-based evaluation)
- Explainable decisions (LLM rationale for every recommendation)

---

## 7. Implementation Phases

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Phase 1: Data Pipeline** | 4–6 weeks | Job scraping + PostgreSQL schema + Airflow DAG + Streamlit showing scraped jobs |
| **Phase 2: AI Matching** | 4–6 weeks | Candidate ingestion (GitHub, Scholar, arXiv) + LLM extraction + embedding matching + ranked dashboard |
| **Phase 3: Production** | 4–6 weeks | Structured scoring + LLM rationales + feedback loop + dedup + privacy controls + DSAR workflow |
| **Phase 4: Scale** | Ongoing | Score calibration + more sources + bias auditing + React dashboard + Elasticsearch if needed |

---

## 8. Key Technical Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Career page layout changes break scraper | Content hash monitoring; alert on zero-result crawls; prefer ATS APIs when available |
| LLM hallucination in candidate assessment | Structured output validation (Pydantic); confidence scoring; human review for top candidates |
| Deduplication errors (false merges) | Conservative thresholds; soft links requiring recruiter confirmation; graph clustering |
| Cold start (no feedback for calibration) | Expert-defined initial weights; start with simple linear combination; collect feedback from Day 1 |
| Cost overruns from LLM calls | Per-stage token budgets; circuit breakers; route simple profiles to smaller models |
| Anti-scraping escalation | Prefer official APIs; legal review per source; scrapers disableable independently |
