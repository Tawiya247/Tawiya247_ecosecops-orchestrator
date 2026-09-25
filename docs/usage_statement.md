# Usage Statement — EcoSecOps Orchestrator

**Hackathon IBM Bob 2.0 | lablab.ai**

---

## Who Uses EcoSecOps Orchestrator

EcoSecOps Orchestrator is designed for **DevSecOps engineers**, **platform teams**, and **engineering leads** who are responsible for both the security posture and the operational sustainability of Python-based applications. It is equally relevant to **GreenOps practitioners** who need a concrete, code-level entry point for carbon measurement — beyond infrastructure-level metrics.

---

## How It Is Used

### Typical Workflow

**1. Audit** — A developer or CI pipeline triggers a security and carbon audit by sending the path of a `requirements.txt` file to `POST /api/audit`. In under two seconds, the system:
- Checks every pinned dependency against OSV.dev for known CVEs
- Retrieves live grid carbon intensity from ElectricityMaps (or uses the mock fallback if offline)
- Computes the Software Carbon Intensity (SCI) score for the workload
- Ranks every vulnerable package by its SPSC (Security-Carbon Priority Score)

**2. Prioritise** — The SPSC score tells the engineer which vulnerability to fix **first**, not just which is most severe in isolation. A CVSS=7 package running in a high-carbon region under peak CPU load may outrank a CVSS=9 package in a low-carbon environment at idle. This context-aware ranking directly reduces MTTR.

**3. Remediate** — Clicking "Exécuter la remédiation" in the Streamlit dashboard (or calling `POST /api/remediate`) automatically rewrites the vulnerable `requirements.txt` lines with the OSV-recommended fixed versions. The response includes a full diff of what changed and what could not be patched (with the reason).

**4. Optimise** — The system generates ranked carbon-reduction recommendations calibrated to the measured SCI score. Teams with SCI ≥ 0.5 receive urgent infrastructure migration advice; teams with SCI < 0.1 receive positive confirmation that their workload is already carbon-efficient.

---

## Concrete Use Cases

| User | Scenario | Outcome |
|---|---|---|
| DevSecOps engineer | Pre-merge dependency audit in CI/CD | Catches CVEs before they reach production; SCI score committed alongside code coverage |
| Platform team | Weekly GreenOps review | Tracks SCI trends across services; identifies which services to migrate to low-carbon regions |
| Engineering lead | Sprint planning | Uses SPSC ranking to allocate remediation tickets with combined security + carbon ROI |
| Security auditor | Point-in-time assessment | Exports audit JSON for compliance reporting under CSRD or EU Cyber Resilience Act |

---

## Offline and Mock-Safe Operation

EcoSecOps Orchestrator is designed to work with **zero external dependencies** in test and air-gapped environments:
- No ElectricityMaps API key? → mock returns `210 gCO₂e/kWh` with a visible `🔸 MOCK` badge in the dashboard
- OSV.dev unreachable? → mock returns a canonical jinja2==2.11.2 vulnerability (CVSS=7.5) to demonstrate the full pipeline
- All tests run fully offline via `respx` HTTP mocks — no real API calls in the test suite

This design ensures the system is **always demo-able**, regardless of network conditions — a critical property for a hackathon submission.

---

## Impact Metrics

| Metric | Before | After (EcoSecOps) |
|---|---|---|
| Time to identify vulnerable packages | Manual audit: hours | Automated: < 2 seconds |
| Remediation prioritisation | CVSS-only ranking | SPSC: security + carbon + CPU |
| Carbon footprint visibility | Zero (not measured) | SCI score per workload, per run |
| Patch application | Manual version bump + PR | Automated rewrite of `requirements.txt` |

---

*Built with IBM Bob 2.0 — Hackathon IBM Bob 2.0*
