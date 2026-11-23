# Extension Request Sorter — One-Page Project Specification

**Project Title:** Extension Request Sorter (AI Academic Workflow Assistant)  
**Academic Level:** First-Year Undergraduate AI Capstone Project  
**Author:** AI Capstone Student  
**Target Environment:** University Faculty & Academic Departments  

---

## 1. Executive Summary & Objective
University instructors spend hours triaging routine assignment extension requests. Common issues include vague emails, non-standard reasons, missing course codes, and excessive extension lengths. 

The **Extension Request Sorter** is a console-based Python application that automates the extraction and policy-based triage of student extension requests. 

**Core Safety Principle:** The system **never** approves or rejects requests autonomously. The system acts solely as an intake parser and triage assistant, sorting requests into standard buckets so human faculty can make timely, equitable, and accountable decisions.

---

## 2. System Architecture & Information Flow

```
[Student Request Email/Text]
         │
         ▼
[1. AI Extraction Layer (AECRM Prompted LLM)]
  - Extracts raw JSON: {course, days, reason, summary}
  - Strips personal names and illness conditions (Privacy Mandate)
  - Rejects calendar date arithmetic (Sets days=null for "until Friday")
         │
         ▼
[2. Deterministic Python Validation Layer]
  - Schema & Range Check: 1 <= days <= 30
  - Cross-Verification: course_code verified against courses.csv
  - Day Verification: Extracted integer verified against raw request text
  - Privacy Check: Summary <= 15 words; no sensitive medical/name terms
  - Fault Tolerance: 1 API retry + Safe fallback if API fails
         │
         ▼
[3. Academic Policy Recommendation Engine]
  - Rule 1: Missing course OR days -> "needs_more_info"
  - Rule 2: Days <= 3 AND Reason in (medical, family, technical) -> "within_policy"
  - Rule 3: Uncatalogued course OR Days > 3 OR Other reason -> "needs_faculty_review"
         │
         ▼
[4. Segregated Output Reports]
  ├── results.csv       (Clean audit log; student-safe; NO raw request text)
  ├── review_queue.csv  (Action queue for faculty; includes raw request text)
  └── summary.txt       (Aggregate metrics by recommendation, reason, course)
```

---

## 3. Technology Stack & Key Files
- **Language:** Python 3.10+ (Standard Library: `csv`, `json`, `urllib`, `re`, `os`, `sys`).
- **Data Stores:** Flat CSV files (`requests.csv`, `courses.csv`).
- **Prompt Framework:** AECRM (Authority, Exemplar, Constraint, Rubric, Metadata).
- **Security & Privacy:** Environment variable credential isolation (`.env`), zero-exposure logging, regex-based PII/medical condition redaction.

---

## 4. Key Metrics & Acceptance Criteria
- **Processing Speed:** < 1.0 second per request batch offline / ~1.5s per request via live API.
- **Red-Team Defense Rate:** 100% against prompt injection, date calculation traps, and uncatalogued course spoofing.
- **Privacy Compliance:** 0% leakage of specific illnesses or individual names into aggregate reports.
