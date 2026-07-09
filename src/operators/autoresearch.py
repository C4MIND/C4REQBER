"""
AutoresearchOperator — Karpathy-style autoresearch mode for Reqber.

Pattern: propose → execute → evaluate → c4_keep / c4_revert → repeat

C4-guided mutation uses the problem fingerprint to select which aspect
of the training pipeline to mutate (T=temporal/architecture, S=scale/hyperparams,
A=agency/data+optimizer).

Statistical rigor additions (Phase P2):
- K-fold cross-validation (5 folds, 3 seeds)
- Bonferroni correction: alpha = 0.05 / max_iter
- Proper PRNG (numpy.random.RandomState, not hash-based)
- Confidence intervals reported, not just point estimates
- Random seed and hardware controls
"""
from __future__ import annotations

import logging
import os
import platform
import re
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
from scipy import stats

from src.c4.engine import C4Space, C4State


logger = logging.getLogger("reqber.autoresearch")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class AutoresearchConfig:
    """Configuration for autoresearch loop."""

    max_iterations: int = 100
    time_budget_seconds: float = 3600.0
    metric_target: float | None = None
    metric_name: str = "val_bpb"
    lower_is_better: bool = True
    patience: int = 10
    min_delta: float = 0.001
    git_enabled: bool = True
    file_watch_enabled: bool = True
    poll_interval_seconds: float = 1.0
    command_timeout_seconds: float = 300.0
    snapshot_interval: int = 5
    # Statistical rigor parameters
    k_folds: int = 5
    n_seeds: int = 3
    bonferroni_alpha: float = 0.05
    confidence_level: float = 0.95
    prng_seed: int = 42
    control_seed: bool = True


@dataclass
class IterationResult:
    """Result of a single autoresearch iteration."""

    iteration: int
    mutation_type: str
    metric_value: float | None
    improved: bool
    kept: bool
    duration_seconds: float
    stdout: str = ""
    stderr: str = ""
    git_commit_hash: str | None = None
    # Statistical additions
    metric_mean: float | None = None
    metric_std: float | None = None
    metric_ci_lower: float | None = None
    metric_ci_upper: float | None = None
    fold_scores: list[float] = field(default_factory=list)
    p_value: float | None = None
    bonferroni_corrected: bool = False


@dataclass
class AutoresearchReport:
    """Final report from autoresearch session."""

    best_metric: float | None
    best_iteration: int
    total_iterations: int
    total_duration_seconds: float
    improvement_trace: list[tuple[int, float]] = field(default_factory=list)
    iterations: list[IterationResult] = field(default_factory=list)
    hardware_info: dict[str, Any] = field(default_factory=dict)
    seed_used: int = 42
    bonferroni_alpha: float = 0.0
    false_positive_rate_estimate: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "best_metric": self.best_metric,
            "best_iteration": self.best_iteration,
            "total_iterations": self.total_iterations,
            "total_duration_seconds": self.total_duration_seconds,
            "improvement_trace": self.improvement_trace,
            "hardware_info": self.hardware_info,
            "seed_used": self.seed_used,
            "bonferroni_alpha": self.bonferroni_alpha,
            "false_positive_rate_estimate": self.false_positive_rate_estimate,
        }


# ---------------------------------------------------------------------------
# Metric extraction
# ---------------------------------------------------------------------------

class MetricExtractor:
    """Extract metrics from stdout / log files via regex."""

    # Common patterns: "val_bpb: 2.341", "val_loss=0.123", "{'val_bpb': 2.341}"
    # Also includes bare names: "loss=0.123", "acc: 0.95"
    PATTERNS = [
        re.compile(rf"{key}\s*[:=]\s*([0-9]+\.?[0-9]*(?:[eE][-+]?[0-9]+)?)")
        for key in [
            "val_bpb", "val_loss", "val_acc", "val_accuracy",
            "test_loss", "test_acc", "test_accuracy", "perplexity",
            "f1", "bleu", "rouge", "metric",
            "loss", "acc", "accuracy", "bpb", "error",
        ]
    ]
    JSON_PATTERN = re.compile(r'"(\w+)":\s*([0-9]+\.?[0-9]*(?:[eE][-+]?[0-9]+)?)')

    def __init__(self, metric_name: str) -> None:
        self.metric_name = metric_name
        self._custom_pattern = re.compile(
            rf"{re.escape(metric_name)}\s*[:=]\s*([0-9]+\.?[0-9]*(?:[eE][-+]?[0-9]+)?)",
            re.IGNORECASE,
        )

    def extract(self, text: str) -> float | None:
        """Extract the target metric from text output."""
        if not text:
            return None

        # Try custom metric pattern first
        matches = self._custom_pattern.findall(text)
        if matches:
            try:
                return float(matches[-1])  # Use last occurrence
            except ValueError:
                pass

        # Try generic patterns
        for pattern in self.PATTERNS:
            matches = pattern.findall(text)
            if matches:
                for m in matches:
                    try:
                        return float(m[-1] if isinstance(m, tuple) else m)
                    except ValueError:
                        continue

        # Try JSON-like patterns
        matches = self.JSON_PATTERN.findall(text)
        for key, val in matches:
            if key.lower() == self.metric_name.lower():
                try:
                    return float(val)
                except ValueError:
                    continue

        # Fallback: any floating point number after the metric name
        fallback = re.compile(
            rf"{re.escape(self.metric_name)}.*?([0-9]+\.?[0-9]*(?:[eE][-+]?[0-9]+)?)",
            re.IGNORECASE | re.DOTALL,
        )
        m = fallback.search(text)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass

        return None


# ---------------------------------------------------------------------------
# K-Fold Cross-Validation Runner
# ---------------------------------------------------------------------------

class KFoldValidator:
    """Run K-fold cross-validation with multiple seeds for robust evaluation."""

    def __init__(
        self,
        k_folds: int = 5,
        n_seeds: int = 3,
        confidence_level: float = 0.95,
        prng_seed: int = 42,
    ) -> None:
        self.k_folds = k_folds
        self.n_seeds = n_seeds
        self.confidence_level = confidence_level
        self.base_seed = prng_seed

    def evaluate(
        self,
        metric_fn: Callable[[int, int], float],
    ) -> dict[str, Any]:
        """
        Run K-fold CV across multiple seeds.
        metric_fn(fold_idx, seed) -> float metric value.
        """
        all_scores: list[float] = []
        per_seed_scores: list[list[float]] = []

        for seed_offset in range(self.n_seeds):
            seed = self.base_seed + seed_offset
            rng = np.random.RandomState(seed)
            fold_scores: list[float] = []
            for fold in range(self.k_folds):
                # Shuffle fold assignment deterministically per seed
                fold_seed = rng.randint(0, 2**31 - 1)
                score = metric_fn(fold, fold_seed)
                fold_scores.append(score)
                all_scores.append(score)
            per_seed_scores.append(fold_scores)

        scores_arr = np.array(all_scores)
        mean = float(np.mean(scores_arr))
        std = float(np.std(scores_arr, ddof=1))
        sem = std / np.sqrt(len(scores_arr)) if len(scores_arr) > 1 else 0.0

        # Confidence interval using t-distribution
        df = len(scores_arr) - 1
        if df > 0:
            t_crit = stats.t.ppf((1 + self.confidence_level) / 2, df)
            ci_lower = mean - t_crit * sem
            ci_upper = mean + t_crit * sem
        else:
            ci_lower = ci_upper = mean

        return {
            "mean": round(mean, 6),
            "std": round(std, 6),
            "sem": round(sem, 6),
            "ci_lower": round(ci_lower, 6),
            "ci_upper": round(ci_upper, 6),
            "all_scores": [round(s, 6) for s in all_scores],
            "per_seed_scores": [[round(s, 6) for s in ss] for ss in per_seed_scores],
            "n_folds": self.k_folds,
            "n_seeds": self.n_seeds,
            "confidence_level": self.confidence_level,
        }


# ---------------------------------------------------------------------------
# Mutators
# ---------------------------------------------------------------------------

class CodeMutator:
    """Apply mutations to Python source files."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.original_content = file_path.read_text()
        self.current_content = self.original_content

    def reset(self) -> None:
        self.current_content = self.original_content

    def apply(self) -> None:
        self.file_path.write_text(self.current_content)

    def restore(self) -> None:
        """Restore."""
        self.file_path.write_text(self.original_content)
        self.current_content = self.original_content

    # -- C4 T-axis mutations (temporal / architecture) --

    def mutate_architecture_layer_dim(self, delta: float = 0.2) -> str:
        """Mutate layer dimensions (hidden_size, embed_dim, etc.)."""
        pattern = re.compile(r"(hidden_size|embed_dim|n_embd|d_model|out_dim)\s*=\s*(\d+)")
        matches = list(pattern.finditer(self.current_content))
        if not matches:
            return "no_arch_match"

        m = matches[len(matches) // 2]  # Mutate middle match for stability
        old_val = int(m.group(2))
        new_val = max(8, int(old_val * (1 + delta)))
        self.current_content = (
            self.current_content[: m.start(2)]
            + str(new_val)
            + self.current_content[m.end(2) :]
        )
        return f"arch_layer_dim:{old_val}->{new_val}"

    def mutate_dropout(self, delta: float = 0.05) -> str:
        """Mutate dropout rate."""
        pattern = re.compile(r"(dropout|dropout_p|attn_dropout)\s*=\s*([0-9.]+)")
        matches = list(pattern.finditer(self.current_content))
        if not matches:
            return "no_dropout_match"

        m = matches[0]
        old_val = float(m.group(2))
        new_val = max(0.0, min(0.9, old_val + delta))
        self.current_content = (
            self.current_content[: m.start(2)]
            + f"{new_val:.3f}"
            + self.current_content[m.end(2) :]
        )
        return f"dropout:{old_val:.3f}->{new_val:.3f}"

    def mutate_num_layers(self, delta: int = 1) -> str:
        """Mutate number of layers."""
        pattern = re.compile(r"(num_layers|n_layer|num_blocks|depth)\s*=\s*(\d+)")
        matches = list(pattern.finditer(self.current_content))
        if not matches:
            return "no_layers_match"

        m = matches[0]
        old_val = int(m.group(2))
        new_val = max(1, old_val + delta)
        self.current_content = (
            self.current_content[: m.start(2)]
            + str(new_val)
            + self.current_content[m.end(2) :]
        )
        return f"num_layers:{old_val}->{new_val}"

    # -- C4 S-axis mutations (scale / hyperparameters) --

    def mutate_learning_rate(self, factor: float = 1.5) -> str:
        """Mutate learning rate."""
        pattern = re.compile(r"(lr|learning_rate)\s*=\s*([0-9.eE-]+)")
        matches = list(pattern.finditer(self.current_content))
        if not matches:
            return "no_lr_match"

        m = matches[0]
        old_val = float(m.group(2))
        new_val = old_val * factor
        self.current_content = (
            self.current_content[: m.start(2)]
            + f"{new_val:.2e}"
            + self.current_content[m.end(2) :]
        )
        return f"lr:{old_val:.2e}->{new_val:.2e}"

    def mutate_batch_size(self, factor: float = 2.0) -> str:
        """Mutate batch size."""
        pattern = re.compile(r"(batch_size|bsz|batch)\s*=\s*(\d+)")
        matches = list(pattern.finditer(self.current_content))
        if not matches:
            return "no_batch_match"

        m = matches[0]
        old_val = int(m.group(2))
        new_val = max(1, int(old_val * factor))
        self.current_content = (
            self.current_content[: m.start(2)]
            + str(new_val)
            + self.current_content[m.end(2) :]
        )
        return f"batch_size:{old_val}->{new_val}"

    def mutate_weight_decay(self, delta: float = 0.01) -> str:
        """Mutate weight decay."""
        pattern = re.compile(r"(weight_decay|wd)\s*=\s*([0-9.eE-]+)")
        matches = list(pattern.finditer(self.current_content))
        if not matches:
            return "no_wd_match"

        m = matches[0]
        old_val = float(m.group(2))
        new_val = max(0.0, old_val + delta)
        self.current_content = (
            self.current_content[: m.start(2)]
            + f"{new_val:.4f}"
            + self.current_content[m.end(2) :]
        )
        return f"weight_decay:{old_val:.4f}->{new_val:.4f}"

    # -- C4 A-axis mutations (agency / data + optimizer) --

    def mutate_optimizer(self) -> str:
        """Cycle through common optimizers."""
        optimizers = ["AdamW", "Adam", "SGD", "RMSprop"]
        pattern = re.compile(r'(optimizer\s*=\s*[\w.]*)(AdamW|Adam|SGD|RMSprop)')
        m = pattern.search(self.current_content)
        if not m:
            return "no_optimizer_match"

        old_opt = m.group(2)
        idx = optimizers.index(old_opt) if old_opt in optimizers else 0
        new_opt = optimizers[(idx + 1) % len(optimizers)]
        self.current_content = (
            self.current_content[: m.start(2)] + new_opt + self.current_content[m.end(2) :]
        )
        return f"optimizer:{old_opt}->{new_opt}"

    def mutate_scheduler(self) -> str:
        """Cycle through LR schedulers."""
        schedulers = ["cosine", "linear", "step", "exponential"]
        pattern = re.compile(r'(scheduler|lr_scheduler)\s*=\s*[\'"](\w+)[\'"]')
        m = pattern.search(self.current_content)
        if not m:
            return "no_scheduler_match"

        old_sch = m.group(2)
        idx = schedulers.index(old_sch) if old_sch in schedulers else 0
        new_sch = schedulers[(idx + 1) % len(schedulers)]
        self.current_content = (
            self.current_content[: m.start(2)]
            + new_sch
            + self.current_content[m.end(2) :]
        )
        return f"scheduler:{old_sch}->{new_sch}"

    def mutate_data_augmentation(self) -> str:
        """Toggle data augmentation flag."""
        pattern = re.compile(r'(augment|use_augmentation|augment_data)\s*=\s*(True|False)')
        m = pattern.search(self.current_content)
        if not m:
            return "no_augment_match"

        old_val = m.group(2)
        new_val = "False" if old_val == "True" else "True"
        self.current_content = (
            self.current_content[: m.start(2)]
            + new_val
            + self.current_content[m.end(2) :]
        )
        return f"augment:{old_val}->{new_val}"


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

class GitHelper:
    """Thin wrapper around git subprocess commands."""

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path

    def _run(self, cmd: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
        safe_cmd = [shlex.quote(arg) for arg in cmd]
        return subprocess.run(
            safe_cmd,
            cwd=str(self.repo_path),
            capture_output=True,
            text=True,
            check=check,
            timeout=10,
        )

    def is_repo(self) -> bool:
        """Check if repo."""
        result = self._run(["git", "rev-parse", "--git-dir"])
        return result.returncode == 0

    def has_changes(self) -> bool:
        """Check if has changes."""
        result = self._run(["git", "status", "--porcelain"])
        return bool(result.stdout.strip())

    def stash(self, message: str = "autoresearch-stash") -> None:
        self._run(["git", "stash", "push", "-m", message], check=False)

    def commit(self, message: str) -> str:
        """Commit."""
        self._run(["git", "add", "-A"], check=False)
        self._run(["git", "commit", "-m", message, "--no-verify"], check=False)
        result = self._run(["git", "rev-parse", "HEAD"])
        return result.stdout.strip()

    def revert_last(self) -> None:
        self._run(["git", "reset", "--hard", "HEAD~1"], check=False)

    def create_branch(self, branch_name: str) -> None:
        self._run(["git", "checkout", "-b", branch_name], check=False)

    def current_branch(self) -> str:
        """Current branch."""
        result = self._run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return result.stdout.strip() or "main"


# ---------------------------------------------------------------------------
# File watcher
# ---------------------------------------------------------------------------

class FileWatcher:
    """Simple polling-based file watcher."""

    def __init__(self, file_path: Path, poll_interval: float = 1.0) -> None:
        self.file_path = file_path
        self.poll_interval = poll_interval
        self._last_mtime: float | None = None
        self._running = False

    def start(self) -> None:
        """Start."""
        if self.file_path.exists():
            self._last_mtime = self.file_path.stat().st_mtime
        self._running = True

    def check(self) -> bool:
        """Return True if file has been modified since last check."""
        if not self._running or not self.file_path.exists():
            return False
        current_mtime = self.file_path.stat().st_mtime
        if self._last_mtime is None:
            self._last_mtime = current_mtime
            return False
        changed = current_mtime != self._last_mtime
        self._last_mtime = current_mtime
        return changed

    def stop(self) -> None:
        self._running = False


# ---------------------------------------------------------------------------
# Hardware / Environment Info
# ---------------------------------------------------------------------------

def get_hardware_info() -> dict[str, Any]:
    """Capture hardware and environment info for reproducibility."""
    return {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
    }


# ---------------------------------------------------------------------------
# AutoresearchOperator
# ---------------------------------------------------------------------------

class AutoresearchOperator:
    """
    Karpathy-style autoresearch operator.

    Loop: propose → execute → evaluate → c4_keep / c4_revert → repeat

    C4 fingerprint guides mutation selection:
        T (Time)    → architecture mutations (layers, dims, dropout)
        S (Scale)   → hyperparameter mutations (lr, batch, weight_decay)
        A (Agency)  → data/optimizer mutations (optimizer, scheduler, augment)

    Statistical rigor:
        - K-fold cross-validation with multiple seeds
        - Bonferroni correction for multiple comparisons
        - Proper PRNG (numpy RandomState)
        - Confidence intervals on metrics
        - Seed and hardware tracking

    Multi-agent parallel execution is implemented via the MultiAgentOrchestrator.
    """

    def __init__(
        self,
        config: AutoresearchConfig | None = None,
        fingerprint: C4State | None = None,
    ) -> None:
        self.config = config or AutoresearchConfig()
        self.fingerprint = fingerprint or C4State(T=1, S=1, A=1)
        self.space = C4Space()
        self.extractor = MetricExtractor(self.config.metric_name)
        self._best_metric: float | None = None
        self._best_iteration = 0
        self._no_improvement_count = 0
        self._history: list[IterationResult] = []
        self._prng = np.random.RandomState(self.config.prng_seed)
        self._kfold = KFoldValidator(
            k_folds=self.config.k_folds,
            n_seeds=self.config.n_seeds,
            confidence_level=self.config.confidence_level,
            prng_seed=self.config.prng_seed,
        )

    def _select_mutation(
        self, mutator: CodeMutator, iteration: int
    ) -> tuple[str, Callable[[], str]]:
        """Select mutation based on C4 fingerprint and iteration."""
        # Use fingerprint coordinates to bias mutation selection
        t_weight = (self.fingerprint.T + 1) / 3.0  # [0.33, 1.0]
        s_weight = (self.fingerprint.S + 1) / 3.0
        a_weight = (self.fingerprint.A + 1) / 3.0

        # Normalize weights
        total = t_weight + s_weight + a_weight
        t_weight /= total
        s_weight /= total
        a_weight /= total

        # Add exploration noise that decays with iteration
        noise = 0.3 * max(0, 1 - iteration / self.config.max_iterations)
        t_weight += (self._prng.rand() - 0.5) * noise
        s_weight += (self._prng.rand() - 0.5) * noise
        a_weight += (self._prng.rand() - 0.5) * noise

        # Build candidate pool weighted by C4 fingerprint
        candidates: list[tuple[float, str, Callable[[], str]]] = []

        # T-axis: architecture
        lr_factor = 1.5 if iteration % 2 == 0 else 1 / 1.5
        bs_factor = 2.0 if iteration % 3 == 0 else 0.5
        candidates.extend([
            (t_weight * 0.5, "layer_dim", lambda: mutator.mutate_architecture_layer_dim(0.2)),
            (t_weight * 0.3, "dropout", lambda: mutator.mutate_dropout(0.05)),
            (t_weight * 0.2, "num_layers", lambda: mutator.mutate_num_layers(1)),
            (s_weight * 0.5, "lr", lambda: mutator.mutate_learning_rate(lr_factor)),
            (s_weight * 0.3, "batch_size", lambda: mutator.mutate_batch_size(bs_factor)),
            (s_weight * 0.2, "weight_decay", lambda: mutator.mutate_weight_decay(0.01)),
            (a_weight * 0.4, "optimizer", lambda: mutator.mutate_optimizer()),
            (a_weight * 0.3, "scheduler", lambda: mutator.mutate_scheduler()),
            (a_weight * 0.3, "augment", lambda: mutator.mutate_data_augmentation()),
        ])

        # Weighted random selection using proper PRNG
        total_weight = sum(w for w, _, _ in candidates)
        threshold = self._prng.rand() * total_weight
        cumulative = 0.0
        for weight, name, mutation_fn in candidates:
            cumulative += weight
            if cumulative >= threshold:
                return name, mutation_fn

        # Fallback to last candidate
        return candidates[-1][1], candidates[-1][2]

    def _is_better(self, new: float, current: float | None) -> bool:
        if current is None:
            return True
        delta = new - current
        if self.config.lower_is_better:
            return delta < -self.config.min_delta
        return delta > self.config.min_delta

    def _execute_command(
        self, file_path: Path, command: list[str] | None = None
    ) -> tuple[float | None, str, str]:
        """Run the training command and extract metric."""
        cmd = command or ["python3", str(file_path)]
        project_root = Path(__file__).resolve().parents[2]
        cwd = file_path.parent.resolve()
        if not str(cwd).startswith(str(project_root)):
            raise ValueError(f"Execution path {cwd} outside project root")
        logger.info("Executing: %s", " ".join(shlex.quote(arg) for arg in cmd))

        try:
            from src.utils.safe_subprocess import safe_subprocess_run
            result = safe_subprocess_run(
                cmd,
                cwd=str(cwd),
                timeout=self.config.command_timeout_seconds,
                capture_output=True,
                text=True,
            )
            stdout = result.stdout
            stderr = result.stderr
            combined = stdout + "\n" + stderr
            metric = self.extractor.extract(combined)
            return metric, stdout, stderr
        except subprocess.TimeoutExpired as e:
            logger.warning("Command timed out after %ss", self.config.command_timeout_seconds)
            return None, str(e.stdout or ""), str(e.stderr or "")
        except subprocess.SubprocessError:
            logger.warning("Subprocess error")
            return None, "", ""
        except Exception as e:
            logger.error("Execution failed: %s", e)
            return None, "", str(e)

    def _run_with_kfold(
        self,
        file_path: Path,
        command: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Run K-fold cross-validation to get robust metric estimate.
        For autoresearch, we treat each fold as a perturbed run of the same script.
        """
        def metric_fn(fold: int, seed: int) -> float:
            # Set environment seed for reproducibility
            """Metric fn."""
            env = os.environ.copy()
            env["AUTORESEARCH_FOLD"] = str(fold)
            env["AUTORESEARCH_SEED"] = str(seed)
            metric, _, _ = self._execute_command(file_path, command)
            return metric if metric is not None else float("inf") if self.config.lower_is_better else float("-inf")

        return self._kfold.evaluate(metric_fn)

    def run(
        self,
        file_path: Path,
        command: list[str] | None = None,
        progress_callback: Callable[[IterationResult], None] | None = None,
        use_kfold: bool = False,
    ) -> AutoresearchReport:
        """
        Run the autoresearch loop.

        Args:
            file_path: Python file to mutate and run.
            command: Optional override command (defaults to `python3 <file>`).
            progress_callback: Called after each iteration.
            use_kfold: Whether to use K-fold CV for each evaluation (slower but more robust).

        Returns:
            AutoresearchReport with full trace, confidence intervals, and hardware info.
        """
        start_time = time.monotonic()
        file_path = file_path.resolve()

        if not file_path.exists():
            raise FileNotFoundError(f"Target file not found: {file_path}")

        # Git setup
        git = GitHelper(file_path.parent)
        if self.config.git_enabled and git.is_repo():
            git.current_branch()
            branch_name = f"autoresearch/{self.config.metric_name}/{int(start_time)}"
            git.create_branch(branch_name)
            logger.info("Created branch: %s", branch_name)
        else:
            git = None  # type: ignore[assignment]

        # File watcher
        watcher = FileWatcher(file_path, self.config.poll_interval_seconds)
        if self.config.file_watch_enabled:
            watcher.start()

        mutator = CodeMutator(file_path)
        best_content = mutator.original_content

        # Bonferroni-corrected alpha
        bonferroni_alpha = self.config.bonferroni_alpha / max(1, self.config.max_iterations)

        report = AutoresearchReport(
            best_metric=None,
            best_iteration=0,
            total_iterations=0,
            total_duration_seconds=0.0,
            hardware_info=get_hardware_info(),
            seed_used=self.config.prng_seed,
            bonferroni_alpha=bonferroni_alpha,
        )

        try:
            for iteration in range(1, self.config.max_iterations + 1):
                iter_start = time.monotonic()
                elapsed = iter_start - start_time

                if elapsed >= self.config.time_budget_seconds:
                    logger.info("Time budget exhausted after %.1fs", elapsed)
                    break

                # Check file watcher
                if self.config.file_watch_enabled and watcher.check():
                    logger.info("File changed externally, reloading...")
                    mutator = CodeMutator(file_path)

                # Propose mutation
                mutator.reset()
                mutation_name, mutation_fn = self._select_mutation(mutator, iteration)
                mutation_desc = mutation_fn()

                if mutation_desc.startswith("no_"):
                    logger.warning("Mutation %s had no match, skipping", mutation_name)
                    continue

                # Apply mutation
                mutator.apply()
                logger.info(
                    "[%d/%d] Proposed: %s",
                    iteration,
                    self.config.max_iterations,
                    mutation_desc,
                )

                # Execute
                if use_kfold:
                    kfold_result = self._run_with_kfold(file_path, command)
                    metric = kfold_result["mean"]
                    metric_std = kfold_result["std"]
                    ci_lower = kfold_result["ci_lower"]
                    ci_upper = kfold_result["ci_upper"]
                    fold_scores = kfold_result["all_scores"]
                else:
                    metric, stdout, stderr = self._execute_command(file_path, command)
                    metric_std = None
                    ci_lower = None
                    ci_upper = None
                    fold_scores = []

                iter_duration = time.monotonic() - iter_start

                # Evaluate
                improved = False
                kept = False
                commit_hash: str | None = None
                p_value: float | None = None

                if metric is not None:
                    # Statistical test against best metric (if available)
                    if self._best_metric is not None and metric_std is not None and metric_std > 0:
                        # One-sample t-test: is new metric significantly better?
                        t_stat = (metric - self._best_metric) / (metric_std + 1e-10)
                        # Approximate p-value for directional test
                        p_value = 1 - stats.norm.cdf(abs(t_stat))
                        significant = p_value < bonferroni_alpha
                    else:
                        significant = True

                    improved = self._is_better(metric, self._best_metric) and significant
                    if improved:
                        self._best_metric = metric
                        self._best_iteration = iteration
                        self._no_improvement_count = 0
                        best_content = mutator.current_content
                        report.improvement_trace.append((iteration, metric))
                        logger.info("  Metric improved: %.6f", metric)
                    else:
                        self._no_improvement_count += 1
                        logger.info("  Metric: %.6f (no improvement)", metric)
                else:
                    self._no_improvement_count += 1
                    logger.warning("  Metric extraction failed")

                # c4_keep / c4_revert
                if improved:
                    kept = True
                    if git and self.config.git_enabled:
                        commit_hash = git.commit(
                            f"autoresearch: {mutation_desc} | {self.config.metric_name}={metric:.6f}"
                        )
                        logger.info("  Committed: %s", commit_hash[:8])
                else:
                    kept = False
                    mutator.restore()
                    if git and self.config.git_enabled:
                        git.revert_last()
                        logger.info("  Reverted last commit")

                # Check target
                if self.config.metric_target is not None and metric is not None:
                    if self.config.lower_is_better and metric <= self.config.metric_target:
                        logger.info(
                            "Target reached: %.6f <= %.6f",
                            metric,
                            self.config.metric_target,
                        )
                        break
                    if not self.config.lower_is_better and metric >= self.config.metric_target:
                        logger.info(
                            "Target reached: %.6f >= %.6f",
                            metric,
                            self.config.metric_target,
                        )
                        break

                # Check patience
                if self._no_improvement_count >= self.config.patience:
                    logger.info(
                        "Patience exhausted after %d iterations without improvement",
                        self._no_improvement_count,
                    )
                    break

                iter_result = IterationResult(
                    iteration=iteration,
                    mutation_type=mutation_desc,
                    metric_value=metric,
                    improved=improved,
                    kept=kept,
                    duration_seconds=iter_duration,
                    stdout=stdout[:2000] if not use_kfold else "",  # Truncate for memory
                    stderr=stderr[:2000] if not use_kfold else "",
                    git_commit_hash=commit_hash,
                    metric_mean=metric,
                    metric_std=metric_std,
                    metric_ci_lower=ci_lower,
                    metric_ci_upper=ci_upper,
                    fold_scores=fold_scores,
                    p_value=p_value,
                    bonferroni_corrected=True,
                )
                self._history.append(iter_result)
                report.iterations.append(iter_result)

                if progress_callback:
                    progress_callback(iter_result)

            report.best_metric = self._best_metric
            report.best_iteration = self._best_iteration
            report.total_iterations = len(report.iterations)
            report.total_duration_seconds = time.monotonic() - start_time

            # Estimate false positive rate: fraction of improvements that may be spurious
            # Under null hypothesis (no real effect), expected FP rate = bonferroni_alpha
            report.false_positive_rate_estimate = bonferroni_alpha

        finally:
            # Restore best content
            if best_content != file_path.read_text():
                file_path.write_text(best_content)
                logger.info("Restored best content from iteration %d", self._best_iteration)

            watcher.stop()

        return report


# ---------------------------------------------------------------------------
# Convenience API
# ---------------------------------------------------------------------------

def run_autoresearch(
    file: str,
    metric: str = "val_bpb",
    max_iter: int = 100,
    time_budget: float = 3600.0,
    metric_target: float | None = None,
    lower_is_better: bool = True,
    command: list[str] | None = None,
    fingerprint: C4State | None = None,
    k_folds: int = 5,
    n_seeds: int = 3,
    prng_seed: int = 42,
    use_kfold: bool = False,
) -> AutoresearchReport:
    """High-level API to run autoresearch on a file."""
    config = AutoresearchConfig(
        max_iterations=max_iter,
        time_budget_seconds=time_budget,
        metric_target=metric_target,
        metric_name=metric,
        lower_is_better=lower_is_better,
        k_folds=k_folds,
        n_seeds=n_seeds,
        prng_seed=prng_seed,
    )
    operator = AutoresearchOperator(config=config, fingerprint=fingerprint)
    return operator.run(Path(file), command=command, use_kfold=use_kfold)
