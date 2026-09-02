"""
M2F.2 — Real World Domain Validation Campaign
==============================================

Validates the full intelligence pipeline against 28 real domains across 7 categories.
Executes live DNS lookups, collects pipeline output, and writes a structured markdown report.

Run from: app/backend/
Usage: python scripts/m2f2_validation_campaign.py

Console output is intentionally ASCII-only to avoid UnicodeEncodeError on Windows
consoles that default to cp1252 / cp850.  All emoji are confined to the UTF-8
markdown report that is written directly to disk.
"""

import sys
import os
import json
import time
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# ASCII-safe console logger  (no emoji, no Unicode > 127 in output)
# ---------------------------------------------------------------------------

def safe_print(*args, end="\n", flush=False):
    """Print to stdout using ASCII-only encoding with replace fallback."""
    text = " ".join(str(a) for a in args)
    safe = text.encode("ascii", errors="replace").decode("ascii")
    print(safe, end=end, flush=flush)


# Add app/backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.analysis.dns.resolver import DNSResolver
from domains.analysis.validators.spf import SPFValidator
from domains.analysis.validators.dkim import DKIMValidator
from domains.analysis.validators.dmarc import DMARCValidator
from domains.analysis.aggregator.aggregator import AnalysisAggregator
from core.orchestrator import IntelligenceOrchestrator


# ---------------------------------------------------------------------------
# Domain Test Matrix  (28 domains across 7 categories)
# ---------------------------------------------------------------------------

DOMAIN_MATRIX = [
    # ─── CATEGORY 1: EXCELLENT ─────────────────────────────────────────────
    {"domain": "google.com",      "selector": "google",    "category": "Excellent",
     "expected_band": ["EXCELLENT", "GOOD"],   "expected_no": [],
     "notes": "Google — canonical best-practice reference domain"},
    {"domain": "microsoft.com",   "selector": "selector1", "category": "Excellent",
     "expected_band": ["EXCELLENT", "GOOD"],   "expected_no": [],
     "notes": "Microsoft — enterprise email infrastructure"},
    {"domain": "cloudflare.com",  "selector": "google",    "category": "Excellent",
     "expected_band": ["EXCELLENT", "GOOD"],   "expected_no": [],
     "notes": "Cloudflare — infrastructure company, strong auth expected"},
    {"domain": "github.com",      "selector": "google",    "category": "Excellent",
     "expected_band": ["EXCELLENT", "GOOD"],   "expected_no": [],
     "notes": "GitHub — developer platform, full auth expected"},
    {"domain": "stripe.com",      "selector": "google",    "category": "Excellent",
     "expected_band": ["EXCELLENT", "GOOD"],   "expected_no": [],
     "notes": "Stripe — fintech, PCI/compliance drives strong email security"},

    # ─── CATEGORY 2: GOOD ──────────────────────────────────────────────────
    {"domain": "apple.com",       "selector": "apple",     "category": "Good",
     "expected_band": ["EXCELLENT", "GOOD", "AT_RISK"], "expected_no": [],
     "notes": "Apple — large enterprise, good auth expected"},
    {"domain": "amazon.com",      "selector": "google",    "category": "Good",
     "expected_band": ["EXCELLENT", "GOOD", "AT_RISK"], "expected_no": [],
     "notes": "Amazon — major e-commerce, DKIM selector varies"},
    {"domain": "shopify.com",     "selector": "google",    "category": "Good",
     "expected_band": ["EXCELLENT", "GOOD", "AT_RISK"], "expected_no": [],
     "notes": "Shopify — modern SaaS e-commerce"},
    {"domain": "notion.so",       "selector": "google",    "category": "Good",
     "expected_band": ["EXCELLENT", "GOOD", "AT_RISK"], "expected_no": [],
     "notes": "Notion — SaaS, Google Workspace likely"},
    {"domain": "figma.com",       "selector": "google",    "category": "Good",
     "expected_band": ["EXCELLENT", "GOOD", "AT_RISK"], "expected_no": [],
     "notes": "Figma — design SaaS, likely uses Google Workspace"},

    # ─── CATEGORY 3: DMARC p=none (monitoring only) ────────────────────────
    {"domain": "reddit.com",      "selector": "google",    "category": "DMARC p=none",
     "expected_band": ["GOOD", "AT_RISK", "POOR"], "expected_no": ["BIZ-015"],
     "notes": "Reddit — historically p=none DMARC"},
    {"domain": "wikipedia.org",   "selector": "wikimedia", "category": "DMARC p=none",
     "expected_band": ["AT_RISK", "POOR", "GOOD", "CRITICAL"], "expected_no": [],
     "notes": "Wikipedia — nonprofit, may have p=none"},
    {"domain": "twitch.tv",       "selector": "google",    "category": "DMARC p=none",
     "expected_band": ["GOOD", "AT_RISK", "POOR"], "expected_no": [],
     "notes": "Twitch — gaming platform, DMARC enforcement partial"},
    {"domain": "discord.com",     "selector": "google",    "category": "DMARC p=none",
     "expected_band": ["EXCELLENT", "GOOD", "AT_RISK"], "expected_no": [],
     "notes": "Discord — modern SaaS, DMARC status varies"},

    # ─── CATEGORY 4: MISSING DMARC ─────────────────────────────────────────
    {"domain": "bbc.co.uk",       "selector": "google",    "category": "Missing DMARC",
     "expected_band": ["AT_RISK", "POOR", "CRITICAL", "GOOD"], "expected_no": ["BIZ-015"],
     "notes": "BBC UK — news org, DMARC gaps common in media"},
    {"domain": "archive.org",     "selector": "google",    "category": "Missing DMARC",
     "expected_band": ["AT_RISK", "POOR", "CRITICAL"], "expected_no": ["BIZ-015"],
     "notes": "Internet Archive — nonprofit, may lack DMARC"},
    {"domain": "craigslist.org",  "selector": "google",    "category": "Missing DMARC",
     "expected_band": ["POOR", "CRITICAL", "AT_RISK"], "expected_no": ["BIZ-015"],
     "notes": "Craigslist — legacy system, expected weak email security"},
    {"domain": "sourceforge.net", "selector": "google",    "category": "Missing DMARC",
     "expected_band": ["AT_RISK", "POOR", "CRITICAL"], "expected_no": ["BIZ-015"],
     "notes": "SourceForge — legacy platform, email security gap likely"},

    # ─── CATEGORY 5: WEAK SPF / SPF ISSUES ────────────────────────────────
    {"domain": "aol.com",         "selector": "google",    "category": "Weak SPF",
     "expected_band": ["AT_RISK", "POOR", "CRITICAL", "GOOD"], "expected_no": [],
     "notes": "AOL — legacy provider, SPF complexity expected"},
    {"domain": "hotmail.com",     "selector": "google",    "category": "Weak SPF",
     "expected_band": ["AT_RISK", "POOR", "GOOD", "EXCELLENT"], "expected_no": [],
     "notes": "Hotmail — legacy domain, may use complex SPF chains"},
    {"domain": "protonmail.com",  "selector": "google",    "category": "Weak SPF",
     "expected_band": ["GOOD", "AT_RISK", "EXCELLENT"], "expected_no": [],
     "notes": "ProtonMail — privacy-focused, may have custom SPF"},

    # ─── CATEGORY 6: MISSING DKIM ─────────────────────────────────────────
    {"domain": "php.net",         "selector": "google",    "category": "Missing DKIM",
     "expected_band": ["AT_RISK", "POOR", "CRITICAL"], "expected_no": ["BIZ-015"],
     "notes": "php.net — OSS project, likely no Google DKIM selector"},
    {"domain": "kernel.org",      "selector": "google",    "category": "Missing DKIM",
     "expected_band": ["AT_RISK", "POOR", "CRITICAL"], "expected_no": ["BIZ-015"],
     "notes": "Linux kernel — OSS project, custom mail infra expected"},
    {"domain": "apache.org",      "selector": "google",    "category": "Missing DKIM",
     "expected_band": ["AT_RISK", "POOR", "CRITICAL"], "expected_no": ["BIZ-015"],
     "notes": "Apache foundation — custom mail servers, no Google DKIM"},
    {"domain": "gnu.org",         "selector": "google",    "category": "Missing DKIM",
     "expected_band": ["AT_RISK", "POOR", "CRITICAL"], "expected_no": ["BIZ-015"],
     "notes": "GNU project — independent mail infra, DKIM unlikely with google selector"},

    # ─── CATEGORY 7: INVALID / NON-EXISTENT DOMAINS ──────────────────────
    {"domain": "thisdoesnotexist-abc-xyz-999.com",  "selector": None, "category": "Invalid",
     "expected_band": ["POOR", "CRITICAL"], "expected_no": ["BIZ-015"],
     "notes": "Non-existent domain — should get CRITICAL scores"},
    {"domain": "notareal-domain-test-abc123.org",   "selector": None, "category": "Invalid",
     "expected_band": ["POOR", "CRITICAL"], "expected_no": ["BIZ-015"],
     "notes": "Non-existent domain — NXDOMAIN expected"},
    {"domain": "fake-broken-invalid-domain-xyz.net","selector": None, "category": "Invalid",
     "expected_band": ["POOR", "CRITICAL"], "expected_no": ["BIZ-015"],
     "notes": "Non-existent domain — all protocols should fail"},
]


# ---------------------------------------------------------------------------
# Consistency Validators (ARCH-015)
# ---------------------------------------------------------------------------

def check_consistency(score, band, active_ids, biz_ids, severities):
    violations = []
    if "CRITICAL" in severities and score > 49:
        violations.append(f"CEILING_VIOLATION: CRITICAL present, score={score} > 49")
    if "HIGH" in severities and score > 74:
        violations.append(f"CEILING_VIOLATION: HIGH present, score={score} > 74")
    if "MEDIUM" in severities and score > 89:
        violations.append(f"CEILING_VIOLATION: MEDIUM present, score={score} > 89")
    if score >= 90 and band != "EXCELLENT":
        violations.append(f"BAND_MISMATCH: score={score} → EXCELLENT, got {band}")
    elif 75 <= score < 90 and band != "GOOD":
        violations.append(f"BAND_MISMATCH: score={score} → GOOD, got {band}")
    elif 50 <= score < 75 and band != "AT_RISK":
        violations.append(f"BAND_MISMATCH: score={score} → AT_RISK, got {band}")
    elif 25 <= score < 50 and band != "POOR":
        violations.append(f"BAND_MISMATCH: score={score} → POOR, got {band}")
    elif score < 25 and band != "CRITICAL":
        violations.append(f"BAND_MISMATCH: score={score} → CRITICAL, got {band}")
    if "BIZ-015" in biz_ids and ("CRITICAL" in severities or "HIGH" in severities):
        violations.append("CONTRADICTION: BIZ-015 present with CRITICAL/HIGH findings")
    if "BIZ-015" in biz_ids and "XPRO-012" not in active_ids:
        violations.append("CONTRADICTION: BIZ-015 present without XPRO-012")
    if not (0 <= score <= 100):
        violations.append(f"RANGE_ERROR: score={score} outside [0,100]")
    return violations


def check_expectations(expected_band, expected_no, band, biz_ids):
    failures = []
    if band not in expected_band:
        failures.append(f"UNEXPECTED_BAND: got '{band}', expected one of {expected_band}")
    for biz_id in expected_no:
        if biz_id in biz_ids:
            failures.append(f"UNEXPECTED_BIZ: {biz_id} appeared but expected absent")
    return failures


# ---------------------------------------------------------------------------
# Main Campaign Runner
# ---------------------------------------------------------------------------

# Emoji dicts for markdown report only (never printed to console)
BAND_EMOJI_MD = {
    "EXCELLENT": "🟢", "GOOD": "🟡", "AT_RISK": "🟠",
    "POOR": "🔴",      "CRITICAL": "⛔", "ERROR": "💀",
}
SEV_EMOJI_MD = {
    "CRITICAL": "⛔", "HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟡", "INFO": "ℹ️",
}
PASS_EMOJI_MD = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}

# ASCII tokens for console output
PASS_LABEL = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]"}


def run_campaign():
    safe_print("=" * 70)
    safe_print("M2F.2 -- REAL WORLD DOMAIN VALIDATION CAMPAIGN")
    safe_print(f"Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    safe_print(f"Domains: {len(DOMAIN_MATRIX)}")
    safe_print("=" * 70)

    dns_resolver    = DNSResolver()
    spf_validator   = SPFValidator(dns_resolver)
    dkim_validator  = DKIMValidator(dns_resolver)
    dmarc_validator = DMARCValidator(dns_resolver)
    aggregator      = AnalysisAggregator(dns_resolver, spf_validator, dkim_validator, dmarc_validator)
    orchestrator    = IntelligenceOrchestrator(aggregator)

    results = []

    for idx, entry in enumerate(DOMAIN_MATRIX, 1):
        domain   = entry["domain"]
        selector = entry.get("selector")
        category = entry["category"]
        safe_print(f"\n[{idx:02d}/{len(DOMAIN_MATRIX)}] {domain} ({category}) ...", end=" ", flush=True)
        t0 = time.time()

        try:
            response    = orchestrator.orchestrate_analysis(domain, selector)
            score       = response.score.score
            band        = response.score.band
            active_ids  = [i.insight_id for i in response.active_insights]
            severities  = [i.severity   for i in response.active_insights]
            biz_ids     = [b.insight_id for b in response.business_insights]
            biz_titles  = [b.title      for b in response.business_insights]
            rec_ids     = [r.insight_id for r in response.recommendations]
            elapsed     = round(time.time() - t0, 2)

            violations  = check_consistency(score, band, active_ids, biz_ids, severities)
            exp_fails   = check_expectations(entry["expected_band"], entry.get("expected_no", []), band, biz_ids)
            result      = "FAIL" if violations else ("WARN" if exp_fails else "PASS")

            safe_print(f"{PASS_LABEL[result]}  score={score} band={band}  ({elapsed}s)")

            results.append({
                "idx": idx, "domain": domain, "selector": selector or "(none)",
                "category": category, "notes": entry["notes"],
                "score": score, "band": band,
                "active_insights": active_ids, "severities": severities,
                "recommendations": rec_ids,
                "business_insights": biz_ids, "business_titles": biz_titles,
                "violations": violations, "expectation_failures": exp_fails,
                "result": result, "elapsed_s": elapsed, "error": None,
            })

        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            safe_print(f"[FAIL]  ERROR: {e} ({elapsed}s)")
            results.append({
                "idx": idx, "domain": domain, "selector": selector or "(none)",
                "category": category, "notes": entry["notes"],
                "score": None, "band": "ERROR",
                "active_insights": [], "severities": [], "recommendations": [],
                "business_insights": [], "business_titles": [],
                "violations": [f"EXCEPTION: {e}"], "expectation_failures": [],
                "result": "FAIL", "elapsed_s": elapsed, "error": str(e),
            })

    return results


# ---------------------------------------------------------------------------
# Markdown Report Builder
# ---------------------------------------------------------------------------

def build_report(results):
    now    = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    total  = len(results)
    passed = sum(1 for r in results if r["result"] == "PASS")
    warned = sum(1 for r in results if r["result"] == "WARN")
    failed = sum(1 for r in results if r["result"] == "FAIL")

    L = []
    L += [
        "# M2F.2 — Real World Domain Validation Campaign Report",
        "",
        f"**Generated:** {now}  ",
        f"**Pipeline version:** M2F.1 (ARCH-015 enforced)  ",
        f"**Domains tested:** {total}  ",
        f"**Results:** PASS={passed}  WARN={warned}  FAIL={failed}  ",
        "",
        "> **PASS** — All ARCH-015 consistency invariants satisfied and band within expected range.  ",
        "> **WARN** — Consistency invariants satisfied but band outside expected range (DNS state may have changed).  ",
        "> **FAIL** — One or more ARCH-015 invariants violated (score ceiling, BIZ-015 gating, band coherence).  ",
        "",
        "---", "",
    ]

    # Category summary table
    categories = {}
    for r in results:
        categories.setdefault(r["category"], []).append(r)

    L += ["## Category Summary", "",
          "| Category | Domains | PASS | WARN | FAIL |",
          "|----------|---------|------|------|------|",
    ]
    for cat, cr in categories.items():
        cp = sum(1 for r in cr if r["result"] == "PASS")
        cw = sum(1 for r in cr if r["result"] == "WARN")
        cf = sum(1 for r in cr if r["result"] == "FAIL")
        L.append(f"| {cat} | {len(cr)} | {cp} | {cw} | {cf} |")
    L.append(f"| **TOTAL** | **{total}** | **{passed}** | **{warned}** | **{failed}** |")
    L += ["", "---", ""]

    # Master results table
    L += [
        "## Master Results Table", "",
        "| # | Domain | Category | Score | Band | Key Findings | Business Signals | Result |",
        "|---|--------|----------|-------|------|-------------|-----------------|--------|",
    ]
    for r in results:
        be  = BAND_EMOJI_MD.get(r["band"], "?")
        pe  = PASS_EMOJI_MD[r["result"]]
        findings = ", ".join(f"`{i}`" for i in r["active_insights"][:4])
        if len(r["active_insights"]) > 4:
            findings += f" +{len(r['active_insights'])-4} more"
        biz = ", ".join(f"`{b}`" for b in r["business_insights"])
        score_str = str(r["score"]) if r["score"] is not None else "ERR"
        L.append(f"| {r['idx']} | {r['domain']} | {r['category']} | {score_str} | {be} {r['band']} | {findings or '-'} | {biz or '-'} | {pe} {r['result']} |")
    L += ["", "---", ""]

    # Per-category detailed sections
    for cat, cat_results in categories.items():
        L += [f"## Category: {cat}", ""]
        for r in cat_results:
            be = BAND_EMOJI_MD.get(r["band"], "?")
            pe = PASS_EMOJI_MD[r["result"]]
            L += [f"### {pe} {r['domain']}", "", f"> {r['notes']}", ""]

            L += ["| Field | Value |", "|-------|-------|",
                  f"| **Score** | `{r['score']}` |",
                  f"| **Band** | {be} `{r['band']}` |",
                  f"| **DKIM Selector** | `{r['selector']}` |",
                  f"| **DNS Elapsed** | `{r['elapsed_s']}s` |",
                  f"| **Result** | {pe} **{r['result']}** |", ""]

            # Active Insights
            if r["active_insights"]:
                L.append("**Active Insights:**")
                for i_id, sev in zip(r["active_insights"], r["severities"]):
                    L.append(f"- {SEV_EMOJI_MD.get(sev, '')} `{i_id}` — {sev}")
            else:
                L.append("**Active Insights:** _(none)_")
            L.append("")

            # Business Insights
            if r["business_titles"]:
                L.append("**Business Insights:**")
                for bid, btitle in zip(r["business_insights"], r["business_titles"]):
                    L.append(f"- `{bid}` — {btitle}")
            else:
                L.append("**Business Insights:** _(none)_")
            L.append("")

            # Recommendations
            if r["recommendations"]:
                L.append(f"**Recommendations:** {', '.join(f'`{rec}`' for rec in r['recommendations'])}")
            else:
                L.append("**Recommendations:** _(none)_")
            L.append("")

            # Expected behaviour
            L.append(f"**Expected Behaviour:** Band in {r.get('expected_band', ['—'])}, no unexpected BIZ insights")
            L.append(f"**Actual Behaviour:** Band = `{r['band']}`, Score = `{r['score']}`")
            L.append("")

            if r["violations"]:
                L.append("**⛔ Consistency Violations:**")
                for v in r["violations"]:
                    L.append(f"- `{v}`")
                L.append("")
            if r["expectation_failures"]:
                L.append("**⚠️ Expectation Mismatches (DNS may have changed):**")
                for ef in r["expectation_failures"]:
                    L.append(f"- `{ef}`")
                L.append("")
            if r["result"] == "PASS":
                L.append("All ARCH-015 consistency invariants satisfied.")
                L.append("")

            L += ["---", ""]

    # Invariant verification
    all_v = [v for r in results for v in r["violations"]]
    ceiling_crit  = sum(1 for v in all_v if "CRITICAL" in v and "CEILING" in v)
    ceiling_high  = sum(1 for v in all_v if "HIGH"     in v and "CEILING" in v)
    ceiling_med   = sum(1 for v in all_v if "MEDIUM"   in v and "CEILING" in v)
    band_mis      = sum(1 for v in all_v if "BAND_MISMATCH"  in v)
    biz15_v       = sum(1 for v in all_v if "BIZ-015"        in v)
    range_v       = sum(1 for v in all_v if "RANGE_ERROR"    in v)

    L += [
        "## ARCH-015 Consistency Invariant Verification", "",
        "| Invariant | Domains Tested | Violations |",
        "|-----------|----------------|-----------|",
        f"| CRITICAL severity ceiling (score ≤ 49) | {total} | {ceiling_crit} |",
        f"| HIGH severity ceiling (score ≤ 74) | {total} | {ceiling_high} |",
        f"| MEDIUM severity ceiling (score ≤ 89) | {total} | {ceiling_med} |",
        f"| Band/score coherence | {total} | {band_mis} |",
        f"| BIZ-015 contradiction prevention | {total} | {biz15_v} |",
        f"| Score in range [0, 100] | {total} | {range_v} |",
        "",
    ]

    if all_v:
        L += ["### Violation Details", ""]
        for r in results:
            for v in r["violations"]:
                L.append(f"- **{r['domain']}**: `{v}`")
        L.append("")
    else:
        L.append(f"> **Zero consistency violations across all {total} domains.**")
        L.append("")

    # -----------------------------------------------------------------------
    # Campaign Quality Summary
    # -----------------------------------------------------------------------
    fp_list = []
    fn_list = []
    contra  = [v for r in results for v in r["violations"] if "CONTRADICTION" in v]
    logic_f = [v for r in results for v in r["violations"] if "CEILING_VIOLATION" in v or "RANGE_ERROR" in v]

    for r in results:
        for ef in r["expectation_failures"]:
            if "UNEXPECTED_BAND" in ef and r["band"] in ("EXCELLENT", "GOOD"):
                fp_list.append(f"{r['domain']}: {ef}")
            elif "UNEXPECTED_BAND" in ef and r["band"] in ("POOR", "CRITICAL", "AT_RISK"):
                fn_list.append(f"{r['domain']}: {ef}")

    L += [
        "## Campaign Quality Summary", "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| False Positives (good domain flagged weak) | {len(fp_list)} |",
        f"| False Negatives (weak domain scored high) | {len(fn_list)} |",
        f"| Contradictions (BIZ/finding conflicts) | {len(contra)} |",
        f"| Logic Failures (ceiling / range violations) | {len(logic_f)} |",
        "",
    ]
    if fp_list:
        L.append("### False Positives")
        for item in fp_list:
            L.append(f"- {item}")
        L.append("")
    if fn_list:
        L.append("### False Negatives")
        for item in fn_list:
            L.append(f"- {item}")
        L.append("")
    if contra:
        L.append("### Contradictions")
        for item in contra:
            L.append(f"- {item}")
        L.append("")
    if logic_f:
        L.append("### Logic Failures")
        for item in logic_f:
            L.append(f"- {item}")
        L.append("")

    # Score distribution
    band_groups = {}
    for r in results:
        band_groups.setdefault(r["band"], []).append(r["domain"])

    L += ["## Score Distribution", "",
          "| Band | Count | Domains |",
          "|------|-------|---------|"]
    for b in ["EXCELLENT", "GOOD", "AT_RISK", "POOR", "CRITICAL", "ERROR"]:
        if b in band_groups:
            L.append(f"| {BAND_EMOJI_MD.get(b,'')} {b} | {len(band_groups[b])} | {', '.join(band_groups[b])} |")
    L += ["", "---", ""]

    L += ["---",
          f"*M2F.2 Validation Campaign · {now}*"]

    return "\n".join(L)


# ---------------------------------------------------------------------------
# JSON Results Builder
# ---------------------------------------------------------------------------

def build_json(results):
    return [
        {
            "domain":               r["domain"],
            "selector":             r["selector"],
            "category":             r["category"],
            "score":                r["score"],
            "score_band":           r["band"],
            "active_insights":      r["active_insights"],
            "recommendations":      r["recommendations"],
            "business_insights":    r["business_insights"],
            "violations":           r["violations"],
            "expectation_failures": r["expectation_failures"],
            "result":               r["result"],
            "elapsed_s":            r["elapsed_s"],
            "error":                r["error"],
            "notes":                r["notes"],
        }
        for r in results
    ]


if __name__ == "__main__":
    results = run_campaign()

    total  = len(results)
    passed = sum(1 for r in results if r["result"] == "PASS")
    warned = sum(1 for r in results if r["result"] == "WARN")
    failed = sum(1 for r in results if r["result"] == "FAIL")

    safe_print()
    safe_print("=" * 70)
    safe_print(f"CAMPAIGN COMPLETE -- {total} domains analysed")
    safe_print(f"  PASS: {passed}   WARN: {warned}   FAIL: {failed}")
    safe_print("=" * 70)

    # ---- Markdown report ----
    report = build_report(results)
    report_path = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "..", "docs", "context", "M2F2_VALIDATION_REPORT.md"
    ))
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    safe_print(f"\nReport saved -> {report_path}")

    # ---- JSON results ----
    json_data = build_json(results)
    json_path = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "..", "docs", "context", "M2F2_VALIDATION_RESULTS.json"
    ))
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    safe_print(f"JSON saved   -> {json_path}")
