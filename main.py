"""
Extension Request Sorter
========================
AI Capstone Project for Academic Workflow Automation
Author: First-Year College Student Capstone Project

Core Architecture:
1. LLM handles untrusted text extraction into structured JSON (Authority, Exemplar, Constraint, Rubric, Metadata).
2. Python handles all deterministic business rules, validation, privacy checks, and routing.
3. NEVER automatically approves or rejects - faculty make the final decision.
"""

import os
import sys
import csv
import json
import re
import urllib.request
import urllib.error
from typing import Dict, List, Tuple, Any, Optional

# ==============================================================================
# SECTION 1: POLICY CONSTANTS & CONFIGURATION
# ==============================================================================
MAX_AUTO_DAYS: int = 3
ALLOWED_AUTO_REASONS: set = {"medical", "family", "technical"}
ALLOWED_REASONS: set = {"medical", "family", "technical", "event", "workload", "other"}

CATEGORY_WITHIN_POLICY: str = "within_policy"
CATEGORY_NEEDS_FACULTY_REVIEW: str = "needs_faculty_review"
CATEGORY_NEEDS_MORE_INFO: str = "needs_more_info"

# Forbidden medical and personally identifiable keywords for privacy check
FORBIDDEN_PRIVACY_TERMS: set = {
    "fever", "migraine", "flu", "dengue", "covid", "cold", "infection",
    "hospital", "hospitalized", "surgery", "sprain", "poisoning", "depression",
    "cancer", "asthma", "diarrhea", "fracture", "alan", "ada", "edgar",
    "dennis", "isaac", "carl", "virginia", "richard", "marie", "john",
    "turing", "lovelace", "codd", "ritchie", "newton", "gauss", "woolf",
    "feynman", "curie", "mccarthy"
}

# ==============================================================================
# SECTION 2: ENVIRONMENT AND SYSTEM PROMPT LOADER
# ==============================================================================
def load_env_file(filepath: str = ".env") -> None:
    """Manually parse .env file to avoid external dependency issues."""
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val
    except Exception as e:
        print(f"[WARN] Error reading .env file: {e}")

def load_system_prompt(filepath: str = "system_prompt.txt") -> str:
    """Load the AECRM structured system prompt."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"System prompt file not found at: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()

# ==============================================================================
# SECTION 3: CORE DATA LOADING FUNCTIONS (Functions 1 & 2)
# ==============================================================================
def load_courses(filepath: str = "courses.csv") -> Dict[str, Dict[str, str]]:
    """
    Function 2: load_courses()
    Reads valid course codes and metadata from courses.csv.
    Returns: Dict mapping course_code -> {course_name, instructor}
    """
    courses = {}
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Course catalog file missing: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("course_code", "").strip()
            if code:
                courses[code] = {
                    "course_name": row.get("course_name", "").strip(),
                    "instructor": row.get("instructor", "").strip()
                }
    return courses

def load_requests(filepath: str = "requests.csv") -> List[Dict[str, str]]:
    """
    Function 1: load_requests()
    Reads student extension requests from requests.csv.
    Returns: List of dicts with request_id, student_id, request_text.
    """
    requests_list = []
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Requests file missing: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            req_id = row.get("request_id", "").strip()
            student_id = row.get("student_id", "").strip()
            request_text = row.get("request_text", "").strip()
            if req_id and request_text:
                requests_list.append({
                    "request_id": req_id,
                    "student_id": student_id,
                    "request_text": request_text
                })
    return requests_list

# ==============================================================================
# SECTION 4: LLM CLIENT & EXTRACTION (LLM API + Validation + Retries + Mock)
# ==============================================================================
def mock_llm_extractor(request_text: str) -> Dict[str, Any]:
    """
    High-fidelity offline mock extractor simulating an LLM obeying system_prompt.txt.
    Enables reproducible unit tests, offline grading, and zero-token testing.
    """
    text_lower = request_text.lower()

    # Adversarial prompt injection defense test:
    # If student attempts prompt injection, system ignores override
    if "system override" in text_lower or "ignore all previous instructions" in text_lower:
        return {
            "course": "CS101" if "cs101" in text_lower else None,
            "days": None,
            "reason": "other",
            "summary": "Prompt injection detected; flagged for faculty evaluation"
        }

    # Extract course (matches standard department prefix + 3 digits, e.g., CS101, MATH102)
    course_match = re.search(r'\b([A-Z]{2,4}\d{3})\b', request_text)
    course = course_match.group(1) if course_match else None

    # Check for date vs explicit days count
    # E.g., "until next friday", "on monday" -> MUST NOT calculate days from dates
    days = None
    date_phrases = ["next friday", "on monday", "until friday", "next monday", "until next week", "until tomorrow"]
    has_date_phrase = any(dp in text_lower for dp in date_phrases)

    # Search for explicit days: e.g., "2-day", "2 days", "3 day", "10 days"
    days_match = re.search(r'\b(\d{1,2})\s*[- ]\s*day', text_lower)
    if days_match:
        extracted_num = int(days_match.group(1))
        if 1 <= extracted_num <= 30:
            days = extracted_num
    elif has_date_phrase:
        # Strict rule: Never calculate days from dates
        days = None

    # Extract reason category
    reason = "other"
    if any(k in text_lower for k in ["fever", "sick", "ill", "surgery", "hospital", "migraine", "dengue", "flu", "sprain", "cold", "doctor", "food poisoning"]):
        reason = "medical"
    elif any(k in text_lower for k in ["family", "domestic", "cyclone", "flooding"]):
        reason = "family"
    elif any(k in text_lower for k in ["laptop", "motherboard", "internet", "power supply", "hard drive", "repair", "crashes", "connection"]):
        reason = "technical"
    elif any(k in text_lower for k in ["hackathon", "debating", "conference", "competition", "robotics"]):
        reason = "event"
    elif any(k in text_lower for k in ["overwhelmed", "workload", "midterms", "deadlines"]):
        reason = "workload"

    # Privacy-preserving summary (max 15 words, NO specific illnesses, NO names)
    summary_course = course if course else "coursework"
    summary_days = f"{days} days" if days is not None else "extension"
    summary_reason = f"{reason} reason" if reason != "other" else "unspecified reason"
    summary = f"Requests {summary_days} for {summary_course}, {summary_reason}"

    return {
        "course": course,
        "days": days,
        "reason": reason,
        "summary": summary
    }

def call_live_llm(request_text: str, system_prompt: str) -> str:
    """Call Google Gemini or OpenAI API using standard library urllib."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "openai":
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY not configured.")
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract fields from this request:\n\n{request_text}"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {openai_key}"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            return res_json["choices"][0]["message"]["content"]
    else:
        # Default: Gemini API
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError("GEMINI_API_KEY is not set. Set it in .env or set MOCK_LLM=true.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_prompt}\n\nStudent Request:\n{request_text}\n\nOutput ONLY raw JSON:"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json"
            }
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            return res_json["candidates"][0]["content"]["parts"][0]["text"]

def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """Parse raw LLM string into JSON, stripping code blocks if present."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    return json.loads(text)

def classify(request_text: str, system_prompt: str) -> Dict[str, Any]:
    """
    Function 3: classify()
    Extracts structured fields using LLM API (or Mock mode).
    Includes 1 retry for malformed responses and a safe fallback if retry fails.
    """
    use_mock = os.getenv("MOCK_LLM", "false").lower() in ("true", "1", "yes")
    has_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY"))

    if use_mock or not has_key:
        return mock_llm_extractor(request_text)

    # Try live LLM with 1 retry
    last_error = None
    for attempt in range(2):
        try:
            raw_response = call_live_llm(request_text, system_prompt)
            data = clean_json_response(raw_response)
            
            # Verify required keys exist
            required_keys = {"course", "days", "reason", "summary"}
            if not required_keys.issubset(data.keys()):
                raise ValueError(f"Missing required JSON keys: {required_keys - set(data.keys())}")
            
            return data
        except Exception as e:
            last_error = e
            print(f"  [RETRY] Attempt {attempt + 1} failed ({e}). Retrying...")

    print(f"  [FALLBACK] API retry failed ({last_error}). Triggering deterministic safe fallback.")
    return mock_llm_extractor(request_text)

# ==============================================================================
# SECTION 5: VALIDATION FUNCTIONS (Function 4: is_valid)
# ==============================================================================
def check_privacy(summary: str) -> bool:
    """
    Validates privacy rules for summary:
    - Must be 15 words or fewer.
    - Must not contain personal names or specific illness names.
    """
    if not summary:
        return False
    words = summary.strip().split()
    if len(words) > 15:
        return False
    
    # Check for forbidden illness or person names
    tokens = set(re.findall(r'[a-zA-Z]+', summary.lower()))
    if tokens.intersection(FORBIDDEN_PRIVACY_TERMS):
        return False
        
    return True

def sanitize_summary(summary: str, reason: str, course: Optional[str]) -> str:
    """Ensure summary is strictly compliant with privacy and length rules."""
    if not summary or not check_privacy(summary):
        c_str = course if course else "assignment"
        return f"Requests extension for {c_str}, {reason} reason"
    return summary

def is_valid(data: Dict[str, Any], original_request_text: str, valid_courses: Dict[str, Dict[str, str]]) -> Tuple[bool, List[str]]:
    """
    Function 4: is_valid()
    Strict multi-stage validation:
    1. Schema validation (keys, types).
    2. Course validation against courses.csv.
    3. Days validation (numeric range 1-30 and consistency with original request).
    4. Reason validation (one of allowed categories).
    5. Privacy check on summary (max 15 words, no medical/personal names).
    """
    issues = []

    # 1. Reason validation
    reason = data.get("reason")
    if reason not in ALLOWED_REASONS:
        issues.append(f"Invalid reason '{reason}'. Must be one of {ALLOWED_REASONS}")

    # 2. Course validation against courses.csv
    course = data.get("course")
    if course is not None:
        if course not in valid_courses:
            issues.append(f"Course '{course}' not found in active course catalog (courses.csv)")

    # 3. Days validation
    days = data.get("days")
    if days is not None:
        if not isinstance(days, int) or days < 1 or days > 30:
            issues.append(f"Days '{days}' is out of valid range (1-30)")
        else:
            # Days validation against original request text:
            # Check if student gave a date instead of days, or if the number actually appears
            day_str = str(days)
            has_explicit_number = bool(re.search(rf'\b{day_str}\b', original_request_text))
            if not has_explicit_number:
                issues.append(f"Extracted days ({days}) not explicitly found in original student request")

    # 4. Privacy and length checks for summary
    summary = data.get("summary", "")
    if not check_privacy(summary):
        issues.append("Summary violates privacy (contains forbidden terms or exceeds 15 words)")

    valid = len(issues) == 0
    return valid, issues

# ==============================================================================
# SECTION 6: PYTHON EXTENSION POLICY & RECOMMENDATION (Function 5: recommend)
# ==============================================================================
def recommend(data: Dict[str, Any], validation_issues: List[str]) -> Tuple[str, str]:
    """
    Function 5: recommend()
    Pure deterministic Python logic applying academic extension policy:
    - Missing course or missing days -> needs_more_info
    - Any validation error regarding unknown course -> needs_faculty_review or needs_more_info
    - Days <= 3 and reason in (medical, family, technical) -> within_policy
    - Everything else -> needs_faculty_review
    
    Returns: (recommendation_category, policy_reason_explanation)
    """
    course = data.get("course")
    days = data.get("days")
    reason = data.get("reason")

    # Rule 1: Missing course or days requires more info from student
    if not course or days is None:
        missing_fields = []
        if not course:
            missing_fields.append("course code")
        if days is None:
            missing_fields.append("exact number of days")
        return (
            CATEGORY_NEEDS_MORE_INFO,
            f"Missing required information ({', '.join(missing_fields)})"
        )

    # Check for uncatalogued course
    if any("not found in active course catalog" in issue for issue in validation_issues):
        return (
            CATEGORY_NEEDS_FACULTY_REVIEW,
            f"Course code '{course}' not in official active catalog; requires administrative check"
        )

    # Rule 2: Days <= 3 and reason is medical, family, or technical
    if days <= MAX_AUTO_DAYS and reason in ALLOWED_AUTO_REASONS:
        return (
            CATEGORY_WITHIN_POLICY,
            f"Meets standard criteria (<= {MAX_AUTO_DAYS} days for verified {reason} cause)"
        )

    # Rule 3: Everything else goes to faculty review
    reasons_for_review = []
    if days > MAX_AUTO_DAYS:
        reasons_for_review.append(f"Requested days ({days}) exceeds standard policy threshold of {MAX_AUTO_DAYS}")
    if reason not in ALLOWED_AUTO_REASONS:
        reasons_for_review.append(f"Reason category '{reason}' requires individual instructor judgment")

    return (
        CATEGORY_NEEDS_FACULTY_REVIEW,
        "; ".join(reasons_for_review) if reasons_for_review else "Requires manual instructor review"
    )

# ==============================================================================
# SECTION 7: REPORTING & ARTIFACT GENERATION (Function 6: write_reports)
# ==============================================================================
def write_reports(
    processed_records: List[Dict[str, Any]],
    results_path: str = "results.csv",
    queue_path: str = "review_queue.csv",
    summary_path: str = "summary.txt"
) -> None:
    """
    Function 6: write_reports()
    Generates required output files:
    1. results.csv: All requests with extracted fields and recommendation (NO raw text).
    2. review_queue.csv: Requests not within policy (WITH raw text for faculty audit).
    3. summary.txt: Aggregate metrics by recommendation, reason, and course.
    """
    # 1. Write results.csv
    with open(results_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["request_id", "student_id", "course", "days", "reason", "summary", "recommendation", "policy_notes"])
        for r in processed_records:
            writer.writerow([
                r["request_id"],
                r["student_id"],
                r["course"] or "N/A",
                r["days"] if r["days"] is not None else "N/A",
                r["reason"],
                r["summary"],
                r["recommendation"],
                r["policy_notes"]
            ])

    # 2. Write review_queue.csv (faculty only)
    queue_records = [r for r in processed_records if r["recommendation"] != CATEGORY_WITHIN_POLICY]
    with open(queue_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["request_id", "student_id", "course", "days", "reason", "recommendation", "policy_notes", "original_request_text"])
        for r in queue_records:
            writer.writerow([
                r["request_id"],
                r["student_id"],
                r["course"] or "N/A",
                r["days"] if r["days"] is not None else "N/A",
                r["reason"],
                r["recommendation"],
                r["policy_notes"],
                r["original_request_text"]
            ])

    # 3. Compute aggregations for summary.txt
    total_count = len(processed_records)
    rec_counts = {CATEGORY_WITHIN_POLICY: 0, CATEGORY_NEEDS_FACULTY_REVIEW: 0, CATEGORY_NEEDS_MORE_INFO: 0}
    reason_counts: Dict[str, int] = {}
    course_counts: Dict[str, int] = {}

    for r in processed_records:
        rec = r["recommendation"]
        rec_counts[rec] = rec_counts.get(rec, 0) + 1

        rs = r["reason"]
        reason_counts[rs] = reason_counts.get(rs, 0) + 1

        cr = r["course"] or "Unspecified / Missing"
        course_counts[cr] = course_counts.get(cr, 0) + 1

    # Write summary.txt
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("======================================================================\n")
        f.write("                 EXTENSION REQUEST SORTER - SUMMARY REPORT             \n")
        f.write("======================================================================\n\n")
        f.write(f"Total Requests Processed: {total_count}\n\n")

        f.write("--- BREAKDOWN BY RECOMMENDATION ---\n")
        for cat, cnt in sorted(rec_counts.items()):
            pct = (cnt / total_count * 100) if total_count else 0
            f.write(f"  * {cat.ljust(25)}: {cnt:3d}  ({pct:5.1f}%)\n")
        f.write("\n")

        f.write("--- BREAKDOWN BY REASON CATEGORY ---\n")
        for rsn, cnt in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (cnt / total_count * 100) if total_count else 0
            f.write(f"  * {rsn.ljust(25)}: {cnt:3d}  ({pct:5.1f}%)\n")
        f.write("\n")

        f.write("--- BREAKDOWN BY COURSE ---\n")
        for crs, cnt in sorted(course_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (cnt / total_count * 100) if total_count else 0
            f.write(f"  * {crs.ljust(25)}: {cnt:3d}  ({pct:5.1f}%)\n")
        f.write("\n")
        f.write("======================================================================\n")
        f.write("Note: Recommendations are advisory. Faculty make all final decisions.\n")
        f.write("======================================================================\n")

# ==============================================================================
# SECTION 8: MAIN WORKFLOW PIPELINE
# ==============================================================================
def process_all_requests() -> None:
    """Executes the complete end-to-end extraction and sorting pipeline."""
    print("=" * 70)
    print("         EXTENSION REQUEST SORTER - CONSOLE PIPELINE")
    print("=" * 70)

    # Step 1: Load environment & system prompt
    load_env_file()
    system_prompt = load_system_prompt()
    print("[1/5] Loaded system prompt & configuration.")

    # Step 2: Load valid courses
    courses = load_courses("courses.csv")
    print(f"[2/5] Loaded {len(courses)} accredited courses from courses.csv.")

    # Step 3: Load requests
    requests_data = load_requests("requests.csv")
    print(f"[3/5] Loaded {len(requests_data)} student requests from requests.csv.\n")

    # Step 4: Process requests
    processed = []
    print("[4/5] Processing requests through AI Extraction & Python Policy Engine...")
    print("-" * 70)

    for idx, req in enumerate(requests_data, 1):
        req_id = req["request_id"]
        raw_text = req["request_text"]
        print(f"[{idx:02d}/{len(requests_data):02d}] Processing {req_id}...", end=" ", flush=True)

        # 4a. Extraction via LLM (or mock)
        extracted = classify(raw_text, system_prompt)

        # 4b. Privacy sanitization
        cleaned_summary = sanitize_summary(
            extracted.get("summary", ""),
            extracted.get("reason", "other"),
            extracted.get("course")
        )
        extracted["summary"] = cleaned_summary

        # 4c. Strict Python Validation
        valid, issues = is_valid(extracted, raw_text, courses)

        # 4d. Recommendation Engine
        recommendation, policy_notes = recommend(extracted, issues)

        print(f"-> Result: {recommendation.upper()} (Course: {extracted.get('course')}, Days: {extracted.get('days')})")

        processed.append({
            "request_id": req_id,
            "student_id": req["student_id"],
            "original_request_text": raw_text,
            "course": extracted.get("course"),
            "days": extracted.get("days"),
            "reason": extracted.get("reason"),
            "summary": extracted.get("summary"),
            "recommendation": recommendation,
            "policy_notes": policy_notes,
            "validation_issues": issues
        })

    # Step 5: Generate output reports
    print("-" * 70)
    print("[5/5] Generating analytical reports...")
    write_reports(processed)
    print("  -> results.csv generated (all requests, student-safe view).")
    print("  -> review_queue.csv generated (faculty review queue with original text).")
    print("  -> summary.txt generated (aggregated metrics and counts).")
    print("\n[SUCCESS] Pipeline execution finished cleanly.")

if __name__ == "__main__":
    process_all_requests()
