# Extension Request Sorter — Presentation Outline

**Presentation Title:** Extension Request Sorter: AI-Powered Academic Workflow Assistant  
**Presenter:** First-Year AI Capstone Student  
**Target Duration:** 10 Minutes + Q&A  
**Total Slides:** 9 Slides  

---

### Slide 1: Title & Introduction (1 Minute)
- **Slide Title:** Extension Request Sorter: AI Academic Workflow Assistant
- **Subtitle:** First-Year AI Capstone Project
- **Key Talking Points:**
  - Brief self-introduction.
  - Project vision: Using artificial intelligence responsibly to assist university educators with administrative workload.
  - Core philosophy: AI as an intake triage assistant, never an autonomous decision-maker.

---

### Slide 2: Problem Statement & Motivation (1 Minute)
- **Slide Title:** The Problem: Administrative Overload & Inconsistent Extension Triage
- **Key Talking Points:**
  - Professors and teaching assistants receive dozens of extension emails around assignment deadlines.
  - Common student communication challenges: missing course codes, vague explanations, and ambiguous dates (e.g., *"Can I submit next Friday?"*).
  - Risk of sensitive medical information being shared unprotected across email inboxes.
  - Need for an objective, privacy-safe, and consistent triage pipeline.

---

### Slide 3: Project Objectives & Core Principles (1 Minute)
- **Slide Title:** Project Objectives: Safety, Structure & Human Oversight
- **Key Talking Points:**
  - **Objective 1:** Extract structured information from free-form student emails reliably.
  - **Objective 2:** Enforce university extension policy deterministically in code.
  - **Objective 3:** Protect student medical privacy by redacting sensitive health disclosures.
  - **Golden Safety Mandate:** AI and software **never approve or reject** requests. Final authority rests 100% with human faculty.

---

### Slide 4: System Architecture & Technologies Used (1.5 Minutes)
- **Slide Title:** Decoupled Architecture: AI Extraction Meets Deterministic Python
- **Key Talking Points:**
  - **Layer 1: AI Extraction:** Uses the AECRM prompt framework to parse text into JSON (`course`, `days`, `reason`, `summary`). Supports Google Gemini 1.5 Flash, OpenAI GPT-4o-mini, and a local offline mock extractor.
  - **Layer 2: Python Validation & Privacy Engine:** Cross-checks courses against `courses.csv`, bounds days (1–30), verifies days against original text, and sanitizes summaries.
  - **Layer 3: Policy Recommendation Engine:** Classifies into `within_policy`, `needs_faculty_review`, or `needs_more_info`.
  - **Layer 4: Segregated Reporting:** Safe `results.csv` for general records; faculty-only `review_queue.csv` with raw text; `summary.txt` analytics; and an interactive Streamlit dashboard (`app.py`).

---

### Slide 5: How the Application Works (Demonstration Walkthrough) (1.5 Minutes)
- **Slide Title:** How It Works: Intake, Triage & File Generation
- **Key Talking Points:**
  - Step-by-step console pipeline (`python main.py`):
    - Reads `courses.csv` catalog and student `requests.csv`.
    - Parses each request into structured format.
    - Applies academic policy constants (`MAX_AUTO_DAYS = 3`, `ALLOWED_AUTO_REASONS = medical, family, technical`).
  - Interactive Web Dashboard (`streamlit run app.py`):
    - Visual charts of request volume by category, reason, and course.
    - Searchable tables and downloadable triage queues for faculty.

---

### Slide 6: Policy Rules & Recommendation Logic (1 Minute)
- **Slide Title:** Academic Policy Rules & Three-Tier Triage
- **Key Talking Points:**
  - **`needs_more_info`:** Missing course code or missing integer days (e.g., student wrote a calendar date). Triggers a request back to student for clarification.
  - **`within_policy`:** Routine requests meeting standard policy (days $\le$ 3 for medical, family, or technical issues). Expedites faculty sign-off.
  - **`needs_faculty_review`:** Complex cases requiring professor discretion (days > 3, workload stress, hackathons/events, or uncatalogued courses).

---

### Slide 7: Evaluation & Red-Team Testing Results (1.5 Minutes)
- **Slide Title:** Rigorous Evaluation & Adversarial Hardening
- **Key Talking Points:**
  - **Standard Evaluation Suite (5/5 Passed - 100%):** Validated medical, extended days, missing info, technical issues, and hackathons.
  - **Red-Team Security Suite (3/3 Passed - 100%):**
    - *Prompt Injection:* Blocked simulated jailbreak attempt commanding AI to act as dean.
    - *Date Calculation Trap:* Successfully blocked calendar date parsing (*"until next Friday"*), routing safely to `needs_more_info`.
    - *Catalog Spoofing:* Detected uncatalogued course `HIST999` and escalated to `needs_faculty_review`.
  - Offline Mock Engine guarantees zero API costs and 100% reproducible test results.

---

### Slide 8: Student Privacy & Responsible AI Safeguards (1 Minute)
- **Slide Title:** Privacy by Design & Responsible AI Governance
- **Key Talking Points:**
  - **Privacy Filter:** Scans and removes specific illnesses (e.g., *dengue, surgery, depression*) and student/professor names from general reports.
  - **File Segregation:** Public summaries contain generic text (*"Requests 2 days for CS101, medical reason"*). Raw student emails are restricted to authorized faculty in `review_queue.csv`.
  - **Transparency:** Every recommendation includes an explicit policy reason in `policy_notes`.

---

### Slide 9: Limitations, Future Work & Conclusion (0.5 Minutes)
- **Slide Title:** Limitations, Future Work & Key Takeaways
- **Key Talking Points:**
  - **Current Limitations:** CSV batch processing rather than direct LMS (Canvas/Moodle) integration; no automated OCR for doctor notes.
  - **Future Roadmap:** Canvas LMS webhooks, automated email replies for missing info, and attachment scanning.
  - **Conclusion:** Responsible AI does not replace educators—it reduces administrative clutter so teachers can focus on teaching and student welfare.
  - Ready for Tutor Q&A.
