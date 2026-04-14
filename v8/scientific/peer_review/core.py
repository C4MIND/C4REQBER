"""
TURBO-CDI v8.0 - Peer Review System
Agent 8: Scientific Method

Implements structured peer review for transformation plans.
Validates plans through multiple independent checks.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
from datetime import datetime


class ReviewStatus(Enum):
    """Status of a review check"""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class ReviewCheck:
    """Individual review check result"""

    check_id: str
    name: str
    category: str  # "formal", "empirical", "pragmatic", "ethical"
    status: ReviewStatus
    message: str
    recommendation: Optional[str] = None
    severity: str = "info"  # "info", "low", "medium", "high", "critical"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewReport:
    """Complete peer review report"""

    timestamp: datetime
    plan_id: str
    overall_status: str  # "approved", "approved_with_warnings", "rejected"
    checks: List[ReviewCheck]
    pass_rate: float
    critical_issues: int
    warnings: int
    recommendations: List[str]


class PeerReviewSystem:
    """
    Multi-dimensional peer review for transformation plans.

    Review categories:
    - Formal: Logic, completeness, consistency
    - Empirical: Evidence-based validation
    - Pragmatic: Feasibility, resource constraints
    - Ethical: Value alignment, side effects
    """

    def __init__(self):
        self._reviewers: Dict[str, Callable] = {
            # Formal reviewers
            "completeness": self._check_completeness,
            "consistency": self._check_consistency,
            "theorem_11_compliance": self._check_theorem_11,
            # Empirical reviewers
            "calibration_status": self._check_calibration,
            "historical_precedent": self._check_historical_precedent,
            # Pragmatic reviewers
            "feasibility": self._check_feasibility,
            "resource_constraints": self._check_resources,
            "reversibility": self._check_reversibility,
            # Ethical reviewers
            "side_effect_risk": self._check_side_effects,
            "value_alignment": self._check_value_alignment,
        }

    def review_plan(
        self, plan: Dict[str, Any], context: Optional[Dict] = None
    ) -> ReviewReport:
        """
        Perform full peer review of a transformation plan.

        Args:
            plan: Transformation plan to review
            context: Additional context (user profile, domain, etc.)

        Returns:
            Complete ReviewReport with all checks
        """
        checks = []

        # Run all reviewers
        for check_id, reviewer in self._reviewers.items():
            try:
                check = reviewer(plan, context or {})
                checks.append(check)
            except Exception as e:
                checks.append(
                    ReviewCheck(
                        check_id=check_id,
                        name=check_id.replace("_", " ").title(),
                        category="error",
                        status=ReviewStatus.SKIPPED,
                        message=f"Check failed with error: {e}",
                        severity="high",
                    )
                )

        # Calculate overall status
        critical_count = sum(1 for c in checks if c.severity == "critical")
        failed_count = sum(1 for c in checks if c.status == ReviewStatus.FAILED)
        warning_count = sum(1 for c in checks if c.status == ReviewStatus.WARNING)

        if critical_count > 0 or failed_count > 2:
            overall = "rejected"
        elif warning_count > 0 or failed_count > 0:
            overall = "approved_with_warnings"
        else:
            overall = "approved"

        # Collect recommendations
        recommendations = [
            c.recommendation
            for c in checks
            if c.recommendation and c.status != ReviewStatus.PASSED
        ]

        # Calculate pass rate
        completed = [c for c in checks if c.status != ReviewStatus.SKIPPED]
        passed = sum(1 for c in completed if c.status == ReviewStatus.PASSED)
        pass_rate = passed / len(completed) if completed else 0.0

        return ReviewReport(
            timestamp=datetime.now(),
            plan_id=plan.get("id", "unknown"),
            overall_status=overall,
            checks=checks,
            pass_rate=pass_rate,
            critical_issues=critical_count,
            warnings=warning_count,
            recommendations=recommendations,
        )

    # ═════════════════════════════════════════════════════════════════════════════
    # FORMAL REVIEWERS
    # ═════════════════════════════════════════════════════════════════════════════

    def _check_completeness(self, plan: Dict, context: Dict) -> ReviewCheck:
        """Check if plan has all required components"""
        required = ["path", "transformation", "domain", "estimated_effectiveness"]
        missing = [r for r in required if r not in plan or plan[r] is None]

        if missing:
            return ReviewCheck(
                check_id="completeness",
                name="Plan Completeness",
                category="formal",
                status=ReviewStatus.FAILED,
                message=f"Missing required components: {', '.join(missing)}",
                recommendation=f"Add the following components: {', '.join(missing)}",
                severity="critical",
            )

        return ReviewCheck(
            check_id="completeness",
            name="Plan Completeness",
            category="formal",
            status=ReviewStatus.PASSED,
            message="All required components present",
            severity="info",
        )

    def _check_consistency(self, plan: Dict, context: Dict) -> ReviewCheck:
        """Check internal consistency of the plan"""
        issues = []

        # Check effectiveness range
        eff = plan.get("estimated_effectiveness", 0.5)
        if not (0 <= eff <= 1):
            issues.append(f"Effectiveness {eff} outside [0,1] range")

        # Check path length matches transformation complexity
        path = plan.get("path", [])
        if len(path) > 6:
            issues.append(f"Path length {len(path)} exceeds Theorem 11 bound")

        if issues:
            return ReviewCheck(
                check_id="consistency",
                name="Internal Consistency",
                category="formal",
                status=ReviewStatus.FAILED,
                message="; ".join(issues),
                recommendation="Review plan parameters for consistency",
                severity="high",
            )

        return ReviewCheck(
            check_id="consistency",
            name="Internal Consistency",
            category="formal",
            status=ReviewStatus.PASSED,
            message="Plan is internally consistent",
            severity="info",
        )

    def _check_theorem_11(self, plan: Dict, context: Dict) -> ReviewCheck:
        """Verify plan complies with Theorem 11"""
        path = plan.get("path", [])

        if len(path) > 6:
            return ReviewCheck(
                check_id="theorem_11_compliance",
                name="Theorem 11 Compliance",
                category="formal",
                status=ReviewStatus.FAILED,
                message=f"Plan requires {len(path)} steps, exceeds ≤6 bound",
                recommendation="Break plan into multiple stages or find shorter path",
                severity="critical",
            )

        return ReviewCheck(
            check_id="theorem_11_compliance",
            name="Theorem 11 Compliance",
            category="formal",
            status=ReviewStatus.PASSED,
            message=f"Plan uses {len(path)} steps, within ≤6 bound",
            severity="info",
        )

    # ═════════════════════════════════════════════════════════════════════════════
    # EMPIRICAL REVIEWERS
    # ═════════════════════════════════════════════════════════════════════════════

    def _check_calibration(self, plan: Dict, context: Dict) -> ReviewCheck:
        """Check if system is well-calibrated for this domain"""
        domain = plan.get("domain", "")

        # Check if we have outcome tracker in context
        tracker = context.get("outcome_tracker")
        if tracker:
            calibration = tracker.calculate_calibration(domain=domain)
            if calibration.n_samples >= 30:  # Need more samples for reliability
                # Brier score: 0 = perfect, 0.25 = random, 0.5 = always wrong
                if calibration.brier > 0.25:  # Worse than random
                    return ReviewCheck(
                        check_id="calibration_status",
                        name="Calibration Status",
                        category="empirical",
                        status=ReviewStatus.WARNING,
                        message=f"Poor calibration in {domain} (Brier: {calibration.brier:.3f})",
                        recommendation="Predictions may be unreliable; verify with domain expert",
                        severity="high",
                        details={
                            "brier": calibration.brier,
                            "n_samples": calibration.n_samples,
                        },
                    )
                elif calibration.brier > 0.15:  # Room for improvement
                    return ReviewCheck(
                        check_id="calibration_status",
                        name="Calibration Status",
                        category="empirical",
                        status=ReviewStatus.INFO,
                        message=f"Calibration in {domain} has room for improvement (Brier: {calibration.brier:.3f})",
                        recommendation="Consider gathering more calibration data",
                        severity="low",
                        details={
                            "brier": calibration.brier,
                            "n_samples": calibration.n_samples,
                        },
                    )
                elif calibration.brier < 0.05:
                    return ReviewCheck(
                        check_id="calibration_status",
                        name="Calibration Status",
                        category="empirical",
                        status=ReviewStatus.PASSED,
                        message=f"Well-calibrated in {domain} (Brier: {calibration.brier:.3f})",
                        severity="info",
                        details={
                            "brier": calibration.brier,
                            "n_samples": calibration.n_samples,
                        },
                    )

        return ReviewCheck(
            check_id="calibration_status",
            name="Calibration Status",
            category="empirical",
            status=ReviewStatus.SKIPPED,
            message=f"Insufficient data for calibration check in {domain}",
            recommendation="Record outcomes to improve calibration",
            severity="low",
        )

    def _check_historical_precedent(self, plan: Dict, context: Dict) -> ReviewCheck:
        """Check for similar successful transformations"""
        domain = plan.get("domain", "")
        tracker = context.get("outcome_tracker")

        if tracker:
            # Check domain effectiveness
            stats = tracker._get_domain_stats()
            if domain in stats and stats[domain]["count"] >= 3:
                avg_eff = stats[domain]["avg"]
                if avg_eff > 0.7:
                    return ReviewCheck(
                        check_id="historical_precedent",
                        name="Historical Precedent",
                        category="empirical",
                        status=ReviewStatus.PASSED,
                        message=f"Strong historical precedent: {stats[domain]['count']} transformations, avg effectiveness {avg_eff:.2f}",
                        severity="info",
                        details={
                            "count": stats[domain]["count"],
                            "avg_effectiveness": avg_eff,
                        },
                    )
                elif avg_eff < 0.4:
                    return ReviewCheck(
                        check_id="historical_precedent",
                        name="Historical Precedent",
                        category="empirical",
                        status=ReviewStatus.WARNING,
                        message=f"Poor historical performance in {domain}: avg effectiveness {avg_eff:.2f}",
                        recommendation="Consider alternative approaches or domains",
                        severity="medium",
                        details={
                            "count": stats[domain]["count"],
                            "avg_effectiveness": avg_eff,
                        },
                    )

        return ReviewCheck(
            check_id="historical_precedent",
            name="Historical Precedent",
            category="empirical",
            status=ReviewStatus.SKIPPED,
            message=f"No historical data available for {domain}",
            recommendation="Proceed with caution and record outcomes",
            severity="low",
        )

    # ═════════════════════════════════════════════════════════════════════════════
    # PRAGMATIC REVIEWERS
    # ═════════════════════════════════════════════════════════════════════════════

    def _check_feasibility(self, plan: Dict, context: Dict) -> ReviewCheck:
        """Check practical feasibility"""
        path = plan.get("path", [])
        eff = plan.get("estimated_effectiveness", 0.5)

        # Very short paths with low effectiveness are suspicious
        if len(path) <= 2 and eff < 0.4:
            return ReviewCheck(
                check_id="feasibility",
                name="Practical Feasibility",
                category="pragmatic",
                status=ReviewStatus.WARNING,
                message=f"Simple plan ({len(path)} steps) with low effectiveness ({eff:.0%}) suggests complexity underestimated",
                recommendation="Re-evaluate transformation complexity",
                severity="medium",
            )

        return ReviewCheck(
            check_id="feasibility",
            name="Practical Feasibility",
            category="pragmatic",
            status=ReviewStatus.PASSED,
            message="Plan appears feasible",
            severity="info",
        )

    def _check_resources(self, plan: Dict, context: Dict) -> ReviewCheck:
        """Check resource constraints"""
        path = plan.get("path", [])

        # Longer paths need more resources
        if len(path) > 5:
            return ReviewCheck(
                check_id="resource_constraints",
                name="Resource Constraints",
                category="pragmatic",
                status=ReviewStatus.WARNING,
                message=f"Long plan ({len(path)} steps) requires significant resources",
                recommendation="Consider parallel execution or resource pre-allocation",
                severity="medium",
            )

        return ReviewCheck(
            check_id="resource_constraints",
            name="Resource Constraints",
            category="pragmatic",
            status=ReviewStatus.PASSED,
            message="Resource requirements appear manageable",
            severity="info",
        )

    def _check_reversibility(self, plan: Dict, context: Dict) -> ReviewCheck:
        """Check reversibility implications"""
        rev = plan.get("estimated_reversibility", 0.5)

        if rev < 0.3:
            return ReviewCheck(
                check_id="reversibility",
                name="Reversibility Check",
                category="pragmatic",
                status=ReviewStatus.WARNING,
                message=f"Low reversibility ({rev:.0%}): transformation may be irreversible",
                recommendation="Implement checkpoints and rollback procedures",
                severity="high",
            )

        return ReviewCheck(
            check_id="reversibility",
            name="Reversibility Check",
            category="pragmatic",
            status=ReviewStatus.PASSED,
            message=f"Reversibility acceptable ({rev:.0%})",
            severity="info",
        )

    # ═════════════════════════════════════════════════════════════════════════════
    # ETHICAL REVIEWERS
    # ═════════════════════════════════════════════════════════════════════════════

    def _check_side_effects(self, plan: Dict, context: Dict) -> ReviewCheck:
        """Check for potential side effects"""
        # This is a simplified check
        operation = plan.get("operation", "")
        domain = plan.get("domain", "")

        # High-impact operations in sensitive domains need review
        sensitive_domains = ["healthcare", "finance", "legal", "military", "social"]
        high_impact_ops = ["DISRUPT", "ACTIVATE"]

        if any(sd in domain.lower() for sd in sensitive_domains):
            if any(op in str(operation) for op in high_impact_ops):
                return ReviewCheck(
                    check_id="side_effect_risk",
                    name="Side Effect Risk",
                    category="ethical",
                    status=ReviewStatus.WARNING,
                    message=f"High-impact operation in sensitive domain ({domain})",
                    recommendation="Conduct thorough impact assessment before execution",
                    severity="high",
                )

        return ReviewCheck(
            check_id="side_effect_risk",
            name="Side Effect Risk",
            category="ethical",
            status=ReviewStatus.PASSED,
            message="No significant side effect risks identified",
            severity="info",
        )

    def _check_value_alignment(self, plan: Dict, context: Dict) -> ReviewCheck:
        """Check alignment with stated values"""
        user_profile = context.get("user_profile")

        if user_profile and hasattr(user_profile, "risk_tolerance"):
            risk = user_profile.risk_tolerance
            eff = plan.get("estimated_effectiveness", 0.5)

            if risk == "conservative" and eff < 0.7:
                return ReviewCheck(
                    check_id="value_alignment",
                    name="Value Alignment",
                    category="ethical",
                    status=ReviewStatus.WARNING,
                    message=f"Low effectiveness ({eff:.0%}) may not align with conservative risk profile",
                    recommendation="Consider more reliable transformations or adjust risk tolerance",
                    severity="medium",
                )

        return ReviewCheck(
            check_id="value_alignment",
            name="Value Alignment",
            category="ethical",
            status=ReviewStatus.PASSED,
            message="Plan aligns with stated values",
            severity="info",
        )

    def generate_report_markdown(self, report: ReviewReport) -> str:
        """Generate markdown report for documentation"""
        lines = [
            "# Peer Review Report",
            f"**Plan ID:** {report.plan_id}",
            f"**Date:** {report.timestamp.isoformat()}",
            f"**Overall Status:** {report.overall_status.upper()}",
            f"**Pass Rate:** {report.pass_rate:.1%}",
            f"**Critical Issues:** {report.critical_issues}",
            f"**Warnings:** {report.warnings}",
            "",
            "## Checks Performed",
            "",
        ]

        # Group by category
        by_category = {}
        for check in report.checks:
            cat = check.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(check)

        for category, checks in by_category.items():
            lines.append(f"### {category.title()} Checks")
            lines.append("")

            for check in checks:
                status_icon = {
                    ReviewStatus.PASSED: "✅",
                    ReviewStatus.FAILED: "❌",
                    ReviewStatus.WARNING: "⚠️",
                    ReviewStatus.SKIPPED: "⏭️",
                }.get(check.status, "❓")

                lines.append(f"{status_icon} **{check.name}** ({check.status.value})")
                lines.append(f"   {check.message}")
                if check.recommendation:
                    lines.append(f"   💡 {check.recommendation}")
                lines.append("")

        if report.recommendations:
            lines.extend(["## Summary Recommendations", ""])
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {rec}")

        return "\n".join(lines)
