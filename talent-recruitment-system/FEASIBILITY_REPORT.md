# DSTA Talent Recruitment Intelligence System — Feasibility Report

**Date:** 2026-03-26
**Prepared for:** DSTA (Defence Science and Technology Agency, Singapore)

---

## 1. Executive Summary

This report evaluates the feasibility of building an AI-powered talent recruitment intelligence system that:

1. **Identifies talent needs** from DSTA's public website and career postings
2. **Searches public sources** (LinkedIn, GitHub, academic databases, etc.) for matching candidates
3. **Monitors daily** for new potential candidates
4. **Recommends candidates** with scoring and ranking

**Overall Feasibility: Conditionally Feasible** — The system is technically achievable but must navigate significant legal constraints, particularly around LinkedIn data access and Singapore's PDPA. The recommended approach uses official APIs, publicly available open-source profiles, and academic databases rather than scraping.

---

## 2. DSTA Talent Needs Analysis

### 2.1 Programme Centres (18 Divisions)

DSTA is organized into 18 Programme Centres, each representing a distinct hiring domain:

**Engineering Domain:**

| Programme Centre | Focus Area |
|-----------------|------------|
| **Advanced Systems** | Next-generation defence systems |
| **Air Systems** | Fighter jets, transport aircraft, helicopters, UAVs |
| **Building & Infrastructure** | Resilient and smart defence infrastructure, protective technology |
| **Land Systems** | Tracked vehicles, major fighting assets, robotics |
| **Naval Systems** | Stealth frigates, naval helicopters, sea line defence |
| **Simulation & Training Systems Hub** | Training transformation for the SAF |
| **Systems Management** | Lifecycle management of defence systems |
| **Masterplanning & Systems Architecting** | New concepts and architectures for SAF capability |
| **Systems Engineering & C3 Centre** | Front-end planning, systems architecting |

**Digital/Infocomm Domain:**

| Programme Centre | Focus Area |
|-----------------|------------|
| **C3 Development** | Command, Control, and Communications solutions |
| **Cybersecurity** | Advanced cyber defence, CyberSOC 2.0, risk assessment |
| **Cyber AI** | AI-powered cyber threat detection |
| **Digital Hub** | Digital innovation and transformation |
| **Enterprise IT** | Data analytics, IoT, agile enterprise systems, digital services |
| **Infocomm Infrastructure** | Secure networks, cloud data centres, IoT, mobility |
| **Information** | AI, data analytics, counter-disinformation, hybrid warfare |
| **Systems Resiliency** | System robustness and continuity |

### 2.2 Key Technology Domains

| Domain | Description |
|--------|-------------|
| **Artificial Intelligence & Machine Learning** | AI algorithms, disinformation countermeasures (MIT CSAIL collaboration), AI-powered cyber threat detection |
| **Cybersecurity** | CyberSOC 2.0, cyber incident monitoring/detection/response, risk assessment |
| **Data Analytics** | Enterprise IT, operational systems, decision support |
| **Command, Control & Communications (C3)** | Situational awareness, decision-making, operational effectiveness |
| **Autonomous Systems & Robotics** | UAVs, unmanned maritime drones, autonomous vehicles |
| **Internet of Things (IoT)** | Smart utilities, sensor networks, mobility solutions |
| **Virtual/Augmented/Extended Reality** | Simulation, training systems |
| **Digital Twins** | Defence technology applications |
| **Space Situational Awareness** | Partnership with Digantara Industries, National Space Agency |
| **Cloud Computing** | Cloud data centres, secure infrastructure |
| **Systems Engineering** | Large-scale defence system design and integration |
| **Protective Technology & Smart Infrastructure** | Energy efficiency, smart utilities (SP Group partnership) |
| **Software Development** | Systems integration, application development |

### 2.3 Typical Role Profiles

- Software Engineer / Senior Engineer
- Cybersecurity Engineer / Research Engineer
- Visual AI Engineer (Digital Hub)
- Data Scientist / Data Engineer
- Systems Analyst / Business Analyst
- Analyst Programmer
- Network Administrator
- Engineer (Unmanned Aircraft Systems)
- UX Architect
- Procurement Specialist

Career progression follows two tracks: **Managerial** (leadership) and **Technical** (deep expertise).

### 2.4 Talent Profile Characteristics

**Required Qualifications:**
- Singapore Citizenship (mandatory for most roles and all scholarships)
- Degree in Engineering, Computing, IT, Mathematics, or Science
- Good academic and co-curricular activity (CCA) track record

**Key Skill Domains Sought:**
- Systems engineering and integration
- Software development (full-stack, embedded)
- AI/ML and data analytics
- Cybersecurity engineering and operations
- Network and cloud infrastructure
- IoT and sensor systems
- Simulation and modelling
- Robotics and autonomous systems

### 2.5 Talent Pipeline Programmes (Sourcing Signals)

These programmes represent key talent pipeline indicators the system should monitor:

| Programme | Target | Description |
|-----------|--------|-------------|
| **DSTA Scholarship** | University students | Full sponsorship for STEM degrees; includes global internship |
| **DSTA Merit Scholarship** | University students | Digital technologies and cybersecurity focus |
| **DSTA Polytechnic Digital Scholarship** | Polytechnic students | IT/cybersecurity diplomas (no bond); AI, data analytics, IoT |
| **Technology Undergraduate Programme (Tech UP)** | Top Year 2 undergrads | Exclusive internship + curated courses + networking |
| **Technology Graduate Programme (TGP)** | Fresh graduates | Structured entry with career mentor and development plan |
| **BrainHack** | Students (4,000+ participants) | Annual competition in cybersecurity, AI, XR, coding, space tech |
| **Internships** | Students | 3–6 months in engineering, infocomm, cybersecurity |

**Partner Organizations** (defence technology community):
- DSO National Laboratories
- CSIT (Centre for Strategic Infocomm Technologies)

---

## 3. Data Source Feasibility Analysis

### 3.1 LinkedIn

| Approach | Feasibility | Risk |
|----------|-------------|------|
| **LinkedIn Talent Solutions API** (official partner) | High — but requires partnership approval | Low |
| **LinkedIn Recruiter + Hiring Assistant** | High — LinkedIn's own AI tools | Low |
| **Third-party tools using official APIs** | Medium — dependent on vendor | Low |
| **Scraping public profiles (no account)** | Low — legal gray area | High |
| **Scraping with LinkedIn account** | Not Recommended — breach of ToS | Very High |

**Key Legal Context:**
- LinkedIn actively enforces its Terms of Service against scrapers. In 2025, LinkedIn won against Proxycurl, forcing permanent deletion of all scraped data.
- The hiQ v. LinkedIn case (settled 2022) established that even scraping publicly visible data can be contractually prohibited if you have a LinkedIn account.
- LinkedIn offers an AI-powered "Hiring Assistant" within Recruiter that automates sourcing and reduces profile review by 62%.

**Recommendation:** Use LinkedIn Talent Solutions API (requires becoming an approved partner) or subscribe to LinkedIn Recruiter for official, legal access.

### 3.2 GitHub (Developer Talent)

| Approach | Feasibility | Risk |
|----------|-------------|------|
| **GitHub REST/GraphQL API** | High — generous rate limits, public data | Low |
| **GitHub profile analysis** | High — contributions, repos, languages | Low |

**What's Available:**
- Public profiles, repositories, contribution history
- Programming languages, project involvement
- Star counts, follower networks
- Organization memberships

**Relevance to DSTA:** Excellent for sourcing software engineers, AI/ML engineers, and cybersecurity researchers through code contributions.

### 3.3 Academic Sources

| Source | Feasibility | Data Available |
|--------|-------------|----------------|
| **Google Scholar** | Medium — no official API, but Semantic Scholar API available | Publications, citations, h-index |
| **Semantic Scholar API** | High — free, well-documented | Papers, authors, citations, topics |
| **ORCID API** | High — open API | Researcher profiles, affiliations |
| **arXiv API** | High — free, open | Preprints in CS, physics, math |
| **DBLP** | High — open data | CS publication records |
| **ResearchGate** | Low — no API, anti-scraping | Researcher profiles |

**Relevance to DSTA:** Critical for sourcing AI/ML researchers, cybersecurity researchers, and signal processing experts.

### 3.4 Other Public Sources

| Source | Feasibility | Use Case |
|--------|-------------|----------|
| **Stack Overflow / Stack Exchange** | High — public API | Developer expertise assessment |
| **Patent databases (e.g., Google Patents)** | High — public | Innovation track record |
| **Conference speaker lists** | Medium — manual curation | Domain experts |
| **Professional association directories** | Medium — varies by org | Credentialed professionals |
| **Government job boards (Careers@Gov)** | High — public | Current/former public sector talent |
| **Kaggle** | High — public API | Data science / ML talent |

---

## 4. Legal & Compliance Framework

### 4.1 Singapore PDPA Compliance

The Personal Data Protection Act (PDPA) imposes strict requirements:

- **Consent:** Must obtain consent before collecting personal data, or rely on a legitimate purpose exception
- **Purpose Limitation:** Data collected only for stated recruitment purposes
- **Data Minimization:** Only collect what's necessary at each recruitment stage
- **Retention:** Must delete candidate data when no longer needed
- **Penalties:** Up to SGD $1 million or 10% annual turnover for breaches

### 4.2 Key Compliance Requirements for the System

1. **Transparency:** Inform candidates how their publicly available data was found and is being used
2. **Opt-Out Mechanism:** Provide a way for individuals to request removal from the system
3. **Data Protection:** Encryption at rest and in transit, access controls, audit logs
4. **Bias Mitigation:** Regular audits of AI matching algorithms for fairness
5. **Fair Consideration Framework (FCF):** Ensure compliance with Singapore's fair hiring guidelines
6. **AI Governance:** Align with Singapore's Model AI Governance Framework and AI Verify toolkit

### 4.3 Recommended Legal Approach

- Use only **official APIs** and **publicly shared data** (no scraping)
- Implement **privacy-by-design** principles
- Maintain **audit trails** for all candidate data processing
- Conduct **regular PDPA compliance reviews**
- Engage legal counsel specializing in Singapore data protection law

---

## 5. Proposed System Architecture

### 5.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TALENT INTELLIGENCE PLATFORM                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │  JOB NEEDS   │    │  CANDIDATE   │    │   AI MATCHING    │   │
│  │  EXTRACTOR   │    │  INGESTION   │    │     ENGINE       │   │
│  │              │    │   PIPELINE   │    │                  │   │
│  │ • DSTA site  │    │              │    │ • LLM semantic   │   │
│  │ • Job posts  │    │ • GitHub API │    │   matching       │   │
│  │ • NLP parse  │    │ • Scholar API│    │ • Skill scoring  │   │
│  │              │    │ • LinkedIn   │    │ • Experience     │   │
│  │              │    │   (official) │    │   ranking        │   │
│  │              │    │ • arXiv API  │    │ • Deduplication  │   │
│  │              │    │ • ORCID API  │    │                  │   │
│  └──────┬───────┘    │ • Kaggle API │    └────────┬─────────┘   │
│         │            │ • StackOverf │             │              │
│         │            └──────┬───────┘             │              │
│         │                   │                     │              │
│  ┌──────▼───────────────────▼─────────────────────▼──────────┐  │
│  │                    DATA STORE LAYER                        │  │
│  │                                                            │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │  │
│  │  │ PostgreSQL  │  │ Elasticsearch│  │  Redis Cache    │   │  │
│  │  │ (primary)   │  │ (search)     │  │  (dedup/rate)   │   │  │
│  │  └─────────────┘  └──────────────┘  └─────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │  SCHEDULER   │    │  COMPLIANCE  │    │   DASHBOARD &    │   │
│  │              │    │    ENGINE     │    │   NOTIFICATIONS  │   │
│  │ • Daily scan │    │              │    │                  │   │
│  │ • Rate limit │    │ • PDPA check │    │ • Candidate list │   │
│  │ • Retry      │    │ • Consent    │    │ • Match scores   │   │
│  │              │    │ • Audit log  │    │ • Daily digest   │   │
│  │              │    │ • Data TTL   │    │ • Email alerts   │   │
│  └──────────────┘    └──────────────┘    └──────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Component Details

#### Component 1: Job Needs Extractor
- **Purpose:** Monitor DSTA's career page and extract structured role requirements
- **Technology:** Python + BeautifulSoup/Playwright for page parsing, Claude API for NLP extraction
- **Output:** Structured job profiles with required skills, experience levels, domains
- **Frequency:** Daily scan of `https://careersearch.dsta.gov.sg/gh/en/listing/`

#### Component 2: Candidate Ingestion Pipeline
- **Purpose:** Aggregate candidate profiles from multiple public sources
- **Sources & Methods:**

| Source | Method | Data Points |
|--------|--------|-------------|
| GitHub | REST/GraphQL API | Repos, languages, contributions, bio, location |
| Semantic Scholar | Official API | Papers, citations, research areas, co-authors |
| arXiv | OAI-PMH API | Preprints, topics, affiliations |
| ORCID | Public API | Career history, publications, education |
| Stack Overflow | Public API | Reputation, tags, answers quality |
| LinkedIn | Talent Solutions API (partner) | Professional profiles, skills, experience |
| Kaggle | Public API | Competition rankings, datasets, notebooks |
| Patent databases | Google Patents API | Inventions, technology areas |

- **Technology:** Apache Airflow for orchestration, Python for API clients
- **Rate Limiting:** Respect all API rate limits with exponential backoff

#### Component 3: AI Matching Engine
- **Purpose:** Score and rank candidates against job requirements
- **Approach:** Hybrid scoring model

```
Final Score = w1 × Skill_Match + w2 × Experience_Match + w3 × Domain_Relevance
            + w4 × Publication_Score + w5 × Code_Quality + w6 × Location_Fit
```

- **Skill Matching:** Use Claude API for semantic similarity between job requirements and candidate profiles (beyond keyword matching)
- **Experience Scoring:** Years of relevant experience, seniority of past roles
- **Domain Relevance:** Alignment with DSTA's defence technology domains
- **Publication Score:** h-index, citation count, relevance of research topics
- **Code Quality:** GitHub contribution metrics, project impact (stars, forks)
- **Technology:** Claude API (claude-opus-4-6) for semantic matching, scikit-learn for scoring models

#### Component 4: Scheduler & Monitoring
- **Purpose:** Automated daily pipeline execution
- **Technology:** Apache Airflow or Celery Beat
- **Schedule:**
  - **Daily (6 AM SGT):** Scan career page for new/changed job postings
  - **Daily (8 AM SGT):** Run candidate search for new/updated roles
  - **Daily (10 AM SGT):** Generate and send recommendation digest
  - **Weekly:** Full re-score of existing candidate pool

#### Component 5: Compliance Engine
- **Purpose:** Ensure PDPA compliance and ethical AI governance
- **Features:**
  - Consent tracking and opt-out management
  - Automatic data expiry (configurable TTL)
  - Audit log for all data access and processing
  - Bias detection and fairness metrics
  - Data anonymization for initial screening

#### Component 6: Dashboard & Notifications
- **Purpose:** Recruiter-facing interface for reviewing recommendations
- **Technology:** React frontend + FastAPI backend (or Streamlit for MVP)
- **Features:**
  - Ranked candidate lists per role
  - Match score breakdown and explanation
  - Candidate profile aggregation (multi-source view)
  - Daily email digest with top new candidates
  - Filtering by domain, skill, location, experience
  - Export to ATS (Applicant Tracking System)

### 5.3 Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Language** | Python 3.12+ | Rich ecosystem for NLP, APIs, data processing |
| **Web Framework** | FastAPI | Async support, auto-docs, high performance |
| **AI/LLM** | Claude API (Anthropic) | Semantic matching, NLP extraction, scoring |
| **Database** | PostgreSQL 16 | Robust relational data, JSONB for flexible schemas |
| **Search** | Elasticsearch 8.x | Full-text search, vector similarity for candidate matching |
| **Cache** | Redis | Rate limit tracking, deduplication, session cache |
| **Orchestration** | Apache Airflow | DAG-based scheduling, monitoring, retry logic |
| **Frontend** | React + TypeScript | Modern dashboard UI (or Streamlit for MVP) |
| **Deployment** | Docker + Kubernetes | Scalable, cloud-agnostic deployment |
| **Monitoring** | Prometheus + Grafana | Pipeline health, API rate tracking |

---

## 6. Implementation Roadmap

### Phase 1: MVP (Weeks 1–6)
- Job needs extractor for DSTA career page
- GitHub API integration for developer candidate sourcing
- Semantic Scholar / arXiv integration for researcher sourcing
- Basic Claude-powered matching engine
- Streamlit dashboard for candidate review
- Daily scheduling with cron/Celery
- **Deliverable:** Working prototype sourcing candidates from GitHub + academic sources

### Phase 2: Enhanced Sourcing (Weeks 7–12)
- LinkedIn Talent Solutions API integration (requires partner application)
- Stack Overflow, Kaggle, ORCID integrations
- Advanced scoring model with multi-source profile merging
- Deduplication engine (same person across sources)
- Email digest notifications
- PDPA compliance engine (consent, audit logs, data TTL)
- **Deliverable:** Multi-source candidate intelligence platform

### Phase 3: Production (Weeks 13–18)
- React dashboard with full recruiter workflow
- ATS integration (export candidates)
- Bias detection and fairness monitoring
- Admin panel for configuring search criteria and weights
- Performance analytics and reporting
- Security hardening and access controls
- **Deliverable:** Production-ready talent intelligence system

### Phase 4: Advanced Features (Weeks 19+)
- Candidate engagement tracking (outreach, response rates)
- Predictive analytics (candidate likelihood to respond)
- Market intelligence (talent pool trends, competitor hiring)
- Integration with internal HR systems

---

## 7. Cost Estimates

| Item | Monthly Cost (Est.) |
|------|-------------------|
| Claude API (matching + extraction) | $500–$2,000 |
| LinkedIn Talent Solutions (Recruiter Seat) | $8,000–$12,000 |
| Cloud Infrastructure (AWS/GCP) | $500–$1,500 |
| Elasticsearch (managed) | $200–$500 |
| GitHub API | Free (within rate limits) |
| Academic APIs (Semantic Scholar, arXiv) | Free |
| **Total (without LinkedIn)** | **$1,200–$4,000/month** |
| **Total (with LinkedIn Recruiter)** | **$9,200–$16,000/month** |

---

## 8. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LinkedIn API access denied | Medium | High | Start with non-LinkedIn sources; apply early for partnership |
| PDPA non-compliance | Low | Very High | Legal review, privacy-by-design, compliance engine |
| Low candidate match quality | Medium | Medium | Iterative model tuning, recruiter feedback loop |
| API rate limiting | Low | Low | Respect limits, caching, exponential backoff |
| Data staleness | Medium | Medium | Daily refresh cycles, timestamp tracking |
| AI bias in candidate scoring | Medium | High | Regular audits, fairness metrics, diverse training data |
| Defence sector sensitivity | Medium | High | No classified data, public sources only, security review |

---

## 9. Existing Commercial Alternatives

Before building a custom system, consider these established platforms:

| Platform | Strengths | Pricing |
|----------|-----------|---------|
| **SeekOut** | Deep tech talent search, GitHub/Scholar integration, diversity | Enterprise pricing |
| **Eightfold.ai** | AI matching, talent intelligence, large profile database | Enterprise pricing |
| **hireEZ (Hiretual)** | Multi-source sourcing, outreach automation | $149+/month |
| **Juicebox (PeopleGPT)** | Natural language search, 800M+ profiles | Custom pricing |
| **HeroHunt.ai** | GPT-powered sourcing, cross-platform search | Custom pricing |
| **LinkedIn Recruiter** | Largest professional network, AI Hiring Assistant | $8,000+/month |

**Build vs. Buy Recommendation:** A hybrid approach is recommended — use LinkedIn Recruiter for LinkedIn-specific sourcing, and build a custom system for GitHub/academic/open-source intelligence that is tailored to DSTA's unique defence technology domains.

---

## 10. Conclusion & Recommendations

### Feasibility Verdict: **YES, with constraints**

Building this system is technically feasible and potentially high-value. The key recommendations are:

1. **Start with freely available sources** (GitHub, Semantic Scholar, arXiv, ORCID, Stack Overflow) — these provide excellent coverage for DSTA's technical hiring needs and have permissive API access.

2. **Use official LinkedIn channels** — Apply for LinkedIn Talent Solutions partnership or subscribe to LinkedIn Recruiter. Do NOT scrape LinkedIn.

3. **Invest in compliance from Day 1** — Build PDPA compliance into the architecture, not as an afterthought. Engage a Singapore data protection officer.

4. **Use LLMs for intelligent matching** — Claude API provides the semantic understanding needed to match candidates beyond keyword matching, understanding contextual skills and domain relevance.

5. **Consider a hybrid approach** — Combine a commercial tool (LinkedIn Recruiter) for professional network sourcing with a custom-built system for open-source intelligence (GitHub, academic, patents).

6. **Plan for a 4–6 month MVP** — The initial system covering GitHub + academic sources with Claude-powered matching can be built in 6 weeks, with full production readiness in 4–5 months.

---

## Sources

- [LinkedIn Talent Solutions API](https://learn.microsoft.com/en-us/linkedin/talent/?view=li-lts-2025-10)
- [LinkedIn API Developer Catalog](https://developer.linkedin.com/product-catalog/talent)
- [LinkedIn Takes Legal Action to Defend Member Privacy (2025)](https://news.linkedin.com/2025/linkedin-takes-legal-action-to-defend-member-privacy)
- [LinkedIn Wins Legal Case Against Data Scrapers (Proxycurl)](https://www.socialmediatoday.com/news/linkedin-wins-legal-case-data-scrapers-proxycurl/756101/)
- [PDPA Compliance for HR Data](https://www.kelick.io/post/pdpa-compliance-for-hr-data)
- [How Recruitment Automation Tools Ensure Compliance with Singaporean Laws](https://www.mokahr.io/myblog/recruitment-automation-tools-singapore-compliance/)
- [DSTA Careers](https://www.dsta.gov.sg/join-us/job-seeker/dsta-careers)
- [DSTA at NUS Career Fair](https://careerfair.comp.nus.edu.sg/Company0824/DSTA.html)
- [Best AI Talent Sourcing Tools for Recruiters 2026](https://juicebox.ai/blog/ai-sourcing-tools)
- [Recruitment Intelligence: Modern AI Techniques (HeroHunt)](https://www.herohunt.ai/blog/recruitment-intelligence-modern-ai-techniques-to-find-the-top-1-talent)
- [Most Accurate AI Candidate Matching Platforms 2025](https://nodes.inc/blogs/most-accurate-ai-candidate-matching-platforms-2025)
- [Singapore PDPA Compliance Guide](https://www.hawksford.com/insights-and-guides/pdpa-compliance-in-singapore)
- [LinkedIn Scraping Legal Guide](https://blog.closelyhq.com/how-to-scrape-linkedin-data-legally/)
