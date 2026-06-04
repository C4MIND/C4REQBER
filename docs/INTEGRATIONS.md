# Интегрируемые модули и пакеты C4REQBER

## Установленные (лёгкие, работают на Mac без GPU)

| Пакет | Вес | Для чего | Статус |
|--------|-----|----------|--------|
| `qiskit` + `cirq` | ~50MB | Квантовые симуляции (квантовые схемы, entanglement, алгоритмы Шора/Гровера). Qiskit от IBM — industry standard | ✅ Установлен (2.4.1) |
| `gymnasium` + `stable-baselines3` | ~80MB | Reinforcement Learning. OpenAI Gym + SB3: PPO, A2C, DQN агенты. Работают на CPU | ✅ Установлен |
| `PySpice` | ~15MB | Симуляция электронных схем (SPICE). Интеграция с Ngspice | ⏳ В плане |
| `filterpy` | ~5MB | Kalman-фильтры, сенсор-фьюжн, SLAM | ⏳ В плане |
| `pulp` | ~10MB | Линейное программирование, оптимизация | ⏳ В плане |
| `nashpy` | ~3MB | Game Theory (Nash equilibrium, чистые/смешанные стратегии) | ⚠ Python 3.14 несовместим |
| `dowhy` | ~15MB | Causal inference — backdoor adjustment, propensity scoring, IV | ✅ Установлен (0.8) |
| `econml` | ~40MB | Causal ML — CausalForest, DoubleML, metalearners | ✅ Установлен (0.16) |
| `gcastle` | ~5MB | Causal discovery — PC, FCI, NOTEARS, ANM | ✅ Установлен (1.0.4) |

## Roadmap (крутые пакеты для будущей интеграции)

### Ближайшее (v5.5)
| Пакет | Для чего | Почему круто |
|--------|----------|-------------|
| `fastmcp` (22K⭐) | Anthropic MCP-серверы и клиенты. Позволит C4REQBER подключаться к любым MCP-инструментам | Стандарт индустрии 2026 |
| `crewai` (51K⭐) | Multi-agent orchestration. C4REQBER-агенты в ролях с цепочками задач | Лидер рынка multi-agent |
| `mlx-lm` | Локальные LLM на Apple Silicon GPU (0$/MTok). DeepSeek, Qwen, Llama локально | Идеально для Mac |
| `pydantic-ai` | Уже используется, расширить интеграцию с MCP-тулами | Agent framework |

### Научные симуляции (v5.6)
| Пакет | Для чего |
|--------|----------|
| `fenics` / `dolfinx` | Метод конечных элементов (FEM) — механика, упругость, тепло |
| `openmm` | Молекулярная динамика белков (Folding@Home) |
| `deepchem` | Deep learning для drug discovery |
| `pymc` / `bambi` | Байесовская статистика (MCMC, BMA) |
| `arviz` | Байесовская визуализация |

### AI / ML (v5.7)
| Пакет | Для чего |
|--------|----------|
| `langgraph` | LLM-агенты с графом состояний |
| `instructor` | Structured LLM outputs (Pydantic) |
| `chromadb` / `lancedb` | Векторные БД для knowledge retrieval |
| `unsloth` | Тюнинг LLM локально (4-bit QLoRA) |
| `vllm` | Высокопроизводительный LLM inference |

### MCP-экосистема (v5.8)
| Пакет | Для чего |
|--------|----------|
| `mcp-server-git` | Git-операции через MCP |
| `mcp-server-brave-search` | Brave Search API через MCP |
| `mcp-server-postgres` | PostgreSQL через MCP |
| `mcp-server-filesystem` | Файловая система через MCP |
| `smithery` | MCP-маркетплейс (найти и подключить любые MCP-серверы) |

## Примечания по совместимости
- Python 3.14+: часть пакетов отстают (nashpy, votekit). Использовать `uv` или venv с Python 3.12 для полной совместимости
- Mac без GPU: все лёгкие пакеты работают. Qiskit без GPU — только small circuits. Gymnasium — CPU-only RL ок для обучения, медленный для инференса
- GPU (Apple Silicon M1+): `mlx-lm` — нативный. `torch` — MPS backend. `tensorflow` — не родной на Mac, лучше `mlx-lm`

## Как добавить пакет в систему
1. `pip install package --break-system-packages`
2. Создать `src/integrations/<пакет>_bridge.py`
3. Зарегистрировать в `src/integrations/__init__.py`
4. Добавить MCP-tool в `src/mcp_server/server.py` если нужен
5. Обновить `AGENTS.md` + данный документ
