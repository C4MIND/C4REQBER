#!/usr/bin/env python3
"""
Export c4factory's best PyTorch model to ONNX for lightweight deployment.
============================================================================

Source: models/c4factory/c4_classifier_best.pt (3.1 GB, 96.5% accuracy)
Target: models/c4factory/c4_classifier.onnx (~500MB, same accuracy)

Usage:
    python scripts/export_c4_onnx.py
    python scripts/export_c4_onnx.py --quantize  # INT8 quantized (~125MB)

Requirements:
    pip install torch transformers onnx onnxruntime
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = PROJECT_ROOT / "models" / "c4factory"
PYTORCH_MODEL = MODELS_DIR / "c4_classifier_best.pt"
ONNX_OUTPUT = MODELS_DIR / "c4_classifier.onnx"
CONFIG_OUTPUT = MODELS_DIR / "config.json"


def export_onnx(
    *,
    quantize: bool = False,
    opset: int = 14,
    max_length: int = 256,
) -> Path:
    """
    Export c4_classifier_best.pt to ONNX format.

    Args:
        quantize: Apply dynamic INT8 quantization (4x smaller, slight accuracy loss)
        opset: ONNX opset version
        max_length: Max sequence length for the model

    Returns:
        Path to the exported ONNX file
    """
    import torch
    import torch.onnx
    from transformers import DebertaV2Tokenizer

    from src.c4.neural_classifier.architectures.c4_router import C4ClassifierModel

    if not PYTORCH_MODEL.exists():
        raise FileNotFoundError(f"PyTorch model not found: {PYTORCH_MODEL}")

    logger.info(f"Loading PyTorch model from {PYTORCH_MODEL}")
    logger.info(f"  File size: {PYTORCH_MODEL.stat().st_size / 1e9:.2f} GB")

    # Load model — C4ClassifierModel matches c4factory checkpoint architecture
    model = C4ClassifierModel(
        base_model="microsoft/mdeberta-v3-base",
        hidden_size=768,
    )

    ckpt = torch.load(str(PYTORCH_MODEL), map_location="cpu")
    model.load_state_dict(ckpt.get("model_state_dict", ckpt))
    model.eval()

    # Save config for later loading
    config = {
        "base_model": "microsoft/mdeberta-v3-base",
        "hidden_size": 768,
        "architecture": "C4ClassifierModel",
    }
    with open(CONFIG_OUTPUT, "w") as f:
        json.dump(config, f, indent=2)
    logger.info(f"Saved config to {CONFIG_OUTPUT}")

    # Prepare dummy input
    tokenizer = DebertaV2Tokenizer.from_pretrained(config["base_model"])
    dummy_text = "This is a test sentence for C4 classification."
    inputs = tokenizer(
        dummy_text,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
        padding="max_length",
    )

    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    # Export
    logger.info(f"Exporting to ONNX (opset={opset}, max_length={max_length})...")

    ONNX_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    torch.onnx.export(
        model,
        (input_ids, attention_mask),
        str(ONNX_OUTPUT),
        input_names=["input_ids", "attention_mask"],
        output_names=["logits_t", "logits_d", "logits_i"],
        dynamic_axes={
            "input_ids": {0: "batch_size", 1: "sequence_length"},
            "attention_mask": {0: "batch_size", 1: "sequence_length"},
            "logits_t": {0: "batch_size"},
            "logits_d": {0: "batch_size"},
            "logits_i": {0: "batch_size"},
        },
        opset_version=opset,
        do_constant_folding=True,
    )

    logger.info(f"ONNX model exported to {ONNX_OUTPUT}")
    logger.info(f"  File size: {ONNX_OUTPUT.stat().st_size / 1e6:.1f} MB")

    # Quantization
    if quantize:
        from onnxruntime.quantization import QuantType, quantize_dynamic

        quantized_path = ONNX_OUTPUT.with_suffix(".quantized.onnx")
        logger.info("Applying INT8 dynamic quantization...")

        quantize_dynamic(
            model_input=str(ONNX_OUTPUT),
            model_output=str(quantized_path),
            weight_type=QuantType.QInt8,
        )

        logger.info(f"Quantized model saved to {quantized_path}")
        logger.info(f"  File size: {quantized_path.stat().st_size / 1e6:.1f} MB")
        return quantized_path

    return ONNX_OUTPUT


def verify_onnx(model_path: Path, num_samples: int = 5) -> None:
    """Verify ONNX model produces same outputs as PyTorch."""
    import numpy as np
    import onnxruntime as ort
    import torch
    from transformers import DebertaV2Tokenizer

    from src.c4.neural_classifier.architectures.c4_router import C4ClassifierModel

    logger.info(f"Verifying ONNX model: {model_path}")

    # Load PyTorch model — C4ClassifierModel matches checkpoint architecture
    pt_model = C4ClassifierModel(
        base_model="microsoft/mdeberta-v3-base",
        hidden_size=768,
    )
    ckpt = torch.load(str(PYTORCH_MODEL), map_location="cpu")
    pt_model.load_state_dict(ckpt.get("model_state_dict", ckpt))
    pt_model.eval()

    # Load ONNX
    session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])

    # Test sentences
    test_sentences = [
        "I will think about this problem tomorrow.",
        "Yesterday I bought some bread at the store.",
        "They are discussing the philosophy of science.",
        "The system requires optimization for better performance.",
        "I notice my thoughts are racing right now.",
    ][:num_samples]

    tokenizer = DebertaV2Tokenizer.from_pretrained("microsoft/mdeberta-v3-base")

    max_diff = 0.0
    for sentence in test_sentences:
        inputs = tokenizer(
            sentence,
            return_tensors="pt",
            truncation=True,
            max_length=256,
            padding="max_length",
        )

        # PyTorch — DeBERTa doesn't use token_type_ids
        pt_inputs = {k: v for k, v in inputs.items() if k != "token_type_ids"}
        with torch.no_grad():
            pt_out = pt_model(**pt_inputs)

        pt_t = pt_out["logits_t"].numpy()
        pt_d = pt_out["logits_d"].numpy()
        pt_i = pt_out["logits_i"].numpy()

        # ONNX
        onnx_out = session.run(
            None,
            {
                "input_ids": inputs["input_ids"].numpy(),
                "attention_mask": inputs["attention_mask"].numpy(),
            },
        )
        onnx_t, onnx_d, onnx_i = onnx_out[0], onnx_out[1], onnx_out[2]

        # Compare
        diff_t = np.abs(pt_t - onnx_t).max()
        diff_d = np.abs(pt_d - onnx_d).max()
        diff_i = np.abs(pt_i - onnx_i).max()
        diff = max(diff_t, diff_d, diff_i)
        max_diff = max(max_diff, diff)

        pt_pred = (int(pt_t.argmax()), int(pt_d.argmax()), int(pt_i.argmax()))
        onnx_pred = (int(onnx_t.argmax()), int(onnx_d.argmax()), int(onnx_i.argmax()))

        match = "✓" if pt_pred == onnx_pred else "✗"
        logger.info(
            f"  {match} '{sentence[:50]}...' | PT:{pt_pred} ONNX:{onnx_pred} | max_diff={diff:.6f}"
        )

    logger.info(f"Maximum difference across all samples: {max_diff:.6f}")
    if max_diff > 1e-4:
        logger.warning("Difference is larger than expected (>1e-4)")
    else:
        logger.info("✓ ONNX export verified successfully!")


def main():
    parser = argparse.ArgumentParser(description="Export C4 classifier to ONNX")
    parser.add_argument("--quantize", action="store_true", help="Apply INT8 quantization")
    parser.add_argument("--verify", action="store_true", help="Verify ONNX against PyTorch")
    parser.add_argument("--opset", type=int, default=14, help="ONNX opset version")
    args = parser.parse_args()

    try:
        output_path = export_onnx(
            quantize=args.quantize,
            opset=args.opset,
        )

        if args.verify:
            verify_onnx(output_path)

        logger.info(f"✅ Done! Exported model: {output_path}")

    except Exception as e:
        logger.error(f"Export failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
