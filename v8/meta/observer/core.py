"""
TURBO-CDI v8.0 - Meta-Observer
Agent 4: Meta Systems (Bateson)

Second-order cybernetics: the system observes itself.
Tracks system performance, detects anomalies, maintains awareness.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
from collections import deque
from enum import Enum
import statistics


class ObservationType(Enum):
    """Types of meta-observations"""

    PERFORMANCE = "performance"
    CALIBRATION = "calibration"
    ANOMALY = "anomaly"
    RESOURCE = "resource"
    INTERACTION = "interaction"


@dataclass
class SystemObservation:
    """A single meta-observation"""

    timestamp: datetime
    observation_type: ObservationType
    metric: str
    value: float
    threshold: float
    status: str  # "normal", "warning", "critical"
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetaReport:
    """Comprehensive meta-system report"""

    timestamp: datetime
    system_health: str  # "healthy", "degraded", "critical"
    observations: List[SystemObservation]
    trends: Dict[str, List[float]]  # Metric -> recent values
    recommendations: List[str]
    self_awareness_score: float  # 0-1, how well system knows itself


class MetaObserver:
    """
    Second-order cybernetic observer (Bateson).

    The system observes its own operation:
    - Performance metrics (speed, accuracy)
    - Calibration drift (predictions vs reality)
    - Anomaly detection (unexpected behavior)
    - Resource usage (memory, computation)
    - Interaction patterns (user behavior)

    Key insight: "The system that observes itself changes itself"
    """

    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.observations: deque = deque(maxlen=history_size)
        self.metrics_history: Dict[str, deque] = {}
        self._anomaly_detector = AnomalyDetector()
        self._performance_tracker = PerformanceTracker()

    def observe(
        self,
        observation_type: ObservationType,
        metric: str,
        value: float,
        threshold: float,
        context: Optional[Dict] = None,
    ) -> SystemObservation:
        """
        Record a meta-observation.

        Args:
            observation_type: Type of observation
            metric: Metric name
            value: Current value
            threshold: Threshold for comparison
            context: Additional context

        Returns:
            SystemObservation record
        """
        # Determine status
        ratio = value / threshold if threshold > 0 else 0

        if ratio < 0.8 or ratio > 1.25:
            status = "critical"
        elif ratio < 0.9 or ratio > 1.1:
            status = "warning"
        else:
            status = "normal"

        observation = SystemObservation(
            timestamp=datetime.now(),
            observation_type=observation_type,
            metric=metric,
            value=value,
            threshold=threshold,
            status=status,
            context=context or {},
        )

        self.observations.append(observation)

        # Track metric history
        if metric not in self.metrics_history:
            self.metrics_history[metric] = deque(maxlen=self.history_size)
        self.metrics_history[metric].append(value)

        return observation

    def observe_performance(
        self, operation: str, duration_ms: float, success: bool
    ) -> SystemObservation:
        """
        Observe system performance.

        Args:
            operation: Operation performed
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
        """
        # Thresholds based on operation type
        thresholds = {
            "navigation": 10.0,  # 10ms for navigation
            "transformation": 5.0,  # 5ms for transformation planning
            "bias_detection": 20.0,  # 20ms for bias analysis
            "falsification": 1000.0,  # 1s for falsification suite
        }

        threshold = thresholds.get(operation, 50.0)

        context = {
            "operation": operation,
            "success": success,
            "duration_ms": duration_ms,
        }

        return self.observe(
            ObservationType.PERFORMANCE,
            f"perf_{operation}",
            duration_ms,
            threshold,
            context,
        )

    def observe_calibration(
        self, domain: str, brier_score: float, n_samples: int
    ) -> SystemObservation:
        """
        Observe calibration status.

        Args:
            domain: Domain being observed
            brier_score: Current Brier score
            n_samples: Number of samples
        """
        # Brier threshold: lower is better
        threshold = 0.1  # Good calibration threshold

        context = {"domain": domain, "n_samples": n_samples, "brier_score": brier_score}

        # Invert for consistency (higher = better)
        value = 1.0 - (brier_score / 0.25)  # Normalize to 0-1
        value = max(0, min(1, value))

        return self.observe(
            ObservationType.CALIBRATION,
            f"calibration_{domain}",
            value,
            0.6,  # Threshold for "good" calibration
            context,
        )

    def detect_anomalies(
        self, metric: str, window_size: int = 10
    ) -> List[SystemObservation]:
        """
        Detect anomalies in recent observations.

        Args:
            metric: Metric to check
            window_size: Number of recent values to analyze

        Returns:
            List of anomaly observations
        """
        if metric not in self.metrics_history:
            return []

        values = list(self.metrics_history[metric])[-window_size:]

        if len(values) < 3:
            return []

        anomalies = []

        # Simple statistical anomaly detection
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0

        for i, value in enumerate(values):
            if std > 0 and abs(value - mean) > 2 * std:  # 2 sigma rule
                anomaly = SystemObservation(
                    timestamp=datetime.now(),
                    observation_type=ObservationType.ANOMALY,
                    metric=f"anomaly_{metric}",
                    value=value,
                    threshold=mean + 2 * std,
                    status="warning",
                    context={
                        "mean": mean,
                        "std": std,
                        "z_score": (value - mean) / std if std > 0 else 0,
                        "index": len(values) - window_size + i,
                    },
                )
                anomalies.append(anomaly)
                self.observations.append(anomaly)

        return anomalies

    def generate_meta_report(self) -> MetaReport:
        """
        Generate comprehensive meta-system report.

        Returns:
            MetaReport with system self-assessment
        """
        # Get recent observations
        recent = list(self.observations)[-100:]

        # Calculate system health
        status_counts = {"normal": 0, "warning": 0, "critical": 0}
        for obs in recent:
            status_counts[obs.status] = status_counts.get(obs.status, 0) + 1

        if status_counts["critical"] > 5:
            health = "critical"
        elif status_counts["warning"] > 10 or status_counts["critical"] > 0:
            health = "degraded"
        else:
            health = "healthy"

        # Build trends
        trends = {}
        for metric, history in self.metrics_history.items():
            trends[metric] = list(history)[-20:]  # Last 20 values

        # Generate recommendations
        recommendations = self._generate_recommendations(recent, trends)

        # Calculate self-awareness score
        # Based on: coverage of metrics, recency of observations, diversity
        coverage = len(self.metrics_history) / 10  # Expect at least 10 metrics
        recency = min(1.0, len(recent) / 50)  # At least 50 recent observations
        diversity = len(set(obs.observation_type for obs in recent)) / 5

        awareness = (coverage + recency + diversity) / 3

        return MetaReport(
            timestamp=datetime.now(),
            system_health=health,
            observations=recent,
            trends=trends,
            recommendations=recommendations,
            self_awareness_score=round(awareness, 3),
        )

    def _generate_recommendations(
        self, observations: List[SystemObservation], trends: Dict[str, List[float]]
    ) -> List[str]:
        """Generate recommendations based on observations"""
        recommendations = []

        # Check for calibration drift
        calibration_obs = [
            o for o in observations if o.observation_type == ObservationType.CALIBRATION
        ]
        if calibration_obs:
            poor_count = sum(1 for o in calibration_obs if o.status != "normal")
            if poor_count > len(calibration_obs) * 0.3:
                recommendations.append(
                    "Calibration drift detected. Consider recalibrating prediction models."
                )

        # Check for performance degradation
        perf_obs = [
            o for o in observations if o.observation_type == ObservationType.PERFORMANCE
        ]
        if perf_obs:
            slow_count = sum(1 for o in perf_obs if o.value > o.threshold * 1.5)
            if slow_count > len(perf_obs) * 0.2:
                recommendations.append(
                    "Performance degradation detected. Review resource allocation."
                )

        # Check for anomaly frequency
        anomaly_obs = [
            o for o in observations if o.observation_type == ObservationType.ANOMALY
        ]
        if len(anomaly_obs) > 5:
            recommendations.append(
                f"High anomaly frequency ({len(anomaly_obs)} detected). "
                "Investigate root causes."
            )

        # Check for missing observations
        if not trends:
            recommendations.append(
                "Limited observational data. Increase monitoring coverage."
            )

        return recommendations

    def get_system_insights(self) -> Dict[str, Any]:
        """Get insights about system operation"""
        if not self.observations:
            return {"error": "No observations recorded"}

        # Calculate key metrics
        total_obs = len(self.observations)
        type_distribution = {}
        status_distribution = {}

        for obs in self.observations:
            ot = obs.observation_type.value
            type_distribution[ot] = type_distribution.get(ot, 0) + 1

            status_distribution[obs.status] = status_distribution.get(obs.status, 0) + 1

        # Trend analysis
        trending_up = []
        trending_down = []

        for metric, values in self.metrics_history.items():
            if len(values) >= 5:
                recent = list(values)[-5:]
                if all(recent[i] <= recent[i + 1] for i in range(len(recent) - 1)):
                    trending_up.append(metric)
                elif all(recent[i] >= recent[i + 1] for i in range(len(recent) - 1)):
                    trending_down.append(metric)

        return {
            "total_observations": total_obs,
            "observation_types": type_distribution,
            "status_distribution": status_distribution,
            "metrics_tracked": len(self.metrics_history),
            "trending_up": trending_up,
            "trending_down": trending_down,
            "self_awareness": self.generate_meta_report().self_awareness_score,
        }


class AnomalyDetector:
    """Helper class for anomaly detection"""

    def detect(self, values: List[float]) -> List[int]:
        """
        Detect anomalous indices in value series.

        Returns list of indices where anomalies detected.
        """
        if len(values) < 3:
            return []

        anomalies = []
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0

        if std == 0:
            return []

        for i, value in enumerate(values):
            z_score = abs(value - mean) / std
            if z_score > 2.0:  # 2 sigma
                anomalies.append(i)

        return anomalies


class PerformanceTracker:
    """Helper class for performance tracking"""

    def __init__(self):
        self.benchmarks: Dict[str, float] = {}

    def set_benchmark(self, operation: str, target_ms: float):
        """Set performance benchmark for operation"""
        self.benchmarks[operation] = target_ms

    def check_performance(self, operation: str, actual_ms: float) -> Dict[str, Any]:
        """Check performance against benchmark"""
        benchmark = self.benchmarks.get(operation, 50.0)
        ratio = actual_ms / benchmark if benchmark > 0 else 0

        return {
            "operation": operation,
            "actual_ms": actual_ms,
            "benchmark_ms": benchmark,
            "ratio": ratio,
            "meets_slo": ratio <= 1.0,
            "status": "good"
            if ratio <= 1.0
            else "slow"
            if ratio <= 2.0
            else "critical",
        }
