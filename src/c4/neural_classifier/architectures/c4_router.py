"""
C4 Router Model
===============

Модель для классификации текста в C4 координаты.

Архитектура:
- Base: предобученный encoder (BERT/RoBERTa/Phi)
- Head T: классификация Time (3 класса)
- Head D: классификация Scale (3 класса)
- Head I: классификация Agency (3 класса)

Особенности:
- Multi-task learning (3 головы)
- Возможность использовать как отдельно, так и совместно
- Поддержка разных base моделей
"""

import logging
from dataclasses import dataclass
from typing import Any


logger = logging.getLogger(__name__)

# Опциональный импорт PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. Install: pip install torch")


@dataclass
class C4RouterConfig:
    """Конфигурация C4Router модели"""
    # Base model
    base_model: str = "microsoft/deberta-v3-small"
    hidden_size: int = 768

    # Architecture
    head_hidden_size: int = 256
    dropout: float = 0.1
    num_classes_per_axis: int = 3

    # Training
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1

    # Loss weights for multi-task
    loss_weight_t: float = 1.0
    loss_weight_d: float = 1.0
    loss_weight_i: float = 1.0

    # Freezing
    freeze_base: bool = False
    freeze_base_layers: int = 0  # Freeze first N layers

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_model": self.base_model,
            "hidden_size": self.hidden_size,
            "head_hidden_size": self.head_hidden_size,
            "dropout": self.dropout,
        }


if TORCH_AVAILABLE:
    class C4ClassificationHead(nn.Module):
        """Голова классификации для одной оси"""

        def __init__(
            self,
            input_size: int,
            hidden_size: int,
            num_classes: int,
            dropout: float = 0.1,
        ):
            super().__init__()
            self.dense = nn.Linear(input_size, hidden_size)
            self.activation = nn.GELU()
            self.dropout = nn.Dropout(dropout)
            self.classifier = nn.Linear(hidden_size, num_classes)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """Forward."""
            x = self.dense(x)
            x = self.activation(x)
            x = self.dropout(x)
            x = self.classifier(x)
            return x


    class C4ClassifierModel(nn.Module):
        """
        Flat C4 Classifier — matches c4factory checkpoint architecture.

        Architecture:
        - backbone: DeBERTa-v3-base encoder
        - head_t/d/i: Linear(hidden_size, 3) — no hidden layers

        This is the architecture used by c4_classifier_best.pt (96.5% accuracy).
        """

        def __init__(self, base_model: str = "microsoft/mdeberta-v3-base", hidden_size: int = 768):
            super().__init__()
            from transformers import AutoModel
            self.backbone = AutoModel.from_pretrained(base_model)
            self.head_t = nn.Linear(hidden_size, 3)
            self.head_d = nn.Linear(hidden_size, 3)
            self.head_i = nn.Linear(hidden_size, 3)

        def forward(
            self,
            input_ids: torch.Tensor,
            attention_mask: torch.Tensor | None = None,
        ) -> dict[str, torch.Tensor]:
            """Forward."""
            outputs = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
            hidden = outputs.last_hidden_state[:, 0]  # CLS token
            return {
                "logits_t": self.head_t(hidden),
                "logits_d": self.head_d(hidden),
                "logits_i": self.head_i(hidden),
            }

        def predict(self, input_ids, attention_mask=None):
            """Predict."""
            self.eval()
            with torch.no_grad():
                out = self.forward(input_ids, attention_mask)
                return (
                    torch.argmax(out["logits_t"], dim=-1),
                    torch.argmax(out["logits_d"], dim=-1),
                    torch.argmax(out["logits_i"], dim=-1),
                )

        def get_c4_index(self, input_ids, attention_mask=None):
            """Get c4 index."""
            pred_t, pred_d, pred_i = self.predict(input_ids, attention_mask)
            return pred_t * 9 + pred_d * 3 + pred_i

        def get_probabilities(self, input_ids, attention_mask=None):
            """Get probabilities."""
            self.eval()
            with torch.no_grad():
                out = self.forward(input_ids, attention_mask)
                return {
                    "prob_t": F.softmax(out["logits_t"], dim=-1),
                    "prob_d": F.softmax(out["logits_d"], dim=-1),
                    "prob_i": F.softmax(out["logits_i"], dim=-1),
                }


    class C4RouterModel(nn.Module):
        """
        C4 Router - Multi-task классификатор для C4 координат.

        Три головы классификации:
        - head_t: Time (Past/Present/Future)
        - head_d: Scale (Concrete/Abstract/Meta)
        - head_i: Agency (Self/Other/System)

        Example:
            >>> config = C4RouterConfig()
            >>> model = C4RouterModel(config)
            >>> outputs = model(input_ids, attention_mask)
            >>> logits_t, logits_d, logits_i = outputs['logits_t'], outputs['logits_d'], outputs['logits_i']
        """

        def __init__(self, config: C4RouterConfig):
            super().__init__()
            self.config = config

            # Base encoder
            self.encoder = self._load_encoder(config.base_model)

            # Classification heads
            self.head_t = C4ClassificationHead(
                config.hidden_size,
                config.head_hidden_size,
                config.num_classes_per_axis,
                config.dropout,
            )
            self.head_d = C4ClassificationHead(
                config.hidden_size,
                config.head_hidden_size,
                config.num_classes_per_axis,
                config.dropout,
            )
            self.head_i = C4ClassificationHead(
                config.hidden_size,
                config.head_hidden_size,
                config.num_classes_per_axis,
                config.dropout,
            )

            # Pooler
            self.pooler = nn.Linear(config.hidden_size, config.hidden_size)
            self.pooler_activation = nn.Tanh()

            # Loss weights
            self.loss_weights = torch.tensor([
                config.loss_weight_t,
                config.loss_weight_d,
                config.loss_weight_i,
            ])

            # Apply freezing
            if config.freeze_base:
                self._freeze_encoder()
            elif config.freeze_base_layers > 0:
                self._freeze_encoder_layers(config.freeze_base_layers)

        def _load_encoder(self, model_name: str):
            """Загрузка base encoder"""
            try:
                from transformers import AutoModel
                return AutoModel.from_pretrained(model_name)
            except ImportError as e:
                raise ImportError("transformers required. Install: pip install transformers") from e

        def _freeze_encoder(self):
            """Заморозить весь encoder"""
            for param in self.encoder.parameters():
                param.requires_grad = False

        def _freeze_encoder_layers(self, num_layers: int):
            """Заморозить первые N слоёв encoder"""
            # Для BERT-like моделей
            if hasattr(self.encoder, 'embeddings'):
                for param in self.encoder.embeddings.parameters():
                    param.requires_grad = False

            if hasattr(self.encoder, 'encoder') and hasattr(self.encoder.encoder, 'layer'):
                for i, layer in enumerate(self.encoder.encoder.layer):
                    if i < num_layers:
                        for param in layer.parameters():
                            param.requires_grad = False

        def forward(
            self,
            input_ids: torch.Tensor,
            attention_mask: torch.Tensor | None = None,
            labels_t: torch.Tensor | None = None,
            labels_d: torch.Tensor | None = None,
            labels_i: torch.Tensor | None = None,
        ) -> dict[str, torch.Tensor]:
            """
            Forward pass.

            Args:
                input_ids: [batch_size, seq_len]
                attention_mask: [batch_size, seq_len]
                labels_t/d/i: [batch_size] - labels for each axis

            Returns:
                Dict with logits and optionally loss
            """
            # Encoder
            outputs = self.encoder(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

            # Pooling ([CLS] token)
            hidden_states = outputs.last_hidden_state
            pooled = self.pooler(hidden_states[:, 0])
            pooled = self.pooler_activation(pooled)

            # Classification heads
            logits_t = self.head_t(pooled)
            logits_d = self.head_d(pooled)
            logits_i = self.head_i(pooled)

            result = {
                "logits_t": logits_t,
                "logits_d": logits_d,
                "logits_i": logits_i,
                "pooled_output": pooled,
            }

            # Compute loss if labels provided
            if labels_t is not None and labels_d is not None and labels_i is not None:
                loss_fn = nn.CrossEntropyLoss()

                loss_t = loss_fn(logits_t, labels_t)
                loss_d = loss_fn(logits_d, labels_d)
                loss_i = loss_fn(logits_i, labels_i)

                # Weighted sum
                total_loss = (
                    self.config.loss_weight_t * loss_t +
                    self.config.loss_weight_d * loss_d +
                    self.config.loss_weight_i * loss_i
                )

                result["loss"] = total_loss
                result["loss_t"] = loss_t
                result["loss_d"] = loss_d
                result["loss_i"] = loss_i

            return result

        def predict(
            self,
            input_ids: torch.Tensor,
            attention_mask: torch.Tensor | None = None,
        ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            """
            Predict C4 coordinates.

            Returns:
                (pred_t, pred_d, pred_i) - predictions for each axis
            """
            self.eval()
            with torch.no_grad():
                outputs = self.forward(input_ids, attention_mask)

                pred_t = torch.argmax(outputs["logits_t"], dim=-1)
                pred_d = torch.argmax(outputs["logits_d"], dim=-1)
                pred_i = torch.argmax(outputs["logits_i"], dim=-1)

            return pred_t, pred_d, pred_i

        def get_c4_index(
            self,
            input_ids: torch.Tensor,
            attention_mask: torch.Tensor | None = None,
        ) -> torch.Tensor:
            """
            Get C4 state index (0-26).

            index = t * 9 + d * 3 + i
            """
            pred_t, pred_d, pred_i = self.predict(input_ids, attention_mask)
            return pred_t * 9 + pred_d * 3 + pred_i

        def get_probabilities(
            self,
            input_ids: torch.Tensor,
            attention_mask: torch.Tensor | None = None,
        ) -> dict[str, torch.Tensor]:
            """
            Get probability distributions for each axis.
            """
            self.eval()
            with torch.no_grad():
                outputs = self.forward(input_ids, attention_mask)

                prob_t = F.softmax(outputs["logits_t"], dim=-1)
                prob_d = F.softmax(outputs["logits_d"], dim=-1)
                prob_i = F.softmax(outputs["logits_i"], dim=-1)

            return {
                "prob_t": prob_t,
                "prob_d": prob_d,
                "prob_i": prob_i,
            }

        def save_pretrained(self, path: str):
            """Сохранить модель"""
            import json
            import os

            os.makedirs(path, exist_ok=True)

            # Save config
            with open(os.path.join(path, "config.json"), "w") as f:
                json.dump(self.config.to_dict(), f, indent=2)

            # Save weights
            torch.save(self.state_dict(), os.path.join(path, "pytorch_model.bin"))

        @classmethod
        def from_pretrained(cls, path: str, config: C4RouterConfig | None = None):
            """Загрузить модель"""
            import json
            import os

            # Load config
            if config is None:
                with open(os.path.join(path, "config.json")) as f:
                    config_dict = json.load(f)
                config = C4RouterConfig(**config_dict)

            # Create model
            model = cls(config)

            # Load weights
            state_dict = torch.load(
                os.path.join(path, "pytorch_model.bin"),
                map_location="cpu"
            )
            model.load_state_dict(state_dict)

            return model

else:
    # Stub когда PyTorch недоступен
    class C4RouterModel:  # type: ignore[no-redef]
        """C4RouterModel."""
        def __init__(self, config):
            raise ImportError("PyTorch required. Install: pip install torch transformers")

    class C4ClassificationHead:  # type: ignore[no-redef]
        """C4ClassificationHead."""
        pass


# Пресеты конфигураций
C4_ROUTER_CONFIGS = {
    # === English-only (fast, for testing) ===
    "tiny": C4RouterConfig(
        base_model="prajjwal1/bert-tiny",
        hidden_size=128,
        head_hidden_size=64,
    ),
    "small": C4RouterConfig(
        base_model="microsoft/deberta-v3-small",
        hidden_size=768,
        head_hidden_size=256,
    ),
    "base": C4RouterConfig(
        base_model="microsoft/deberta-v3-base",
        hidden_size=768,
        head_hidden_size=384,
    ),

    # === MULTILINGUAL (ru/en) - RECOMMENDED ===
    "xlm-small": C4RouterConfig(
        base_model="xlm-roberta-base",  # 100+ languages, 270M params
        hidden_size=768,
        head_hidden_size=256,
    ),
    "xlm-large": C4RouterConfig(
        base_model="xlm-roberta-large",  # 550M params, best quality
        hidden_size=1024,
        head_hidden_size=384,
    ),
    "mbert": C4RouterConfig(
        base_model="bert-base-multilingual-cased",  # 104 languages
        hidden_size=768,
        head_hidden_size=256,
    ),
    "rubert": C4RouterConfig(
        base_model="DeepPavlov/rubert-base-cased",  # Russian-optimized
        hidden_size=768,
        head_hidden_size=256,
    ),
    "rubert-tiny": C4RouterConfig(
        base_model="cointegrated/rubert-tiny2",  # 29M params, fast
        hidden_size=312,
        head_hidden_size=128,
    ),

    # === Large models (need GPU) ===
    "phi": C4RouterConfig(
        base_model="microsoft/phi-2",
        hidden_size=2560,
        head_hidden_size=512,
    ),
}

# Алиас для удобства
C4_ROUTER_CONFIGS["multilingual"] = C4_ROUTER_CONFIGS["xlm-small"]
C4_ROUTER_CONFIGS["bilingual"] = C4_ROUTER_CONFIGS["xlm-small"]


def create_c4_router(preset: str = "xlm-small") -> 'C4RouterModel':
    """
    Фабрика для создания C4Router модели.

    Args:
        preset: 'tiny', 'small', 'base' (English)
                'xlm-small', 'xlm-large', 'mbert' (Multilingual)
                'rubert', 'rubert-tiny' (Russian-optimized)
                'multilingual', 'bilingual' (aliases for xlm-small)
    """
    if preset not in C4_ROUTER_CONFIGS:
        raise ValueError(f"Unknown preset: {preset}. Available: {list(C4_ROUTER_CONFIGS.keys())}")

    config = C4_ROUTER_CONFIGS[preset]
    return C4RouterModel(config)
