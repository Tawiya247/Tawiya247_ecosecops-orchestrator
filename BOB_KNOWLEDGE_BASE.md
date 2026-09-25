IBM BOB 2.0 MASTER KNOWLEDGE BASE & SYSTEM DIRECTIVES
Project: EcoSecOps Orchestrator
Event: IBM Bob 2.0 Hackathon (lablab.ai & IBM)
Purpose: Full offline specification context for autonomous execution

1. HACKATHON CONTEXT, CONSTRAINTS & RULES
Rules & Deliverables
Platform & Repository: Must build on a public GitHub repository generated from the official IBM template.   

Security First: Failsafe protection against secret leakage. Files .env, *.key, credentials.json MUST be listed in .gitignore and .bobignore.   

Deliverables Required for Submission:

Working GitHub repository with clean code and tests.

Screenshots of IBM Bob 2.0 session summaries.

3-minute demo video (at least 90 seconds showing IBM Bob 2.0 actively refactoring and planning).

Written problem & usage statements (< 500 words each).

Judging Criteria (25% Each)
Technology Application: Advanced usage of Bob's features (/init, plan, advanced, orchestrator, subagents, multi-file code editing).   

Originality: Combining Open Source Cybersecurity (OSV) with GreenOps Software Carbon Intensity (ISO/IEC 21031:2024).

Business Value: Measurable reduction in Mean Time To Remediate (MTTR) and energy footprint (SCI).

Presentation & Quality: Clean modular architecture, docstrings, type hints, and unit test coverage.

2. API CONTRACTS & SCHEMAS (OFFLINE REFERENCE)
Since internet access is disabled, Bob must implement robust HTTP clients that use the official schemas below when connected, and gracefully fall back to mock data when API keys or network are unavailable.

A. OSV.dev API (Open Source Vulnerabilities)
Protocol: HTTP POST

Endpoint: [https://api.osv.dev/v1/query](https://api.osv.dev/v1/query)

Purpose: Check package dependency vulnerabilities.

Request Payload Schema (JSON):json
{
"package": {
"name": "jinja2",
"ecosystem": "PyPI"
},
"version": "2.11.2"
}


Expected Response Schema (JSON):
```json
{
  "vulns": [
    {
      "id": "GHSA-fe52-489u-72pt",
      "summary": "HTML injection in Jinja2",
      "details": "Jinja2 before 2.11.3 allows HTML injection...",
      "severity": [
        {
          "type": "CVSS_V3",
          "score": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:N"
        }
      ],
      "affected": [
        {
          "package": {
            "name": "jinja2",
            "ecosystem": "PyPI"
          },
          "ranges": [
            {
              "type": "ECOSYSTEM",
              "events": [
                { "introduced": "0" },
                { "fixed": "2.11.3" }
              ]
            }
          ]
        }
      ]
    }
  ]
}
Mock Fallback (Required in connectors/osv_client.py):
If network call fails, return a simulated vulnerability for jinja2==2.11.2 with CVSS score 7.5 and fixed version 2.11.3.

B. ElectricityMaps API (Grid Carbon Intensity)
Protocol: HTTP GET

Endpoint: https://api.electricitymap.org/v3/carbon-intensity/latest?zone=US-NY

Headers: auth-token: <API_KEY>

Purpose: Retrieve real-time grid carbon emissions (gCO 
2
​
 e/kWh).

Expected Response Schema (JSON):

JSON
{
  "zone": "US-NY",
  "carbonIntensity": 240,
  "datetime": "2026-09-25T15:00:00.000Z",
  "updatedAt": "2026-09-25T14:50:00.000Z",
  "emissionFactorType": "lifecycle",
  "isEstimated": false,
  "estimationMethod": "TIME_SLIDER"
}
Mock Fallback (Required in connectors/electricity_client.py):
If auth-token is missing or call fails, return {"zone": "US-NY", "carbonIntensity": 210, "isMock": true}.

3. MATHEMATICAL ENGINES & FORMULAS
A. Software Carbon Intensity (SCI) - ISO/IEC 21031:2024
Implement in core/metrics.py:

SCI= 
R
(E⋅I)+M
​
 
Where:

E: Operational energy consumption in kWh (E=Runtime in hours×CPU Watts/1000).

I: Live grid carbon intensity in gCO 
2
​
 e/kWh (from ElectricityMaps API).

M: Embodied carbon of hardware (default static estimate: 0.05 gCO 
2
​
 e).

R: Functional unit (e.g., 1 API Request or 1 Execution).

B. Security-Carbon Priority Score (SPSC)
Implement in core/metrics.py:

SPSC=α⋅CVSS+β⋅( 
I 
r 
e
ˊ
 f 
e
ˊ
 rence
​
 
I 
actuel
​
 
​
 )+γ⋅U 
CPU
​
 
Parameters:

CVSS: Base vulnerability score from OSV (0.0 to 10.0).

I 
actuel
​
 : Current grid carbon intensity.

I 
r 
e
ˊ
 f 
e
ˊ
 rence
​
 : Baseline grid carbon intensity (e.g., 300 gCO 
2
​
 e/kWh).

U 
CPU
​
 : Normalized CPU utilization ratio (0.0 to 1.0).

Weights: α=0.5, β=0.3, γ=0.2.

4. TARGET REPOSITORY ARCHITECTURE
Plaintext
ecosecops-orchestrator/
├── .gitignore
├── .bobignore
├── README.md
├── requirements.txt
├── backend/
│   ├── __init__.py
│   ├── main.py
│   └── config.py
├── connectors/
│   ├── __init__.py
│   ├── osv_client.py
│   └── electricity_client.py
├── core/
│   ├── __init__.py
│   ├── metrics.py
│   └── remediator.py
├── frontend/
│   └── app.py
└── tests/
    ├── __init__.py
    ├── test_connectors.py
    └── test_metrics.py
5. STEP-BY-STEP WORKFLOW FOR IBM BOB 2.0
Step 1: Initial Context Scanning
Run /init to scan repository dependencies and establish codebase understanding.

Step 2: Safety & Environment Setup
Verify .gitignore and .bobignore contain .env, *.log, __pycache__/, *.key.

Step 3: Implement Connectors (connectors/)
Write osv_client.py: Asynchronous client parsing requirements.txt, making POST requests to OSV.dev, handling exceptions with mock fallbacks.

Write electricity_client.py: Asynchronous client fetching gCO 
2
​
 e/kWh, handling missing tokens with mock fallbacks.

Step 4: Implement Core Math (core/metrics.py)
Write calculate_sci() and calculate_spsc() adhering to the mathematical formulas above.

Step 5: Implement Remediation Engine (core/remediator.py)
Write AST/regex utilities to patch vulnerable dependency versions in requirements.txt and suggest carbon-efficient code refactoring.

Step 6: FastAPI Backend (backend/main.py)
Expose API endpoints:

GET /health

POST /api/audit (Scans repo, calculates SCI and SPSC)

POST /api/remediate (Applies security patches & optimization)

Step 7: Streamlit Dashboard (frontend/app.py)
Build an interactive UI showing live SCI score, detected CVEs, carbon intensity, and an "Execute Remediation" button.

Step 8: Validation & Automated Testing (tests/)
Write Pytest unit tests in test_connectors.py and test_metrics.py ensuring >80% code coverage.


---

### Comment utiliser ce document avec IBM Bob 2.0 ?
1. Enregistrez ce bloc dans un fichier nommé `BOB_KNOWLEDGE_BASE.md` à la racine de votre dépôt.
2. Dans l'IDE, ouvrez l'extension **IBM Bob 2.0**.
3. Tapez `/init` pour lui faire lire le dépôt.
4. Passez en mode **`plan`** ou **`advanced`** et envoyez le message :
   > *"Lis le fichier `BOB_KNOWLEDGE_BASE.md`. Il contient l'ensemble du contexte hors-ligne, des schémas d'API et des règles du Hackathon. Exécute le Step 2 et le Step 3 du Workflow en générant les fichiers dans `connectors/`."* [cite: 1, 2, 3]