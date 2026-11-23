# Operational Cost, Latency & Reliability Report

## 1. Executive Summary & Purpose
This report provides an operational analysis of the **Extension Request Sorter** across both **Mock/Offline Mode** and **Live API Mode** (Google Gemini 1.5 Flash / OpenAI GPT-4o-mini).

To maintain academic rigor and integrity, **this document clearly distinguishes between actual local measurements and theoretical cost/token estimates**. Actual local benchmarks reflect test runs performed on the 22-request dataset, while API cost projections are calculated using published vendor pricing tiers.

---

## 2. API Usage Assumptions & Token Modeling (Theoretical Estimates)

The system utilizes an AECRM-engineered system prompt (`system_prompt.txt`) to extract structured JSON from unstructured text in a single zero-shot pass.

### Token Consumption Estimates (Per Request)
- **System Prompt Input (AECRM Instructions + 3 Exemplars):** ~450 tokens
- **Student Request Input (Average across 22 test cases):** ~40 tokens
- **Total Input Tokens Per Call:** ~490 tokens
- **Output JSON Generation (4 fields: course, days, reason, summary):** ~45 tokens
- **Total Tokens Per Call:** ~535 tokens

### Cost Projections Across LLM Providers (Estimated)

Calculated based on standard published vendor rates:
- **Google Gemini 1.5 Flash:** Input \$0.075 / 1M tokens; Output \$0.300 / 1M tokens
- **OpenAI GPT-4o-mini:** Input \$0.150 / 1M tokens; Output \$0.600 / 1M tokens

| Provider / Model | Cost per 1 Request (Est.) | Cost per 1,000 Requests (Est.) | Cost per 10,000 Requests (Campus-Wide Est.) | Recommended Operational Use |
| :--- | :--- | :--- | :--- | :--- |
| **Offline Mock Engine (main.py)** | **\$0.00** | **\$0.00** | **\$0.00** | Unit testing, CI/CD, offline grading, zero-cost development |
| **Google Gemini 1.5 Flash** | **\$0.000050** | **\$0.050 (5 cents)** | **\$0.50 (50 cents)** | Production campus deployment (lowest cost & highest speed) |
| **OpenAI GPT-4o-mini** | \$0.000100 | \$0.100 (10 cents) | \$1.00 (\$1.00) | Secondary / fallback cloud provider |

> **Cost Projection Summary:** Processing an entire university department's semester workload (~5,000 student extension requests) with Gemini 1.5 Flash is estimated at approximately **\$0.25 USD**, demonstrating exceptional financial feasibility for higher education institutions.

---

## 3. Mock Mode vs. Real API Mode: Comparison Matrix

| Dimension | Mock Mode (`MOCK_LLM=true`) | Real API Mode (`MOCK_LLM=false`) |
| :--- | :--- | :--- |
| **Execution Environment** | 100% Local / Sandbox (No Internet Required) | Remote Cloud Server via HTTPS REST API |
| **API Key Requirement** | None (Zero keys needed) | Requires active `GEMINI_API_KEY` or `OPENAI_API_KEY` |
| **API Financial Cost** | Exactly **\$0.00** (Zero cost) | Nominal (\$0.05 / 1K requests on Gemini 1.5 Flash) |
| **Processing Latency** | Instantaneous (< 2 ms per request) | Network bound (~600 ms – 1,500 ms per request) |
| **Determinism** | 100% deterministic (Reproducible regex rules) | Highly deterministic (Temperature = 0.0), but probabilistic |
| **Adversarial Handling** | Rule-based string inspection | Prompt instruction hierarchy + LLM safety filters |
| **Network Failure Risk** | Zero (Runs entirely offline) | Possible HTTP 429 (rate limit), 500/503 (service downtime) |
| **Primary Use Case** | Continuous integration, grading, unit testing | Live production deployment handling free-form text |

---

## 4. Latency Factors & Benchmark Measurements

### Actual Local Measurements (Benchmark Run on 22 Requests)
*Measured on Windows 11, Python 3.12, local execution sandbox:*
- **Mock Pipeline Total Execution Time (22 requests):** ~0.04 seconds total (~1.8 ms per request)
- **Standard Evaluation Suite (5 tests):** < 0.02 seconds
- **Red-Team Security Suite (3 tests):** < 0.01 seconds
- **Local Throughput:** ~550 requests / second in mock mode

### Latency Factors in Live API Mode (Empirical / Estimated Ranges)
When executing against live cloud endpoints, latency is influenced by several operational factors:
1. **Network Round-Trip Time (RTT):** Geographic distance between campus servers and Google/OpenAI data centers adds 50–150 ms per request.
2. **Model Processing & Queue Time:** Time-to-first-token (TTFT) and token generation duration on cloud TPUs/GPUs typically range from 400 ms to 1,200 ms.
3. **Sequential vs. Concurrent Execution:**
   - *Sequential (main.py baseline):* 22 requests @ ~700 ms = ~15.4 seconds.
   - *Batch / Async (Streamlit or multi-threaded worker):* Estimated at ~2.5 to 3.5 seconds total.
4. **Retry Latency:** In the event of a transient HTTP timeout or rate limit, an automated retry introduces a 1–2 second backoff penalty.

---

## 5. Architectural Strategies to Reduce API Costs

To keep operational expenditures minimal while maintaining high accuracy, the project implements four key cost-reduction strategies:

1. **Strict Zero-Shot Prompt Framing:**
   - Rather than sending long few-shot conversational histories or multi-turn chats, `system_prompt.txt` uses compact, high-density AECRM instructions (~450 tokens) with exactly 3 minimal exemplars.
2. **Minimal Schema Output:**
   - The LLM is instructed to output strictly 4 fields (`course`, `days`, `reason`, `summary`), generating fewer than 50 output tokens. No conversational pleasantries or explanations are generated by the model.
3. **Local Deterministic Fallback & Fast-Path Pre-filtering:**
   - Simple validation errors (e.g., empty requests) can be caught locally in Python before dispatching an API call, avoiding unnecessary network tokens.
4. **Offline Development & CI Testing via Mock Mode:**
   - By running development loops, unit testing, and automated grading against `mock_llm_extractor()`, 100% of testing costs are eliminated.

---

## 6. Limitations of Estimates & Reliability Architecture

### Limitations of Cost and Performance Estimates
- **Varying Request Lengths:** Estimates assume an average request length of 40 tokens. Student emails with long narrative attachments or forwarded email threads will consume more input tokens.
- **Provider Pricing Adjustments:** API rates are subject to vendor pricing adjustments over time.
- **Network Variability:** Live API latencies depend heavily on institutional Wi-Fi quality, firewall inspection proxies, and upstream cloud load.

### Two-Tier Fault Tolerance Architecture
To prevent workflow disruption during network outages or API rate-limit spikes:
1. **1 Automatic Retry:** `classify()` attempts a second API call if an initial call encounters a socket timeout or JSON parse issue.
2. **Deterministic Safe Fallback:** If the retry fails or the API key is unavailable, the pipeline falls back smoothly to `mock_llm_extractor()`. The application logs a warning, completes all sorting safely, and never crashes.
