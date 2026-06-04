"""
C4 Neural Fingerprint — ONNX + PyTorch Classification for C4REQBER
=====================================================================

Production-grade C4 text classifier using the best c4factory model:
- Neural: c4_classifier_best.pt (96.5% val accuracy, mDeBERTa-v3-base)
- ONNX: exported lightweight model (~500MB, CPU/GPU inference)
- LLM fallback: when neural model unavailable

Integration: replaces or augments heuristic c4_fingerprint with learned classifier.

Usage:
    from src.c4.neural_classifier.neural_fingerprint import NeuralFingerprint

    fp = NeuralFingerprint()
    result = fp.classify("Quantum entanglement suggests non-local correlations")
    print(result.coordinates)  # (2, 1, 2)  → Future, Abstract, System
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, TYPE_CHECKING


if TYPE_CHECKING:
    from src.c4.neural_classifier.architectures.c4_router import C4RouterModel  # noqa: F401

from src.c4.neural_classifier.c4_types import C4Classification
from src.c4.state import C4State


logger = logging.getLogger(__name__)

# ─── Paths ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = PROJECT_ROOT / "models" / "c4factory"

PYTORCH_MODEL = MODELS_DIR / "c4_classifier_best.pt"
ONNX_MODEL = MODELS_DIR / "c4_classifier.onnx"
CONFIG_JSON = MODELS_DIR / "config.json"

# ─── Optional deps ──────────────────────────────────────────────────
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

try:
    import torch
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from transformers import DebertaV2Tokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class NeuralFingerprint:
    """
    Unified C4 fingerprinting interface.

    Tries inference backends in order:
        1. ONNX Runtime (fastest, ~50ms CPU, ~11ms GPU)
        2. PyTorch (highest accuracy, 96.5%)
        3. LLM-based (always available, ~500ms)

    All backends return canonical C4 coordinates: (Time, Scale, Agency).
    """

    # Model was trained with mDeBERTa-v3-base
    TOKENIZER_NAME: str = "microsoft/mdeberta-v3-base"
    MAX_LENGTH: int = 256

    def __init__(
        self,
        *,
        prefer_onnx: bool = True,
        allow_pytorch: bool = True,
        allow_llm: bool = True,
    ):
        self.prefer_onnx = prefer_onnx
        self.allow_pytorch = allow_pytorch
        self.allow_llm = allow_llm

        self._onnx_session: ort.InferenceSession | None = None
        self._pytorch_model: Any | None = None
        self._tokenizer: DebertaV2Tokenizer | None = None
        self._backend: str = "none"

        self._load()

    # ─── Public API ─────────────────────────────────────────────────

    def classify(self, text: str) -> C4Classification:
        """
        Classify text into C4 coordinates.

        Returns C4Classification with state, confidence, and probabilities.
        """
        if not text or not text.strip():
            raise ValueError("text must be non-empty")

        if self._backend == "onnx":
            return self._classify_onnx(text)
        elif self._backend == "pytorch":
            return self._classify_pytorch(text)
        elif self._backend == "llm":
            return self._classify_llm(text)
        else:
            return self._classify_heuristic(text)

    @property
    def backend(self) -> str:
        return self._backend

    @property
    def is_available(self) -> bool:
        return self._backend != "none"

    # ─── Internal: Loading ──────────────────────────────────────────

    def _load(self) -> None:
        """Try to load the best available backend."""
        # 1. ONNX (fastest)
        if self.prefer_onnx and ONNX_AVAILABLE and ONNX_MODEL.exists():
            try:
                self._load_onnx()
                self._backend = "onnx"
                logger.info(f"NeuralFingerprint: ONNX backend loaded ({ONNX_MODEL.name})")
                return
            except Exception as e:
                logger.warning(f"ONNX load failed: {e}")

        # 2. PyTorch (most accurate)
        if self.allow_pytorch and TORCH_AVAILABLE and PYTORCH_MODEL.exists():
            try:
                self._load_pytorch()
                self._backend = "pytorch"
                logger.info(f"NeuralFingerprint: PyTorch backend loaded ({PYTORCH_MODEL.name})")
                return
            except Exception as e:
                logger.warning(f"PyTorch load failed: {e}")

        # 3. LLM fallback
        if self.allow_llm:
            self._backend = "llm"
            logger.info("NeuralFingerprint: LLM fallback backend")
            return

        self._backend = "none"
        logger.warning("NeuralFingerprint: no backend available")

    def _load_tokenizer(self) -> None:
        if self._tokenizer is None and TRANSFORMERS_AVAILABLE:
            self._tokenizer = DebertaV2Tokenizer.from_pretrained(self.TOKENIZER_NAME)

    def _load_onnx(self) -> None:
        if not ONNX_AVAILABLE:
            raise ImportError("onnxruntime required. Install: pip install onnxruntime")
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        self._onnx_session = ort.InferenceSession(str(ONNX_MODEL), providers=providers)
        self._load_tokenizer()

    def _load_pytorch(self) -> None:
        if not TORCH_AVAILABLE or not TRANSFORMERS_AVAILABLE:
            raise ImportError("torch + transformers required")

        from src.c4.neural_classifier.architectures.c4_router import C4ClassifierModel

        # Load config
        config = self._infer_config()
        self._pytorch_model = C4ClassifierModel(
            base_model=config.get("base_model", self.TOKENIZER_NAME),
            hidden_size=config.get("hidden_size", 768),
        )

        ckpt = torch.load(str(PYTORCH_MODEL), map_location="cpu")
        self._pytorch_model.load_state_dict(ckpt.get("model_state_dict", ckpt))
        self._pytorch_model.eval()
        self._load_tokenizer()

    def _infer_config(self) -> dict:
        """Infer model config from stored JSON or defaults."""
        if CONFIG_JSON.exists():
            with open(CONFIG_JSON) as f:
                return json.load(f)
        # Default: the model was trained with mDeBERTa-v3-base
        return {
            "base_model": self.TOKENIZER_NAME,
            "hidden_size": 768,
            "architecture": "C4ClassifierModel",
        }

    # ─── Internal: Inference ────────────────────────────────────────

    def _tokenize(self, text: str) -> dict:
        self._load_tokenizer()
        if self._tokenizer is None:
            raise RuntimeError("Tokenizer not available")
        return self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self.MAX_LENGTH,
            padding="max_length",
        )

    def _classify_onnx(self, text: str) -> C4Classification:
        tokens = self._tokenize(text)
        input_ids = tokens["input_ids"].numpy()
        attention_mask = tokens["attention_mask"].numpy()

        assert self._onnx_session is not None
        outputs = self._onnx_session.run(
            None,
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
            },
        )
        # ONNX export order: logits_t, logits_d, logits_i
        logits_t, logits_d, logits_i = outputs[0], outputs[1], outputs[2]

        return self._build_result(
            text=text,
            logits_t=logits_t[0],
            logits_d=logits_d[0],
            logits_i=logits_i[0],
            source="onnx",
        )

    def _classify_pytorch(self, text: str) -> C4Classification:
        tokens = self._tokenize(text)
        with torch.no_grad():
            assert self._pytorch_model is not None
            outputs = self._pytorch_model(**tokens)

        return self._build_result(
            text=text,
            logits_t=outputs["logits_t"][0].numpy(),
            logits_d=outputs["logits_d"][0].numpy(),
            logits_i=outputs["logits_i"][0].numpy(),
            source="pytorch",
        )

    def _classify_llm(self, text: str) -> C4Classification:
        """LLM-based fallback using the c4factory prompt engineering."""
        from src.c4.neural_classifier.llm_classifier import C4Classifier

        clf = C4Classifier(backend="groq")  # or auto-detect best available
        result = clf.classify(text)
        return C4Classification(
            state=result.state,
            text=text,
            confidence=getattr(result, "confidence", 0.9),
            source="llm",
            model=getattr(result, "model", "groq"),
        )

    def _classify_heuristic(self, text: str) -> C4Classification:
        """Last resort: keyword-based heuristic from c4-classifier demo."""
        from src.c4.neural_classifier.heuristic_classifier import classify as heuristic_classify

        t, s, a = heuristic_classify(text)
        return C4Classification(
            state=C4State(t, s, a),
            text=text,
            confidence=0.5,
            source="heuristic",
            model="keyword",
        )

    def _build_result(
        self,
        text: str,
        logits_t: np.ndarray,
        logits_d: np.ndarray,
        logits_i: np.ndarray,
        source: str,
    ) -> C4Classification:
        """Build C4Classification from raw logits."""
        import numpy as np

        # Softmax for probabilities
        probs_t = self._softmax(logits_t)
        probs_d = self._softmax(logits_d)
        probs_i = self._softmax(logits_i)

        pred_t = int(np.argmax(probs_t))
        pred_d = int(np.argmax(probs_d))
        pred_i = int(np.argmax(probs_i))

        # Confidence = mean of max probabilities
        confidence = float((probs_t.max() + probs_d.max() + probs_i.max()) / 3.0)

        return C4Classification(
            state=C4State(pred_t, pred_d, pred_i),
            text=text,
            confidence=confidence,
            probabilities=(probs_t.tolist(), probs_d.tolist(), probs_i.tolist()),
            source=source,
            model="c4_classifier_best",
        )

    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        import numpy as np
        exp = np.exp(x - np.max(x))
        return exp / exp.sum()


# ─── Convenience factory ────────────────────────────────────────────

def get_neural_fingerprint() -> NeuralFingerprint:
    """Get or create the singleton NeuralFingerprint instance."""
    return NeuralFingerprint()


# ─── Integration hook for c4_fingerprint MCP tool ───────────────────

async def neural_c4_fingerprint(text: str) -> dict:
    """
    Drop-in replacement for c4_fingerprint using neural backend.

    Returns dict compatible with existing MCP tool response format.
    """
    fp = get_neural_fingerprint()
    result = fp.classify(text)

    return {
        "coordinates": result.coordinates,
        "label": result.label,
        "confidence": result.confidence,
        "probabilities": result.probabilities,
        "backend": fp.backend,
        "model": result.model,
    }
