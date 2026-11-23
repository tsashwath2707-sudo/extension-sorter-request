# Extension Request Sorter — Presentation Speaking Script

**Presentation Title:** Extension Request Sorter: AI Academic Workflow Assistant  
**Target Duration:** Exactly 10 Minutes  
**Format:** Slide-by-slide verbal script designed for a first-year college student presentation.

---

### Slide 1: Title & Introduction (Duration: ~1:00 min)
*"Good morning respected tutors and evaluators. My name is Ashwath, and today I am excited to present my first-year AI capstone project: the **Extension Request Sorter**.*

*At universities, handling assignment extensions is a massive administrative headache. My project addresses this challenge using an AI-assisted workflow. But right from the beginning, I want to emphasize the core philosophy of this project: **artificial intelligence is used strictly as an intake triage assistant, and it never makes final decisions**. In our system, human faculty retain 100% final authority. Today, I will walk you through our architecture, testing, privacy safeguards, and real project results."*

---

### Slide 2: Problem Statement & Motivation (Duration: ~1:00 min)
*"Let us begin with the problem. During midterm and finals weeks, professors and teaching assistants get bombarded with dozens of extension request emails. In practice, these emails create three major problems:*

*First, students write in free-form text. Some forget to mention the course code, some give vague reasons, and many write ambiguous dates like 'Can I submit next Friday?' without stating how many days they actually need.*

*Second, professors spend precious teaching hours reading routine requests, calculating days, and verifying course codes.*

*Third, student emails often contain personal and sensitive medical details, like specific surgeries or diagnoses. If these emails are forwarded around general teaching assistants, it creates serious privacy concerns.*

*Our goal was to build a clean, automated software pipeline that parses these requests, validates them against university rules, and organizes them for faculty review."*

---

### Slide 3: Project Objectives & Core Principles (Duration: ~1:00 min)
*"To solve this problem responsibly, I established three technical objectives and one non-negotiable safety principle:*

*Objective 1 was **Reliable Extraction**: Converting messy student emails into structured JSON data.*

*Objective 2 was **Deterministic Policy Enforcement**: Applying college extension rules consistently in code, rather than letting an AI guess.*

*Objective 3 was **Student Privacy Protection**: Redacting personal names and specific medical conditions from general summaries.*

*And our Golden Safety Principle: **The AI must never automatically approve or reject any request**. Instead, the system acts as an intelligent sorting assistant that categorizes requests into advisory queues so professors can make fast, well-informed, and compassionate decisions."*

---

### Slide 4: System Architecture & Technologies Used (Duration: ~1:30 min)
*"Now let us look at the technical architecture. Rather than relying on a single large language model to do everything, I designed a **decoupled hybrid architecture** with two distinct layers:*

*The first layer is the **AI Extraction Layer**. We use an AECRM-engineered system prompt—standing for Authority, Exemplar, Constraint, Rubric, and Metadata. The AI reads the student email and extracts four clean JSON fields: course code, days requested, standardized reason category, and a brief summary. The system supports live APIs like Google Gemini 1.5 Flash and OpenAI GPT-4o-mini, but it also includes a complete offline mock engine for zero-cost testing.*

*The second layer is the **Deterministic Python Engine**. This is where true safety lives. Python verifies that the course exists in our official `courses.csv` catalog, checks that the days requested are within the valid range of 1 to 30, and confirms that the number actually appeared in the student's text. Python also applies our privacy filter to ensure summaries never leak private health disclosures.*

*Finally, Python applies policy rules and produces segregated reports: a student-safe `results.csv`, a faculty-only `review_queue.csv`, a statistical `summary.txt`, and an interactive Streamlit web dashboard in `app.py`."*

---

### Slide 5: How the Application Works (Walkthrough) (Duration: ~1:30 min)
*"Let us examine how the application actually works in practice.*

*In the console mode, running `python main.py` loads the active course catalog from `courses.csv` and reads incoming student requests from `requests.csv`. Each request is parsed, sanitized, validated, and categorized.*

*We also built an interactive web dashboard using Streamlit. When faculty open the dashboard, they see executive KPI cards displaying total requests, requests within policy, and requests needing review. They get interactive Plotly charts showing breakdown by reason and course, and they can search, filter, and download the review queue directly.*

*In our benchmark dataset of 22 realistic student requests: 40.9% were sorted into 'within policy', 36.4% were flagged for faculty review, and 22.7% were flagged as needing more information. The pipeline runs end-to-end locally in less than 0.1 seconds in mock mode, producing clean audit logs."*

---

### Slide 6: Policy Rules & Recommendation Logic (Duration: ~1:00 min)
*"How does the system decide where a request belongs? The logic is completely transparent and handled in pure Python code:*

*First, if a student forgets the course code, or gives an ambiguous date instead of days, Rule 1 categorizes it as **`needs_more_info`**. The system prompts the student to clarify.*

*Second, if a course code is not in our approved catalog, Rule 2 sends it to **`needs_faculty_review`** for an administrative check.*

*Third, if the request is 3 days or fewer, and the reason is medical, family emergency, or a technical issue, Rule 3 classifies it as **`within_policy`**. This flags it for expedited professor sign-off.*

*Finally, if the student asks for more than 3 days, or cites workload overload or a hackathon event, Rule 4 routes it to **`needs_faculty_review`**. Extracurricular events and heavy workloads require personal teacher judgment, not an automated rule."*

---

### Slide 7: Evaluation & Red-Team Testing Results (Duration: ~1:30 min)
*"To prove that this system is robust and secure, I developed a comprehensive test harness in `test_harness.py`.*

*Part 1 is the **Standard Evaluation Suite** with 5 test cases covering valid medical requests, requests exceeding 3 days, missing course codes, technical issues, and hackathon events. Our test harness achieved a **100% pass rate**.*

*Part 2 is the **Red-Team Security Suite**, where I attacked the system with adversarial inputs:*
- *First, a **Prompt Injection Attack**, where a student pretended to be an administrator and commanded the AI to override rules and approve the request. The system neutralized the attack, ignored the override, and routed it to `needs_more_info`.*
- *Second, a **Date Calculation Trap**, where a student asked for an extension 'until next Friday'. Our prompt and code strictly forbid date arithmetic because models do not know current semester dates. It parsed days as null and routed to `needs_more_info`.*
- *Third, an **Uncatalogued Course Trap**, where a student requested an extension for fake course `HIST999`. Python caught that it wasn't in `courses.csv` and flagged it for faculty review.*

*Our red-team defense rate was **100%**, proving that decoupling the AI from Python policy creates genuine software resilience."*

---

### Slide 8: Student Privacy & Responsible AI Safeguards (Duration: ~1:00 min)
*"One of the most important aspects of this project is responsible AI and student privacy.*

*Medical disclosures are private. In our system, the function `sanitize_summary()` scans for sensitive diagnostic terms—like dengue, surgery, depression, or doctor names—and replaces them with generic statements like 'Requests 2 days for CS101, medical reason'.*

*Furthermore, we strictly segregate our files. General staff only see `results.csv`, which has zero raw student text. Only authorized faculty have access to `review_queue.csv`, which preserves the original student message so professors have full context when making sensitive decisions.*

*Every recommendation also comes with an automated `policy_notes` audit trail, ensuring complete transparency."*

---

### Slide 9: Limitations, Future Work & Conclusion (Duration: ~0:30 min)
*"In conclusion, while our project works cleanly, it has realistic limitations. It currently operates on CSV files rather than live Canvas LMS webhooks, and it does not perform automated OCR on physical doctor notes.*

*In the future, I plan to integrate Canvas API webhooks, automated student reply emails, and document verification.*

*Through this capstone project, I learned that building great AI software isn't about giving an algorithm full control. It's about building secure, reliable guardrails where AI takes care of routine parsing, while human educators remain in charge.*

*Thank you very much. I am now ready for your questions!"*
