# Системные требования и совместимость C4REQBER v5.4

## Поддерживаемые ОС

| ОС | C4 Engine | LLM Providers | Knowledge Sources | Simulations | MCP Server | TUI/CLI |
|----|-----------|---------------|-------------------|-------------|------------|---------|
| **macOS (Apple Silicon M1+)** | ✅ | ✅ 12 провайдеров (MLX GPU) | ✅ 24 источника | ✅ | ✅ | ✅ |
| **macOS (Intel)** | ✅ | ✅ 11 провайдеров (нет MLX) | ✅ 24 источника | ✅ CPU-only | ✅ | ✅ |
| **Linux (x86_64)** | ✅ | ✅ 11 провайдеров (нет MLX) | ✅ 24 источника | ✅ | ✅ | ✅ |
| **Linux (ARM64)** | ✅ | ✅ 12 провайдеров (+ MLX если M-серия) | ✅ 24 источника | ✅ | ✅ | ✅ |
| **Windows** | ⚠️ Не тестирован | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |

## Версии Python

| Версия | Статус | Примечание |
|--------|--------|-----------|
| **3.14** | ✅ Основная | Все ядро работает. TF/NashPy/Flower — в изолированных окружениях |
| **3.13** | ✅ | Полная совместимость |
| **3.12** | ✅ | Все пакеты доступны напрямую (включая TF) |
| **3.11** | ✅ | Минимальная для MLX Newton Physics |
| **3.10** | ⚠️ | Часть фич 3.11+ недоступна |
| **3.9** | ❌ | Не поддерживается |

## Изолированные окружения

Некоторые научные пакеты требуют Python ≤3.12. Они устанавливаются в изолированные окружения через `uv`. C4REQBER вызывает их через subprocess — для пользователя это прозрачно.

| Пакет | Окружение | Python | Причина изоляции |
|-------|----------|--------|-----------------|
| **tensorflow 2.21** | `~/.c4reqber/envs/tensorflow` | 3.12 | TF не поддерживает 3.14 |
| **nashpy** | `~/.c4reqber/envs/nashpy` | 3.12 | NashPy требует ≤3.12 |
| **flower (flwr)** | `~/.c4reqber/envs/flower` | 3.12 | Flower требует ≤3.12 |

### Установка изолированного пакета

```bash
# Автоматически через менеджер пакетов:
blast packages install --id nashpy

# Вручную:
uv venv --python 3.12 ~/.c4reqber/envs/nashpy
uv pip install nashpy --python ~/.c4reqber/envs/nashpy/bin/python
```

### Как это работает

```
C4REQBER (Python 3.14)
  │
  ├── import mlx_lm          # Нативно (3.14)
  ├── import chromadb        # Нативно (3.14)
  ├── import qiskit          # Нативно (3.14)
  │
  └── subprocess: ~/.c4reqber/envs/nashpy/bin/python game_theory.py
       └── import nashpy     # Изолированно (3.12)
```

Пользователь не видит разницы — `blast solve "game theory problem"` работает одинаково.

## LLM-провайдеры по платформам

| Провайдер | Mac ARM | Mac Intel | Linux | Требуется |
|-----------|---------|-----------|-------|----------|
| **MLX** | ✅ GPU, $0/MTok | ❌ | ❌ | Apple Silicon + mlx-lm |
| **Ollama** | ✅ | ✅ | ✅ | Локально |
| **LM Studio** | ✅ | ✅ | ✅ | Локально |
| **OpenRouter** | ✅ | ✅ | ✅ | API ключ |
| **DeepSeek** | ✅ | ✅ | ✅ | API ключ |
| **XAI / Grok** | ✅ | ✅ | ✅ | API ключ |
| **Mistral** | ✅ | ✅ | ✅ | API ключ |
| **Moonshot** | ✅ | ✅ | ✅ | API ключ |
| **Liquid AI** | ✅ | ✅ | ✅ | API ключ |
| **NVIDIA NIM** | ✅ | ✅ | ✅ | API ключ |
| **YandexGPT** | ✅ | ✅ | ✅ | API ключ + folder_id |

## Что протестировано

| Категория | Тестов | Статус |
|-----------|--------|--------|
| **C4 Engine** | 806 | ✅ Все зелёные |
| **Интеграции** | 20 | ✅ Все зелёные |
| **Pipeline** | 245 | ✅ Все зелёные |
| **Agent** | 180 | ✅ Все зелёные |
| **CLI** | 85 | ✅ Все зелёные |
| **TUI** | 42 | ✅ Все зелёные |
| **MCP Server** | 38 | ✅ Все зелёные |
| **LLM Providers** | 65 | ✅ Все зелёные |
| **Auth/Security** | 55 | ✅ Все зелёные |
| **Knowledge Sources** | 0 | ⚠️ Пропущены (требуют API-ключи) |
| **Pattern Simulations** | 0 | ⚠️ Пропущены (требуют OpenFOAM/LAMMPS/FEniCS/TF) |
| **Сетевые интеграции** | 0 | ⚠️ Пропущены (требуют внешние сервисы) |

## Запуск тестов

```bash
# Базовые тесты (всегда проходят):
make test

# Полные тесты (требуют внешние сервисы):
C4REQBER_FULL_TEST=1 OPENROUTER_API_KEY=sk-... make test

# Только C4 Engine:
python3 -m pytest tests/c4/ -q

# Только интеграции:
python3 -m pytest tests/integrations/ -q
```
