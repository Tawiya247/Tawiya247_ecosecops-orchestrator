"""core/remediator.py — EcoSecOps Orchestrator remediation utilities.

Provides helpers to patch vulnerable requirements and suggest SCI-based
carbon-reduction optimisations.  No external dependencies — stdlib only.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_fixed_version(vulns: list[dict]) -> Optional[str]:
    """Return the best (highest) fixed version across all vuln entries.

    Args:
        vulns: List of vuln dicts, each optionally containing a
            ``fixed_version`` string.

    Returns:
        The highest fixed version string found, or ``None`` if none exist.
    """
    candidates: list[str] = [
        v["fixed_version"]
        for v in vulns
        if v.get("fixed_version", "")
    ]
    if not candidates:
        return None
    # Use max with a tuple key so "3.10.0" > "3.9.0" works via string sort;
    # for the common semver-like patterns this is sufficient.  A proper
    # version-aware sort would require `packaging`, which is external.
    return max(candidates, key=lambda s: [int(x) if x.isdigit() else x for x in re.split(r"[.\-]", s)])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_requirements(path: str) -> list[dict]:
    """Parse a requirements.txt file into a list of package descriptors.

    Only lines that contain ``==`` and are not comments or blank are returned.

    Args:
        path: Filesystem path to the requirements file.

    Returns:
        A list of dicts with keys:
            - ``name`` (str): Package name as written in the file.
            - ``version`` (str): Pinned version string.
            - ``line`` (str): The original stripped line (used for replacement).

    Raises:
        FileNotFoundError: If *path* does not exist.
    """
    requirements_path = Path(path)
    if not requirements_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {path}")

    packages: list[dict] = []
    for raw_line in requirements_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, _, version = line.partition("==")
        # Strip any trailing extras / environment markers after the version
        version = version.split(";")[0].split(" ")[0].strip()
        packages.append({"name": name.strip(), "version": version, "line": line})
    return packages


def patch_requirements(requirements_path: str, vulnerabilities: list[dict]) -> dict:
    """Patch a requirements.txt file by upgrading vulnerable package versions.

    For every entry in *vulnerabilities* that carries at least one vuln with a
    non-empty ``fixed_version``, the corresponding line in the requirements
    file is rewritten to the highest available fixed version.  Package name
    comparison is case-insensitive.

    Args:
        requirements_path: Filesystem path to the requirements file to patch.
        vulnerabilities: List of vulnerability report dicts as returned by
            ``connectors/osv_client.check_package()``.  Each dict must contain:
            ``name``, ``version``, ``ecosystem``, ``vulns``, ``is_mock``.

    Returns:
        A dict with three keys:
            - ``patched`` (list[dict]): Records of applied patches, each with
              ``name``, ``old_version``, ``new_version``.
            - ``unchanged`` (list[dict]): Records of skipped packages, each
              with ``name`` and ``reason``.
            - ``total_patched`` (int): Number of packages successfully patched.

    Raises:
        FileNotFoundError: If *requirements_path* does not exist.
    """
    req_file = Path(requirements_path)
    if not req_file.exists():
        raise FileNotFoundError(f"Requirements file not found: {requirements_path}")

    content = req_file.read_text(encoding="utf-8")

    patched: list[dict] = []
    unchanged: list[dict] = []

    for vuln_report in vulnerabilities:
        pkg_name: str = vuln_report["name"]
        pkg_version: str = vuln_report["version"]
        vulns: list[dict] = vuln_report.get("vulns", [])

        fixed_version = _get_fixed_version(vulns)

        if fixed_version is None:
            unchanged.append({
                "name": pkg_name,
                "reason": "no fixed_version available in vulnerability data",
            })
            continue

        if fixed_version == pkg_version:
            unchanged.append({
                "name": pkg_name,
                "reason": f"current version {pkg_version} already matches fixed version",
            })
            continue

        # Build a case-insensitive regex that matches the pinned requirement
        # line (handles both exact-case and mixed-case package names).
        pattern = re.compile(
            r"(?i)(^[ \t]*)" + re.escape(pkg_name) + r"(==)" + re.escape(pkg_version),
            re.MULTILINE,
        )

        new_content, count = pattern.subn(
            lambda m: m.group(1) + pkg_name + "==" + fixed_version,
            content,
        )

        if count == 0:
            unchanged.append({
                "name": pkg_name,
                "reason": (
                    f"package {pkg_name}=={pkg_version} not found in "
                    f"{requirements_path}"
                ),
            })
            continue

        content = new_content
        patched.append({
            "name": pkg_name,
            "old_version": pkg_version,
            "new_version": fixed_version,
        })

    req_file.write_text(content, encoding="utf-8")

    return {
        "patched": patched,
        "unchanged": unchanged,
        "total_patched": len(patched),
    }


def suggest_optimizations(sci_score: float) -> list[str]:
    """Return textual optimisation recommendations based on a SCI score.

    The Software Carbon Intensity (SCI) score determines the severity of the
    recommendations returned:

    * ``SCI < 0.1``  → excellent, positive feedback only.
    * ``0.1 ≤ SCI < 0.5`` → moderate recommendations.
    * ``SCI ≥ 0.5``  → urgent, high-impact recommendations.

    Args:
        sci_score: The computed SCI score (dimensionless, typically 0–1+).

    Returns:
        A list of English-language recommendation strings.
    """
    if sci_score < 0.1:
        return [
            "SCI score is excellent — no optimisation required.",
            "Keep up the good work: your workload already runs with minimal carbon intensity.",
        ]
    elif sci_score < 0.5:
        return [
            "Reduce unnecessary API or network requests by introducing a short-lived in-memory cache.",
            "Batch database writes to avoid repeated small transactions and lower I/O energy.",
            "Profile hot code paths and eliminate redundant computation to trim CPU cycles.",
        ]
    else:
        return [
            "URGENT: Migrate workloads to a cloud region powered by low-carbon or renewable energy.",
            "Optimise CPU-intensive loops — consider vectorisation or offloading to more efficient runtimes.",
            "Schedule non-interactive batch jobs during off-peak hours when the grid carbon intensity is lower.",
            "Reduce container image sizes and startup times to cut per-invocation energy overhead.",
            "Implement auto-scaling policies that scale down aggressively during low-traffic periods.",
        ]
