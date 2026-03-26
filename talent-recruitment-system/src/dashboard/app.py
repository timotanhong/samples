"""Streamlit dashboard for the Talent Recruitment Intelligence System."""

import json
import sys
from pathlib import Path

import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.db.models import (  # noqa: E402
    CandidateProfile,
    CandidateSource,
    JobPosting,
    MatchResult,
    get_session,
    init_db,
)

st.set_page_config(
    page_title="DSTA Talent Intelligence",
    page_icon="🎯",
    layout="wide",
)


def main():
    init_db()

    st.title("DSTA Talent Recruitment Intelligence")
    st.caption("AI-powered candidate sourcing and matching system")

    tab_jobs, tab_resumes, tab_candidates, tab_matches, tab_pipeline = st.tabs(
        ["Job Postings", "Resumes", "Candidates", "Match Results", "Pipeline"]
    )

    with tab_jobs:
        render_jobs_tab()

    with tab_resumes:
        render_resumes_tab()

    with tab_candidates:
        render_candidates_tab()

    with tab_matches:
        render_matches_tab()

    with tab_pipeline:
        render_pipeline_tab()


def render_resumes_tab():
    """Show all sourced candidates in a resume/CV card format."""
    st.header("Sourced Resumes")

    session = get_session()
    try:
        total_count = session.query(CandidateProfile).count()

        # Filters row
        col_f1, col_f2, col_f3, col_f4 = st.columns([1, 1, 1, 1])
        with col_f1:
            source_filter = st.selectbox(
                "Source", ["All", "GitHub", "Semantic Scholar"], key="resume_source"
            )
        with col_f2:
            search_q = st.text_input("Search name / skills / bio", key="resume_search")
        with col_f3:
            sort_option = st.selectbox(
                "Sort by", ["Newest First", "Name A-Z", "Most Followers", "Most Citations"],
                key="resume_sort",
            )
        with col_f4:
            st.metric("Total Resumes", total_count)

        # Build query
        source_map = {"GitHub": "github", "Semantic Scholar": "semantic_scholar"}
        query = session.query(CandidateProfile)

        if source_filter != "All":
            query = query.join(CandidateSource).filter(
                CandidateSource.source_type == source_map[source_filter]
            )

        if search_q:
            like = f"%{search_q}%"
            query = query.filter(
                CandidateProfile.name.ilike(like)
                | CandidateProfile.skills.ilike(like)
                | CandidateProfile.bio.ilike(like)
                | CandidateProfile.headline.ilike(like)
            )

        if sort_option == "Name A-Z":
            query = query.order_by(CandidateProfile.name)
        else:
            query = query.order_by(CandidateProfile.created_at.desc())

        candidates = query.limit(200).all()

        if not candidates:
            st.info("No resumes found. Run the GitHub or Semantic Scholar sourcer from the Pipeline tab.")
            return

        st.write(f"Showing **{len(candidates)}** of {total_count} resumes")
        st.write("---")

        # Render resume cards — two per row
        for i in range(0, len(candidates), 2):
            cols = st.columns(2)
            for col_idx, col in enumerate(cols):
                idx = i + col_idx
                if idx >= len(candidates):
                    break
                candidate = candidates[idx]
                _render_resume_card(col, candidate, session)

    finally:
        session.close()


def _render_resume_card(col, candidate, session):
    """Render a single resume card in the given column."""
    sources = session.query(CandidateSource).filter_by(candidate_id=candidate.id).all()
    source_types = [s.source_type for s in sources]

    # Source badge
    source_badge = ""
    for st_type in source_types:
        if st_type == "github":
            source_badge += " `GitHub`"
        elif st_type == "semantic_scholar":
            source_badge += " `Scholar`"
        else:
            source_badge += f" `{st_type}`"

    with col:
        with st.container(border=True):
            # Header: Name + source badge
            st.markdown(f"### {candidate.name or 'Unknown'}{source_badge}")

            if candidate.headline:
                st.caption(candidate.headline)

            # Location
            if candidate.location:
                st.write(f"**Location:** {candidate.location}")

            # Bio
            if candidate.bio:
                bio_text = candidate.bio[:300]
                if len(candidate.bio) > 300:
                    bio_text += "..."
                st.write(bio_text)

            # Skills
            if candidate.skills:
                try:
                    skills = json.loads(candidate.skills)
                    if skills:
                        skill_tags = " ".join([f"`{s}`" for s in skills[:8]])
                        st.markdown(f"**Skills:** {skill_tags}")
                except json.JSONDecodeError:
                    st.write(f"**Skills:** {candidate.skills}")

            # Source-specific metrics
            if candidate.experience_summary:
                try:
                    exp = json.loads(candidate.experience_summary)

                    # GitHub metrics
                    if "followers" in exp:
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Repos", exp.get("public_repos", 0))
                        m2.metric("Followers", exp.get("followers", 0))
                        # Count languages from recent repos
                        repos = exp.get("recent_repos", [])
                        langs = set()
                        for r in repos:
                            if r.get("language"):
                                langs.add(r["language"])
                        m3.metric("Languages", len(langs))

                        # Top repos
                        if repos:
                            st.write("**Recent Projects:**")
                            for repo in repos[:3]:
                                stars = repo.get("stars", 0)
                                star_str = f" ({stars} stars)" if stars > 0 else ""
                                desc = repo.get("description", "")
                                if desc:
                                    desc = f" — _{desc[:60]}_"
                                st.write(f"- **{repo.get('name', '')}**{star_str}{desc}")

                    # Scholar metrics
                    if "h_index" in exp:
                        m1, m2, m3 = st.columns(3)
                        m1.metric("h-index", exp.get("h_index", 0))
                        m2.metric("Citations", exp.get("citation_count", 0))
                        m3.metric("Papers", exp.get("paper_count", 0))

                        # Affiliations
                        affiliations = exp.get("affiliations", [])
                        if affiliations:
                            st.write(f"**Affiliations:** {', '.join(affiliations[:3])}")

                        # Top papers
                        top_papers = exp.get("top_papers", [])
                        if top_papers:
                            st.write("**Top Publications:**")
                            for paper in top_papers[:3]:
                                cites = paper.get("citations", 0)
                                year = paper.get("year", "")
                                year_str = f" ({year})" if year else ""
                                st.write(f"- {paper.get('title', 'Untitled')}{year_str} — {cites} citations")

                except json.JSONDecodeError:
                    pass

            # Profile link + email
            link_parts = []
            if candidate.profile_url:
                link_parts.append(f"[View Profile]({candidate.profile_url})")
            if candidate.email:
                link_parts.append(f"[{candidate.email}](mailto:{candidate.email})")
            if link_parts:
                st.write(" | ".join(link_parts))


def render_jobs_tab():
    """Show active job postings from DSTA."""
    st.header("Active Job Postings")

    session = get_session()
    try:
        jobs = session.query(JobPosting).filter_by(status="active").order_by(JobPosting.last_seen_at.desc()).all()

        if not jobs:
            st.info("No job postings yet. Run the scraper to fetch DSTA job listings.")
            return

        st.metric("Active Positions", len(jobs))

        for job in jobs:
            with st.expander(f"**{job.title}** — {job.department or 'N/A'}", expanded=False):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Location:** {job.location or 'N/A'}")
                    if job.url:
                        st.write(f"**Link:** [{job.url}]({job.url})")
                    if job.description:
                        st.write("**Description:**")
                        st.write(job.description[:1000] + ("..." if len(job.description or "") > 1000 else ""))

                with col2:
                    st.write("**Extracted Requirements:**")
                    if job.required_skills:
                        try:
                            skills = json.loads(job.required_skills)
                            for s in skills:
                                st.write(f"- {s}")
                        except json.JSONDecodeError:
                            st.write(job.required_skills)
                    else:
                        st.write("_Not yet extracted. Run matching engine._")

                    if job.seniority_level:
                        st.write(f"**Seniority:** {job.seniority_level}")
                    if job.min_experience_years:
                        st.write(f"**Min Experience:** {job.min_experience_years} years")

                    # Show match count
                    match_count = session.query(MatchResult).filter_by(job_posting_id=job.id).count()
                    st.metric("Matched Candidates", match_count)
    finally:
        session.close()


def render_candidates_tab():
    """Show candidate profiles from all sources."""
    st.header("Candidate Pool")

    session = get_session()
    try:
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            source_filter = st.selectbox(
                "Source",
                ["All", "github", "semantic_scholar"],
            )
        with col2:
            search_query = st.text_input("Search (name, skills, bio)")
        with col3:
            sort_by = st.selectbox("Sort by", ["Newest", "Name"])

        query = session.query(CandidateProfile)

        if source_filter != "All":
            query = query.join(CandidateSource).filter(CandidateSource.source_type == source_filter)

        if search_query:
            like_q = f"%{search_query}%"
            query = query.filter(
                CandidateProfile.name.ilike(like_q)
                | CandidateProfile.skills.ilike(like_q)
                | CandidateProfile.bio.ilike(like_q)
            )

        if sort_by == "Newest":
            query = query.order_by(CandidateProfile.created_at.desc())
        else:
            query = query.order_by(CandidateProfile.name)

        candidates = query.limit(100).all()

        st.metric("Total Candidates", session.query(CandidateProfile).count())
        st.write(f"Showing {len(candidates)} candidates")

        for candidate in candidates:
            sources = session.query(CandidateSource).filter_by(candidate_id=candidate.id).all()
            source_labels = [s.source_type for s in sources]

            with st.expander(
                f"**{candidate.name or 'Unknown'}** — {candidate.headline or ''} [{', '.join(source_labels)}]",
                expanded=False,
            ):
                col1, col2 = st.columns([2, 1])
                with col1:
                    if candidate.location:
                        st.write(f"**Location:** {candidate.location}")
                    if candidate.bio:
                        st.write(f"**Bio:** {candidate.bio[:500]}")
                    if candidate.profile_url:
                        st.write(f"**Profile:** [{candidate.profile_url}]({candidate.profile_url})")

                with col2:
                    if candidate.skills:
                        try:
                            skills = json.loads(candidate.skills)
                            st.write("**Skills/Topics:**")
                            st.write(", ".join(skills[:10]))
                        except json.JSONDecodeError:
                            st.write(f"**Skills:** {candidate.skills}")

                    if candidate.experience_summary:
                        try:
                            exp = json.loads(candidate.experience_summary)
                            if "followers" in exp:
                                st.write(f"**GitHub:** {exp.get('public_repos', 0)} repos, {exp.get('followers', 0)} followers")
                            if "h_index" in exp:
                                st.write(f"**Academic:** h-index {exp['h_index']}, {exp.get('citation_count', 0)} citations, {exp.get('paper_count', 0)} papers")
                        except json.JSONDecodeError:
                            pass
    finally:
        session.close()


def render_matches_tab():
    """Show match results with scoring."""
    st.header("Candidate-Job Matches")

    session = get_session()
    try:
        # Job selector
        jobs = session.query(JobPosting).filter_by(status="active").all()
        if not jobs:
            st.info("No jobs available. Run the scraper first.")
            return

        job_options = {f"{j.title} ({j.department or 'N/A'})": j.id for j in jobs}
        selected_job_label = st.selectbox("Select Job", list(job_options.keys()))
        selected_job_id = job_options[selected_job_label]

        matches = (
            session.query(MatchResult)
            .filter_by(job_posting_id=selected_job_id)
            .order_by(MatchResult.overall_score.desc())
            .all()
        )

        if not matches:
            st.info("No matches yet. Run the matching engine for this job.")
            return

        st.metric("Matched Candidates", len(matches))

        for i, match in enumerate(matches, 1):
            candidate = session.query(CandidateProfile).filter_by(id=match.candidate_id).first()
            if not candidate:
                continue

            score_pct = int(match.overall_score * 100)
            confidence_icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(match.confidence or "", "⚪")

            with st.expander(
                f"#{i} **{candidate.name or 'Unknown'}** — Score: {score_pct}% {confidence_icon}",
                expanded=(i <= 3),
            ):
                col1, col2, col3 = st.columns([1, 1, 1])

                with col1:
                    st.write("**Score Breakdown:**")
                    if match.skill_score is not None:
                        st.progress(match.skill_score, text=f"Skill Match: {int(match.skill_score * 100)}%")
                    if match.experience_score is not None:
                        st.progress(match.experience_score, text=f"Experience: {int(match.experience_score * 100)}%")
                    if match.domain_score is not None:
                        st.progress(match.domain_score, text=f"Domain Fit: {int(match.domain_score * 100)}%")

                with col2:
                    st.write("**Candidate Info:**")
                    st.write(f"Name: {candidate.name}")
                    st.write(f"Location: {candidate.location or 'N/A'}")
                    if candidate.profile_url:
                        st.write(f"[View Profile]({candidate.profile_url})")
                    if candidate.headline:
                        st.write(f"_{candidate.headline}_")

                with col3:
                    st.write("**AI Assessment:**")
                    st.write(f"Confidence: {match.confidence or 'N/A'}")
                    if match.rationale:
                        st.write(match.rationale)

                # Feedback buttons
                st.write("---")
                feedback_col1, feedback_col2, feedback_col3, feedback_col4 = st.columns(4)
                current_feedback = match.feedback or "pending"
                st.write(f"Current status: **{current_feedback}**")

                with feedback_col1:
                    if st.button("Contact", key=f"contact_{match.id}"):
                        _update_feedback(match.id, "contacted")
                        st.rerun()
                with feedback_col2:
                    if st.button("Interview", key=f"interview_{match.id}"):
                        _update_feedback(match.id, "interviewed")
                        st.rerun()
                with feedback_col3:
                    if st.button("Hire", key=f"hire_{match.id}"):
                        _update_feedback(match.id, "hired")
                        st.rerun()
                with feedback_col4:
                    if st.button("Reject", key=f"reject_{match.id}"):
                        _update_feedback(match.id, "rejected")
                        st.rerun()
    finally:
        session.close()


def render_pipeline_tab():
    """Pipeline controls for manual runs."""
    st.header("Pipeline Controls")
    st.write("Manually trigger pipeline stages for testing.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Scrape Jobs")
        if st.button("Run DSTA Job Scraper"):
            with st.spinner("Scraping DSTA careers page..."):
                from src.scrapers.dsta_careers import DSTACareersScraper

                scraper = DSTACareersScraper()
                try:
                    stats = scraper.run()
                    st.success(f"Done! New: {stats['new']}, Updated: {stats['updated']}, Unchanged: {stats['unchanged']}")
                except Exception as e:
                    st.error(f"Scraper error: {e}")
                finally:
                    scraper.close()

        st.subheader("2. Source Candidates")

        gh_domains = st.multiselect(
            "GitHub domains",
            ["cybersecurity", "ai_ml", "data_analytics", "robotics", "iot", "software_engineering", "cloud_infrastructure"],
            default=["ai_ml", "cybersecurity"],
        )
        gh_location = st.text_input("GitHub location filter", value="Singapore")

        if st.button("Run GitHub Sourcer"):
            with st.spinner("Searching GitHub..."):
                from src.sourcing.github import GitHubSourcer

                sourcer = GitHubSourcer()
                try:
                    stats = sourcer.run(domains=gh_domains, location=gh_location)
                    st.success(f"Done! New: {stats['new']}, Updated: {stats['updated']}")
                except Exception as e:
                    st.error(f"GitHub sourcer error: {e}")
                finally:
                    sourcer.close()

        scholar_domains = st.multiselect(
            "Scholar domains",
            ["cybersecurity", "ai_ml", "data_analytics", "robotics", "iot", "signal_processing"],
            default=["ai_ml", "cybersecurity"],
        )

        if st.button("Run Semantic Scholar Sourcer"):
            with st.spinner("Searching Semantic Scholar..."):
                from src.sourcing.semantic_scholar import SemanticScholarSourcer

                sourcer = SemanticScholarSourcer()
                try:
                    stats = sourcer.run(domains=scholar_domains)
                    st.success(f"Done! New: {stats['new']}, Updated: {stats['updated']}")
                except Exception as e:
                    st.error(f"Scholar sourcer error: {e}")
                finally:
                    sourcer.close()

    with col2:
        st.subheader("3. Extract Requirements")
        if st.button("Extract Job Requirements (Claude)"):
            with st.spinner("Extracting requirements with Claude..."):
                from src.matching.engine import MatchingEngine

                engine = MatchingEngine()
                try:
                    engine.extract_and_save_requirements()
                    st.success("Requirements extracted!")
                except Exception as e:
                    st.error(f"Extraction error: {e}")

        st.subheader("4. Match Candidates")

        session = get_session()
        try:
            jobs = session.query(JobPosting).filter_by(status="active").all()
        finally:
            session.close()

        if jobs:
            job_options = {f"{j.title}": j.id for j in jobs}
            selected = st.selectbox("Job to match", list(job_options.keys()), key="match_job")
            selected_id = job_options[selected]

            if st.button("Run Matching Engine (Claude)"):
                with st.spinner("Scoring candidates with Claude..."):
                    from src.matching.engine import MatchingEngine

                    engine = MatchingEngine()
                    try:
                        results = engine.match_candidates_to_job(selected_id)
                        st.success(f"Matched {len(results)} candidates!")
                    except Exception as e:
                        st.error(f"Matching error: {e}")
        else:
            st.info("No jobs available. Run the scraper first.")

        st.subheader("5. Database Stats")
        if st.button("Refresh Stats"):
            session = get_session()
            try:
                st.write(f"- **Jobs:** {session.query(JobPosting).count()}")
                st.write(f"- **Candidates:** {session.query(CandidateProfile).count()}")
                st.write(f"- **Sources:** {session.query(CandidateSource).count()}")
                st.write(f"- **Matches:** {session.query(MatchResult).count()}")
            finally:
                session.close()


def _update_feedback(match_id: int, feedback: str):
    """Update recruiter feedback on a match."""
    session = get_session()
    try:
        match = session.query(MatchResult).filter_by(id=match_id).first()
        if match:
            match.feedback = feedback
            session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    main()
