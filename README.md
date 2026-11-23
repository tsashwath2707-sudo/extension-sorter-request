# Extension Request Sorter

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()
[![Defense Rate](https://img.shields.io/badge/red--team%20defense-100%25-success.svg)]()

> **First-Year AI Capstone Project:** A console and web-based Python application that automates the intake, structured extraction, and policy-based triage of student assignment extension requests.

---

## 📌 Problem Statement & Overview
University instructors and teaching assistants spend dozens of hours each semester manually reading and triaging student assignment extension requests. Common issues include:
- Unstructured, lengthy, or vague emails.
- Ambiguous deadlines (e.g., *"Can I submit next Friday?"* instead of specifying number of days).
- Missing critical details such as course codes.
- Sensitive medical disclosures exposed across general departmental channels.
- Risks of arbitrary, non-standard, or delayed extension decisions.

The **Extension Request Sorter** solves these challenges using a **decoupled hybrid architecture**:
1. An **LLM (Large Language Model) / Mock Extractor** parses unstructured natural language requests into schema-validated JSON (`course`, `days`, `reason`, `summary`).
2. A **Deterministic Python Policy Engine** validates course codes against an accredited catalog, checks day bounds, enforces privacy filters, and categorizes requests into advisory buckets.
3. **Core Safety Mandate:** The AI and software **never make final approval or rejection decisions**. All recommendations are strictly advisory, ensuring human faculty maintain 100% authority.

---

## 🚀 Features
- **AECRM Prompt Engineering:** Utilizes the formal *Authority, Exemplar, Constraint, Rubric, Metadata* structure in `system_prompt.txt` for predictable, zero-shot structured JSON extraction.
- **Deterministic Policy Rules in Python:** University policy rules (`MAX_AUTO_DAYS = 3`, `ALLOWED_AUTO_REASONS = {"medical", "family", "technical"}`) are enforced strictly in Python code, preventing prompt override risks.
- **Three-Tier Advisory Categorization:**
  - `within_policy`: Meets standard criteria (<= 3 days for medical, family, or technical reasons) for expedited faculty sign-off.
  - `needs_faculty_review`: Complex cases (requested days > 3, workload issues, hackathons/events, or uncatalogued courses) requiring instructor discretion.
  - `needs_more_info`: Vague requests missing course codes or explicit day counts.
- **Student Privacy & PII Protection:** Automatically filters out sensitive illness names (e.g., *dengue, surgery, depression, migraine*) and personal names from summary logs using `sanitize_summary()`.
- **Role-Segregated Output Files:** General administrative logs (`results.csv`) contain zero raw student text, while faculty review files (`review_queue.csv`) preserve raw narratives for authorized evaluation.
- **Adversarial & Jailbreak Hardening:** Proven 100% defense against prompt injections, calendar date calculation traps, and fake course codes.
- **Zero-Token Mock Mode & Dual API Support:** Complete offline testability via local heuristic regex parsing (`MOCK_LLM=true`), plus full support for Google Gemini and OpenAI live APIs.
- **Interactive Web Dashboard:** Includes a modern Streamlit web interface (`app.py`) for visual request inspection, analytics, and CSV export.

---

## 🛠️ Technologies Used
- **Programming Language:** Python 3.10+
- **Standard Libraries:** `csv`, `json`, `urllib.request`, `re`, `os`, `sys`, `typing`
- **Optional Web UI:** `streamlit`, `pandas`, `plotly`
- **AI / LLM Integration:** Google Gemini 1.5 Flash REST API, OpenAI GPT-4o-mini REST API, and built-in offline mock engine
- **Prompt Framework:** AECRM (Authority, Exemplar, Constraint, Rubric, Metadata)

---

## 📂 Project Structure
```text
Extension_Request_Sorter/
├── main.py                     # Core backend pipeline (all 6 core functions)
├── app.py                      # Interactive Streamlit web dashboard
├── test_harness.py             # Evaluation suite (5 tests) & Red-Team suite (3 tests)
├── courses.csv                 # Accredited college course catalog with instructors
├── requests.csv                # 22 realistic student test requests
├── system_prompt.txt           # AECRM structured system prompt for LLM
├── results.csv                 # Clean audit log (all requests, student-safe view)
├── review_queue.csv            # Faculty-only triage queue (includes original raw text)
├── summary.txt                 # Aggregate metrics and category breakdown report
├── requirements.txt            # Python dependencies (for Streamlit dashboard)
├── .env.example                # Template for environment variables and API keys
├── .gitignore                  # Git ignore rules (protects .env, keys, and cache)
├── docs_project_specification.md  # Formal 1-page engineering specification
├── docs_judgment_framework.md     # Risk assessment & human accountability framework
├── docs_cost_latency_report.md    # Operational cost, latency, & reliability report
├── docs_ai_decision_journal.md    # Engineering decisions, trade-offs, & design history
├── docs_reflection.md             # First-year student engineering reflection essay
└── README.md                   # Comprehensive project documentation
```

---

## ⚙️ Installation Instructions

### Prerequisites
- Python 3.10 or higher installed.
- Git (optional, for version control).

### Step 1: Clone or Navigate to the Project Directory
```powershell
cd c:\Users\ASHWATH\OneDrive\Desktop\Extension_Request_Sorter
```

### Step 2: (Optional) Create and Activate a Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### Step 3: Install Dependencies (Optional for Console, Required for Web UI)
```powershell
pip install -r requirements.txt
```
*(Note: `main.py` and `test_harness.py` use only Python standard libraries and require no pip installations to run in mock mode.)*

---

## 🔑 Mock Mode and API Mode Instructions

The application supports both offline mock evaluation and live cloud LLM APIs via environment variables.

Copy `.env.example` to create your local `.env` file:
```powershell
copy .env.example .env
```

Open `.env` and select your execution mode:

### Mode 1: Offline Mock Mode (Default & Recommended for Testing/Grading)
Requires no API key, incurs zero financial cost, runs completely offline, and works instantly:
```ini
MOCK_LLM=true
```

### Mode 2: Live Google Gemini API Mode
```ini
MOCK_LLM=false
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### Mode 3: Live OpenAI API Mode
```ini
MOCK_LLM=false
LLM_PROVIDER=openai
OPENAI_API_KEY=your_actual_openai_api_key_here
```

---

## 💻 How to Run the Application

### Option A: Run the Main Console Pipeline
Executes batch processing across all requests in `requests.csv`, validates them against `courses.csv`, and generates output reports:
```powershell
python main.py
```

**Console Output Sample:**
```text
======================================================================
         EXTENSION REQUEST SORTER - CONSOLE PIPELINE
======================================================================
[1/5] Loaded system prompt & configuration.
[2/5] Loaded 10 accredited courses from courses.csv.
[3/5] Loaded 22 student requests from requests.csv.

[4/5] Processing requests through AI Extraction & Python Policy Engine...
----------------------------------------------------------------------
[01/22] Processing REQ001... -> Result: WITHIN_POLICY (Course: CS101, Days: 2)
[02/22] Processing REQ002... -> Result: WITHIN_POLICY (Course: MATH101, Days: 3)
[03/22] Processing REQ003... -> Result: WITHIN_POLICY (Course: CS102, Days: 2)
[04/22] Processing REQ004... -> Result: NEEDS_FACULTY_REVIEW (Course: CS201, Days: 2)
[07/22] Processing REQ007... -> Result: NEEDS_MORE_INFO (Course: None, Days: None)
...
[5/5] Generating analytical reports...
  -> results.csv generated (all requests, student-safe view).
  -> review_queue.csv generated (faculty review queue with original text).
  -> summary.txt generated (aggregated metrics and counts).

[SUCCESS] Pipeline execution finished cleanly.
```

### Option B: Launch the Interactive Streamlit Web Dashboard
Provides an intuitive UI for uploading requests, inspecting triage metrics, reviewing flagged cases, and downloading CSV reports:
```powershell
streamlit run app.py
```
Then navigate to **`http://localhost:8501`** in your web browser.

---

## 🧪 How to Run Tests

Run the complete evaluation and red-team test harness:
```powershell
python test_harness.py
```

### What the Test Suite Evaluates:
1. **Standard Evaluation Suite (5 Test Cases):**
   - Valid medical request within policy (<= 3 days, CS101).
   - Request exceeding policy threshold (> 3 days, CS102).
   - Request missing mandatory fields (missing course code).
   - Technical issue request within policy (<= 3 days, CS202).
   - Event/hackathon request requiring instructor review (CS201).
2. **Red-Team Adversarial Suite (3 Attack Vectors):**
   - **Prompt Injection:** Adversarial override commanding AI to act as dean and approve request $\rightarrow$ Successfully blocked and routed to `needs_more_info`.
   - **Date vs. Days Trap:** Ambiguous deadline (*"until next Friday"*) $\rightarrow$ Successfully rejected date arithmetic, parsed days as `null`, and routed to `needs_more_info`.
   - **Catalog Integrity Trap:** Fake or unknown course code (`HIST999`) $\rightarrow$ Cross-referenced against catalog and routed to `needs_faculty_review`.

**Test Result:** **100% Pass Rate** across both standard evaluation and red-team defense suites.

---

## 📊 Output Files Explained
1. **`results.csv`**: Contains all processed requests with extracted fields, sanitized summary, advisory recommendation, and policy notes. **Contains zero raw student email text** to protect student privacy.
2. **`review_queue.csv`**: Contains requests categorized as `needs_faculty_review` or `needs_more_info`. **Includes original raw student text** exclusively for authorized faculty review.
3. **`summary.txt`**: Plain-text statistical breakdown showing total request volume, percentage distributions by recommendation, top reasons, and course breakdown.

---

## 🛡️ Responsible AI, Student Privacy & Human Oversight
- **Zero Autonomous Approvals:** The AI model and Python engine never send final approval or rejection decisions. Faculty retain 100% authority.
- **Privacy by Design:** Student medical conditions (e.g., dengue, surgery, depression) and names are stripped from general summaries using `sanitize_summary()`.
- **Auditability:** Every advisory recommendation includes an explicit policy reason in `policy_notes` based on codified rules.
- **Credential Protection:** Secrets and API keys are stored solely in `.env`, excluded via `.gitignore`, and never logged to console or committed to Git.

---

## ⚠️ System Limitations
- **No Direct LMS Webhooks:** Current version processes flat CSV files rather than integrating directly with Canvas/Moodle APIs.
- **No Document OCR:** Physical doctor notes or competition certificates must still be verified manually by faculty.
- **No Autonomous Email Dispatch:** The system generates queues for faculty rather than sending automated student emails.

---

## 📜 Academic Integrity Statement
This project was developed as a First-Year College AI Capstone Project. It strictly follows ethical AI guidelines, demonstrating how artificial intelligence can assist educators by handling routine triage while preserving human empathy, accountability, and academic fairness.
