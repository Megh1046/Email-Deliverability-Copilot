"""
test_rule_engine_consistency.py

Validates logical consistency of the Rule Engine across:
 - Score ceiling enforcement per severity level
 - Contradiction prevention (no healthy messaging alongside critical failures)
 - BIZ-015 gating: must only appear when XPRO-012 is active
 - DMARC-017 no longer inflates scores as a healthy bonus
 - Real-domain validation for production-grade domains

Architecture: ARCH-015 — Rule Engine Consistency Enforcement
"""

import pytest

from domains.rules.score_calculator import ScoreCalculator
from domains.rules.business_translator import BusinessTranslator
from domains.rules.engine import RuleEngine
from domains.rules.recommendation_mapper import RecommendationMapper
from core.orchestrator import IntelligenceOrchestrator
from domains.analysis.aggregator.aggregator import AnalysisAggregator
from domains.analysis.dns.resolver import DNSResolver
from domains.analysis.validators.spf import SPFValidator
from domains.analysis.validators.dkim import DKIMValidator
from domains.analysis.validators.dmarc import DMARCValidator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def score_calc():
    return ScoreCalculator()


@pytest.fixture
def biz_translator():
    return BusinessTranslator()


@pytest.fixture
def orchestrator():
    dns_resolver = DNSResolver()
    spf_validator = SPFValidator(dns_resolver)
    dkim_validator = DKIMValidator(dns_resolver)
    dmarc_validator = DMARCValidator(dns_resolver)
    aggregator_service = AnalysisAggregator(
        dns_resolver, spf_validator, dkim_validator, dmarc_validator
    )
    return IntelligenceOrchestrator(aggregator_service)


# ---------------------------------------------------------------------------
# Section 1: Severity-Based Score Ceiling Tests
# ---------------------------------------------------------------------------

class TestScoreCeilings:
    """Score must never exceed its severity-based ceiling regardless of bonuses."""

    def test_critical_insight_caps_score_at_49(self, score_calc):
        """CRITICAL severity: score must be ≤ 49 regardless of other bonuses."""
        # DKIM-001 is CRITICAL (-20), XPRO-012 is INFO (+10)
        result = score_calc.calculate(["DKIM-001", "XPRO-012"])
        assert result.score <= 49, (
            f"CRITICAL finding present but score is {result.score} (expected ≤ 49)"
        )

    def test_critical_insight_band_not_excellent_or_good(self, score_calc):
        """CRITICAL severity: band must be POOR or CRITICAL."""
        result = score_calc.calculate(["SPF-001"])  # CRITICAL
        assert result.band in ("POOR", "CRITICAL"), (
            f"Expected POOR/CRITICAL band, got {result.band}"
        )

    def test_high_insight_caps_score_at_74(self, score_calc):
        """HIGH severity: score must be ≤ 74 regardless of other signals."""
        # SPF-006 is HIGH (-12)
        result = score_calc.calculate(["SPF-006"])
        assert result.score <= 74, (
            f"HIGH finding present but score is {result.score} (expected ≤ 74)"
        )

    def test_high_insight_band_not_excellent(self, score_calc):
        """HIGH severity: band must never be EXCELLENT."""
        result = score_calc.calculate(["SPF-006"])
        assert result.band != "EXCELLENT", (
            f"Expected non-EXCELLENT band with HIGH finding, got {result.band}"
        )

    def test_medium_insight_caps_score_at_89(self, score_calc):
        """MEDIUM severity: score must be ≤ 89."""
        # DMARC-008 is MEDIUM (-6)
        result = score_calc.calculate(["DMARC-008"])
        assert result.score <= 89, (
            f"MEDIUM finding present but score is {result.score} (expected ≤ 89)"
        )

    def test_low_insight_has_no_ceiling(self, score_calc):
        """LOW severity: no ceiling applied — score can reach 100."""
        # DMARC-014 is LOW (-2)
        result = score_calc.calculate(["DMARC-014"])
        assert result.score >= 90, (
            f"LOW-only finding should allow EXCELLENT score, got {result.score}"
        )

    def test_critical_dominates_high_ceiling(self, score_calc):
        """When both CRITICAL and HIGH are present, the CRITICAL ceiling (49) applies."""
        result = score_calc.calculate(["SPF-001", "SPF-006"])  # CRITICAL + HIGH
        assert result.score <= 49, (
            f"CRITICAL should dominate ceiling, but score is {result.score}"
        )


# ---------------------------------------------------------------------------
# Section 2: DMARC-017 Is No Longer a Score-Boosting Signal
# ---------------------------------------------------------------------------

class TestDMARC017Neutral:
    """DMARC-017 (p=reject Healthy) must have zero weight — it is informational only."""

    def test_dmarc_017_does_not_boost_score(self, score_calc):
        """Score with only DMARC-017 active must equal 100 (no bonus applied)."""
        # If DMARC-017 had weight +10, score would be 110 → clamped to 100.
        # With weight 0, score stays at 100 identically.
        # The distinction: add a LOW deduction so we can differentiate 98 vs 100
        result_without = score_calc.calculate(["DMARC-014"])  # LOW -2 → score 98
        result_with = score_calc.calculate(["DMARC-014", "DMARC-017"])  # should still be 98
        assert result_with.score == result_without.score, (
            "DMARC-017 must not inflate the score; it is a neutral informational signal"
        )

    def test_dmarc_017_weight_is_zero(self):
        """Directly assert DMARC-017 weight is 0 in the knowledge registry."""
        from domains.rules.knowledge.insights import INSIGHT_REGISTRY
        weight = INSIGHT_REGISTRY["DMARC-017"]["weight"]
        assert weight == 0, (
            f"DMARC-017 must have weight=0 (got {weight}). "
            "Score bonuses must come from XPRO-012 only."
        )


# ---------------------------------------------------------------------------
# Section 3: BIZ-015 Gating — Must Require XPRO-012
# ---------------------------------------------------------------------------

class TestBIZ015Gating:
    """BIZ-015 ('Excellent — Your Email Is Fully Authenticated') must only appear
    when XPRO-012 (Full Authentication Pass) is in the active insight set."""

    def test_biz_015_absent_without_xpro_012(self, biz_translator):
        """BIZ-015 must not appear if XPRO-012 is not active."""
        insights = biz_translator.translate(["DMARC-017"])  # DMARC-017 alone, no XPRO-012
        ids = [i.insight_id for i in insights]
        assert "BIZ-015" not in ids, (
            "BIZ-015 must not trigger on DMARC-017 alone; XPRO-012 is required"
        )

    def test_biz_015_present_with_xpro_012_only(self, biz_translator):
        """BIZ-015 must appear when XPRO-012 is active and no CRITICAL/HIGH exists."""
        insights = biz_translator.translate(["XPRO-012"])
        ids = [i.insight_id for i in insights]
        assert "BIZ-015" in ids, (
            "BIZ-015 must appear when XPRO-012 is active and domain is clean"
        )

    def test_biz_015_suppressed_when_critical_present(self, biz_translator):
        """BIZ-015 must be suppressed even if XPRO-012 is active when CRITICAL exists."""
        # This is a contradictory state — defensive test
        insights = biz_translator.translate(["XPRO-012", "DKIM-001"])
        ids = [i.insight_id for i in insights]
        assert "BIZ-015" not in ids, (
            "BIZ-015 must be suppressed when CRITICAL finding (DKIM-001) is present"
        )

    def test_biz_015_suppressed_when_high_present(self, biz_translator):
        """BIZ-015 must be suppressed when any HIGH severity finding is active."""
        insights = biz_translator.translate(["XPRO-012", "DMARC-005"])
        ids = [i.insight_id for i in insights]
        assert "BIZ-015" not in ids, (
            "BIZ-015 must be suppressed when HIGH finding (DMARC-005) is present"
        )


# ---------------------------------------------------------------------------
# Section 4: Contradiction Prevention Tests
# ---------------------------------------------------------------------------

class TestContradictionPrevention:
    """No healthy/excellent messaging must coexist with CRITICAL or HIGH findings."""

    def test_no_healthy_insight_with_critical_finding(self, biz_translator):
        """All healthy business insights must be absent when CRITICAL is present."""
        insights = biz_translator.translate(["SPF-001", "DKIM-001", "DMARC-001", "XPRO-001"])
        ids = [i.insight_id for i in insights]
        assert "BIZ-015" not in ids

    def test_critical_produces_negative_business_insights_only(self, biz_translator):
        """When only CRITICAL/HIGH insights are active, only negative BIZ insights appear."""
        insights = biz_translator.translate(["SPF-001", "DKIM-001", "DMARC-001", "XPRO-001"])
        # BIZ-001: "Your Emails Are Failing the Internet's Trust Check" — correct
        ids = [i.insight_id for i in insights]
        assert "BIZ-001" in ids, "BIZ-001 should fire on SPF+DKIM+DMARC+XPRO-001 failure"

    def test_contradictory_insight_prevention_mixed(self, biz_translator):
        """DKIM-001 (CRITICAL) with XPRO-012 active — BIZ-015 must not appear."""
        insights = biz_translator.translate(["DKIM-001", "XPRO-012"])
        ids = [i.insight_id for i in insights]
        assert "BIZ-001" in ids or "BIZ-006" in ids  # negative biz insights should fire
        assert "BIZ-015" not in ids

    def test_medium_only_allows_healthy_messaging(self, biz_translator):
        """MEDIUM findings alone must not suppress BIZ-015 if XPRO-012 is present."""
        # DMARC-008 is MEDIUM — should not suppress BIZ-015
        insights = biz_translator.translate(["XPRO-012", "DMARC-008"])
        ids = [i.insight_id for i in insights]
        assert "BIZ-015" in ids, (
            "MEDIUM findings must not suppress healthy messaging; "
            "only CRITICAL or HIGH findings trigger suppression"
        )

    def test_low_only_allows_healthy_messaging(self, biz_translator):
        """LOW findings must not suppress BIZ-015 if XPRO-012 is present."""
        insights = biz_translator.translate(["XPRO-012", "DMARC-014"])
        ids = [i.insight_id for i in insights]
        assert "BIZ-015" in ids


# ---------------------------------------------------------------------------
# Section 5: Real-Domain Validation Tests
# ---------------------------------------------------------------------------

REAL_DOMAINS = ["google.com", "github.com", "microsoft.com", "openai.com"]


class TestRealDomainValidation:
    """
    Live DNS integration tests against well-known production domains.
    These domains are expected to have fully healthy email infrastructure.

    Tests enforce:
      - Score/band consistency
      - Severity ceiling enforcement
      - Contradiction-free business insights
    """

    @pytest.mark.parametrize("domain", REAL_DOMAINS)
    def test_score_band_consistency(self, orchestrator, domain):
        """Score and band must always be consistent with each other."""
        response = orchestrator.orchestrate_analysis(domain)
        score = response.score.score
        band = response.score.band

        if score >= 90:
            assert band == "EXCELLENT", f"{domain}: score={score} but band={band}"
        elif score >= 75:
            assert band == "GOOD", f"{domain}: score={score} but band={band}"
        elif score >= 50:
            assert band == "AT_RISK", f"{domain}: score={score} but band={band}"
        elif score >= 25:
            assert band == "POOR", f"{domain}: score={score} but band={band}"
        else:
            assert band == "CRITICAL", f"{domain}: score={score} but band={band}"

    @pytest.mark.parametrize("domain", REAL_DOMAINS)
    def test_critical_severity_ceiling_enforced(self, orchestrator, domain):
        """If CRITICAL insights are active, score must be ≤ 49."""
        response = orchestrator.orchestrate_analysis(domain)
        severities = [i.severity for i in response.active_insights]
        score = response.score.score

        if "CRITICAL" in severities:
            assert score <= 49, (
                f"{domain}: CRITICAL insight active but score={score} (expected ≤ 49)"
            )

    @pytest.mark.parametrize("domain", REAL_DOMAINS)
    def test_high_severity_ceiling_enforced(self, orchestrator, domain):
        """If HIGH insights are active, score must be ≤ 74."""
        response = orchestrator.orchestrate_analysis(domain)
        severities = [i.severity for i in response.active_insights]
        score = response.score.score

        if "HIGH" in severities:
            assert score <= 74, (
                f"{domain}: HIGH insight active but score={score} (expected ≤ 74)"
            )

    @pytest.mark.parametrize("domain", REAL_DOMAINS)
    def test_no_contradictory_business_insights(self, orchestrator, domain):
        """BIZ-015 must never appear alongside CRITICAL or HIGH findings."""
        response = orchestrator.orchestrate_analysis(domain)
        severities = [i.severity for i in response.active_insights]
        biz_ids = [b.insight_id for b in response.business_insights]

        if "CRITICAL" in severities or "HIGH" in severities:
            assert "BIZ-015" not in biz_ids, (
                f"{domain}: BIZ-015 (healthy) present with CRITICAL/HIGH findings — contradiction"
            )

    @pytest.mark.parametrize("domain", REAL_DOMAINS)
    def test_score_within_valid_range(self, orchestrator, domain):
        """Score must always be in [0, 100]."""
        response = orchestrator.orchestrate_analysis(domain)
        score = response.score.score
        assert 0 <= score <= 100, f"{domain}: score={score} is out of valid range [0, 100]"

    @pytest.mark.parametrize("domain", REAL_DOMAINS)
    def test_biz_015_requires_xpro_012(self, orchestrator, domain):
        """BIZ-015 must only appear when XPRO-012 is in active insights."""
        response = orchestrator.orchestrate_analysis(domain)
        active_ids = [i.insight_id for i in response.active_insights]
        biz_ids = [b.insight_id for b in response.business_insights]

        if "BIZ-015" in biz_ids:
            assert "XPRO-012" in active_ids, (
                f"{domain}: BIZ-015 present but XPRO-012 not in active insights"
            )
