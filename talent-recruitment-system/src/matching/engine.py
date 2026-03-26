"""Claude-powered AI matching engine for candidate-job scoring."""

import json
import logging

import anthropic

from src.config import settings
from src.db.models import CandidateProfile, JobPosting, MatchResult, get_session

logger = logging.getLogger(__name__)

JOB_EXTRACTION_PROMPT = """\
Analyze this job posting and extract structured requirements. Return valid JSON only.

Job Title: {title}
Department: {department}
Description:
{description}

Return this exact JSON structure:
{{
  "required_skills": ["skill1", "skill2"],
  "preferred_skills": ["skill1", "skill2"],
  "min_experience_years": 0,
  "seniority_level": "junior|mid|senior|lead|principal",
  "domain_keywords": ["keyword1", "keyword2"],
  "summary": "One sentence summary of the ideal candidate"
}}"""

MATCHING_PROMPT = """\
You are an expert technical recruiter for DSTA (Defence Science and Technology Agency, Singapore).
Evaluate how well this candidate matches the job requirements.

## Job Requirements
Title: {job_title}
Department: {job_department}
Required Skills: {required_skills}
Preferred Skills: {preferred_skills}
Domain Keywords: {domain_keywords}
Seniority: {seniority_level}
Min Experience: {min_experience_years} years

## Candidate Profile
Name: {candidate_name}
Headline: {candidate_headline}
Location: {candidate_location}
Bio: {candidate_bio}
Skills: {candidate_skills}
Experience: {candidate_experience}

## Instructions
Score this candidate on a scale of 0.0 to 1.0 for each dimension. Be realistic and strict.
Consider that DSTA focuses on defence technology in Singapore.

Return valid JSON only:
{{
  "skill_score": 0.0,
  "experience_score": 0.0,
  "domain_score": 0.0,
  "overall_score": 0.0,
  "confidence": "high|medium|low",
  "rationale": "2-3 sentence explanation of the match quality and key gaps"
}}"""


class MatchingEngine:
    """Uses Claude to extract job requirements and score candidates."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

    def extract_job_requirements(self, job: JobPosting) -> dict:
        """Use Claude to extract structured requirements from a job posting."""
        if not job.description:
            return {}

        prompt = JOB_EXTRACTION_PROMPT.format(
            title=job.title,
            department=job.department or "N/A",
            description=job.description[:3000],
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text.strip()
            # Extract JSON from response (handle markdown code blocks)
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            requirements = json.loads(text)
            logger.info(f"Extracted requirements for job: {job.title}")
            return requirements

        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse Claude response for job {job.id}: {e}")
            return {}
        except anthropic.APIError as e:
            logger.error(f"Claude API error for job {job.id}: {e}")
            return {}

    def extract_and_save_requirements(self, job_id: int | None = None, progress_callback=None):
        """Extract requirements for all jobs (or one) missing structured data.

        Args:
            progress_callback: Optional callable(current, total, job_title)
        """
        session = get_session()
        try:
            query = session.query(JobPosting).filter_by(status="active")
            if job_id:
                query = query.filter_by(id=job_id)
            else:
                query = query.filter(JobPosting.required_skills.is_(None))

            jobs = query.all()
            total = len(jobs)
            logger.info(f"Extracting requirements for {total} jobs")

            for i, job in enumerate(jobs):
                if progress_callback:
                    progress_callback(i + 1, total, job.title)

                reqs = self.extract_job_requirements(job)
                if reqs:
                    job.required_skills = json.dumps(reqs.get("required_skills", []))
                    job.preferred_skills = json.dumps(reqs.get("preferred_skills", []))
                    job.min_experience_years = reqs.get("min_experience_years")
                    job.seniority_level = reqs.get("seniority_level")
                    job.domain_keywords = json.dumps(reqs.get("domain_keywords", []))

            session.commit()
            logger.info(f"Requirements extracted for {len(jobs)} jobs")
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def score_candidate(self, job: JobPosting, candidate: CandidateProfile) -> dict:
        """Score a single candidate against a job using Claude."""
        prompt = MATCHING_PROMPT.format(
            job_title=job.title,
            job_department=job.department or "N/A",
            required_skills=job.required_skills or "[]",
            preferred_skills=job.preferred_skills or "[]",
            domain_keywords=job.domain_keywords or "[]",
            seniority_level=job.seniority_level or "any",
            min_experience_years=job.min_experience_years or 0,
            candidate_name=candidate.name or "Unknown",
            candidate_headline=candidate.headline or "",
            candidate_location=candidate.location or "",
            candidate_bio=candidate.bio or "",
            candidate_skills=candidate.skills or "[]",
            candidate_experience=(candidate.experience_summary or "")[:2000],
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text.strip()
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            return json.loads(text)

        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse match score for candidate {candidate.id}: {e}")
            return {}
        except anthropic.APIError as e:
            logger.error(f"Claude API error scoring candidate {candidate.id}: {e}")
            return {}

    def match_candidates_to_job(
        self,
        job_id: int,
        max_candidates: int | None = None,
        progress_callback=None,
    ) -> list[MatchResult]:
        """Score all candidates against a specific job and save results.

        Args:
            progress_callback: Optional callable(current, total, candidate_name, score_data)
                               called after each candidate is scored.
        """
        max_candidates = max_candidates or settings.match_top_n
        session = get_session()
        results = []

        try:
            job = session.query(JobPosting).filter_by(id=job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found")
                return []

            candidates = session.query(CandidateProfile).all()
            total = len(candidates)
            logger.info(f"Scoring {total} candidates against job: {job.title}")

            scored = []
            for i, candidate in enumerate(candidates):
                score_data = self.score_candidate(job, candidate)

                if progress_callback:
                    progress_callback(i + 1, total, candidate.name or "Unknown", score_data)

                if score_data and score_data.get("overall_score", 0) >= settings.min_match_score:
                    scored.append((candidate, score_data))

            # Sort by overall score descending
            scored.sort(key=lambda x: x[1].get("overall_score", 0), reverse=True)

            # Save top N
            for candidate, score_data in scored[:max_candidates]:
                # Check for existing match
                existing = (
                    session.query(MatchResult)
                    .filter_by(job_posting_id=job.id, candidate_id=candidate.id)
                    .first()
                )

                if existing:
                    existing.overall_score = score_data.get("overall_score", 0)
                    existing.skill_score = score_data.get("skill_score")
                    existing.experience_score = score_data.get("experience_score")
                    existing.domain_score = score_data.get("domain_score")
                    existing.rationale = score_data.get("rationale")
                    existing.confidence = score_data.get("confidence")
                    results.append(existing)
                else:
                    match = MatchResult(
                        job_posting_id=job.id,
                        candidate_id=candidate.id,
                        overall_score=score_data.get("overall_score", 0),
                        skill_score=score_data.get("skill_score"),
                        experience_score=score_data.get("experience_score"),
                        domain_score=score_data.get("domain_score"),
                        rationale=score_data.get("rationale"),
                        confidence=score_data.get("confidence"),
                    )
                    session.add(match)
                    results.append(match)

            session.commit()
            logger.info(f"Saved {len(results)} matches for job: {job.title}")

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        return results

    def run_full_matching(self):
        """Run matching for all active jobs."""
        session = get_session()
        try:
            jobs = session.query(JobPosting).filter_by(status="active").all()
            job_ids = [j.id for j in jobs]
        finally:
            session.close()

        logger.info(f"Running matching for {len(job_ids)} active jobs")
        for job_id in job_ids:
            self.match_candidates_to_job(job_id)
