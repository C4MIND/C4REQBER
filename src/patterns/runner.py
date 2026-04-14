"""
TURBO-CDI v8.4 - v6 Pattern Runner
Dynamic discovery and execution of v6 legacy simulation patterns.
"""

import os
import sys
import inspect
import importlib
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Ensure patterns directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class PatternRunner:
    """
    Unified runner for v6 legacy patterns.
    Discovers pattern classes dynamically and provides a consistent execution API.
    """

    def __init__(self):
        self._patterns: Dict[str, Any] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._load_errors: Dict[str, str] = {}
        self._discover_patterns()

    def _discover_patterns(self):
        """Dynamically discover and load all pattern modules."""
        patterns_dir = os.path.join(os.path.dirname(__file__), "v6_legacy")
        if not os.path.exists(patterns_dir):
            logger.warning("v6_legacy patterns directory not found")
            return

        for filename in sorted(os.listdir(patterns_dir)):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue
            if filename in ["base.py", "loader.py", "core.py"]:
                continue

            module_name = f"patterns.v6_legacy.{filename[:-3]}"
            pattern_id = filename.replace(".py", "")

            try:
                module = importlib.import_module(module_name)
                pattern_class = self._find_pattern_class(module, filename)

                if pattern_class is None:
                    self._load_errors[pattern_id] = "No pattern class found"
                    continue

                instance = pattern_class()
                self._patterns[pattern_id] = instance

                # Extract metadata
                if hasattr(instance, "get_metadata"):
                    meta = instance.get_metadata()
                elif hasattr(pattern_class, "get_metadata"):
                    meta = pattern_class.get_metadata()
                else:
                    meta = {
                        "pattern_id": pattern_id,
                        "name": pattern_class.__name__,
                        "domain": "unknown",
                    }

                self._metadata[pattern_id] = {
                    "id": pattern_id,
                    "name": meta.get("name", meta.get("pattern_id", pattern_id)),
                    "class": pattern_class.__name__,
                    "domain": meta.get("domain", "unknown"),
                    "description": meta.get("description", meta.get("solution", "")),
                    "has_run": hasattr(instance, "run"),
                    "has_estimate": hasattr(instance, "estimate_resources"),
                }

            except Exception as e:
                logger.warning(f"Failed to load pattern {pattern_id}: {e}")
                self._load_errors[pattern_id] = str(e)

        logger.info(
            f"Pattern discovery complete: {len(self._patterns)} loaded, "
            f"{len(self._load_errors)} failed"
        )

    def _find_pattern_class(self, module, filename: str):
        """Find the main pattern class in a module."""
        candidates = []
        expected_prefix = filename.replace(".py", "").replace("_", "")

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ != module.__name__:
                continue  # Skip imported classes

            # Priority 1: Class name contains "Pattern" and matches file
            if "Pattern" in name:
                candidates.append((name, obj, 1))
            # Priority 2: Class name contains "Pattern"
            elif "Pattern" in name:
                candidates.append((name, obj, 2))
            # Priority 3: Class name loosely matches filename
            elif expected_prefix.lower() in name.lower():
                candidates.append((name, obj, 3))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[2])
        return candidates[0][1]

    def list_patterns(self) -> List[str]:
        """List all loaded pattern IDs."""
        return sorted(self._patterns.keys())

    def get_metadata(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get pattern metadata."""
        return self._metadata.get(pattern_id)

    def get_instance(self, pattern_id: str) -> Optional[Any]:
        """Get pattern instance."""
        return self._patterns.get(pattern_id)

    def get_errors(self) -> Dict[str, str]:
        """Get loading errors."""
        return self._load_errors

    async def run_pattern(
        self,
        pattern_id: str,
        hypothesis: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a pattern with optional hypothesis and parameters."""
        instance = self._patterns.get(pattern_id)
        if instance is None:
            raise ValueError(f"Pattern '{pattern_id}' not found or failed to load")

        if not hasattr(instance, "run"):
            raise ValueError(f"Pattern '{pattern_id}' does not have a run() method")

        start_time = datetime.now()

        try:
            # Some patterns expect a Hypothesis dataclass, others accept dict
            run_method = instance.run
            sig = inspect.signature(run_method)

            kwargs = {}
            if "hypothesis" in sig.parameters:
                hyp_param = sig.parameters["hypothesis"]
                if (
                    hyp_param.annotation is not inspect.Parameter.empty
                    and "Hypothesis" in str(hyp_param.annotation)
                ):
                    from patterns.core import Hypothesis

                    h = hypothesis or {}
                    kwargs["hypothesis"] = Hypothesis(
                        text=h.get("text", ""),
                        title=h.get("title", ""),
                        description=h.get("description", ""),
                        parameters=h.get("parameters", {}),
                        confidence=h.get("confidence", 0.5),
                        keywords=h.get("keywords", []),
                    )
                else:
                    kwargs["hypothesis"] = hypothesis or {}
            if "params" in sig.parameters:
                kwargs["params"] = params or {}
            if "config" in sig.parameters:
                # Try to find and instantiate a Config class from the same module
                config = self._build_config(instance, params or {})
                kwargs["config"] = config

            if asyncio.iscoroutinefunction(run_method):
                result = await run_method(**kwargs)
            else:
                # Run synchronous run() in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: run_method(**kwargs))

            execution_time = (datetime.now() - start_time).total_seconds()

            # Normalize result
            if hasattr(result, "__dict__"):
                result_data = result.__dict__
            elif isinstance(result, dict):
                result_data = result
            else:
                result_data = {"output": str(result)}

            return {
                "pattern_id": pattern_id,
                "status": "completed",
                "result": result_data,
                "execution_time_seconds": execution_time,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.exception(f"Pattern {pattern_id} execution failed")
            return {
                "pattern_id": pattern_id,
                "status": "failed",
                "error": str(e),
                "execution_time_seconds": execution_time,
                "timestamp": datetime.now().isoformat(),
            }

    def _build_config(self, instance, params: Dict[str, Any]) -> Any:
        """Build a config object for patterns that require one."""
        run_method = instance.run
        sig = inspect.signature(run_method)
        config_param = sig.parameters.get("config")
        if config_param is None:
            return params

        annotation = config_param.annotation
        # If annotated as Dict/dict/typing.Dict, pass a plain dict
        if annotation is not inspect.Parameter.empty:
            ann_str = str(annotation)
            if any(t in ann_str for t in ["Dict", "dict", "Mapping"]):
                return params

        module_name = instance.__class__.__module__
        module = sys.modules.get(module_name)
        if module is None:
            return params

        # Look for Config class in the module
        config_class = None
        class_name = instance.__class__.__name__
        possible_names = [
            class_name.replace("Pattern", "Config"),
            class_name + "Config",
            "Config",
        ]
        for name in possible_names:
            if hasattr(module, name):
                config_class = getattr(module, name)
                break

        if config_class is None:
            return params

        try:
            sig_cls = inspect.signature(config_class)
            kwargs = {}
            for param_name, param in sig_cls.parameters.items():
                if param_name in params:
                    kwargs[param_name] = params[param_name]
                elif param.default is not inspect.Parameter.empty:
                    kwargs[param_name] = param.default
            return config_class(**kwargs)
        except Exception:
            return config_class()

    def estimate_resources(self, pattern_id: str) -> Dict[str, Any]:
        """Estimate resources for a pattern."""
        instance = self._patterns.get(pattern_id)
        if instance and hasattr(instance, "estimate_resources"):
            try:
                return instance.estimate_resources()
            except Exception:
                pass
        return {
            "memory_mb": 100,
            "cpu_cores": 1,
            "gpu_required": False,
            "estimated_time_seconds": 60,
        }


# Singleton instance
_runner: Optional[PatternRunner] = None


def get_runner() -> PatternRunner:
    global _runner
    if _runner is None:
        _runner = PatternRunner()
    return _runner
