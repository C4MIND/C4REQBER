# TURBO-CDI → FUNCGRADE v7: План Функционального Апгрейда

> **Миссия:** Превратить TURBO-CDI из когнитивного problem-solving движка в **полную экосистему автономного научного открытия** — платформу, покрывающую ВСЕ мыслимые и немыслимые потребности учёного, исследователя, инженера и problem-solver'а.
> **Бенчмарк функциональной полноты:** worldmonitor (для мониторинга) — всё мыслимое и немыслимое
> **Дата:** 2026-04-25
> **Статус:** Мета-анализ завершён, план сформирован

---

## Executive Summary

Проведён многомерный системный анализ функциональной полноты TURBO-CDI в сравнении с:
- Мировыми AI-for-Science платформами (Elicit, Scite, Semantic Scholar, Benchling, MLflow, W&B, JupyterLab)
- Концепциями автономного научного открытия (Robot Scientist Adam/Eve, AlphaFold, GNoME, FunSearch)
- Методологическими фреймворками (10 категорий, 50+ методологий)

**Главный вывод:** TURBO-CDI обладает **уникальным ядром** (C4 cognitive engine, TRIZ, multimodel pipeline) — аналогов нет. Но функционально покрывает лишь **~30%** того, что нужно современному учёному для полного цикла научного problem-solving. Оставшиеся 70% — это 8 новых когнитивных слоёв, которые превратят TURBO-CDI в платформу-категорию, подобно тому как worldmonitor стал категорией в мониторинге.

---

## 1. Мета-Анализ Функционального Ландшафта

### 1.1 Что значит «полный scientific problem-solving»?

Полный цикл научного problem-solving включает 7 фаз:

```
┌─────────────────────────────────────────────────────────────────────┐
│                   ПОЛНЫЙ ЦИКЛ НАУЧНОГО PROBLEM-SOLVING              │
│                                                                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │
│  │ 1.FRAME  │──▶│ 2.SEARCH │──▶│ 3.SYNTH  │──▶│ 4.MODEL  │        │
│  │ Problem  │   │Knowledge │   │Hypothesis│   │ &        │        │
│  │ Framing  │   │Discovery │   │Generation│   │Simulate  │        │
│  └──────────┘   └──────────┘   └──────────┘   └────┬─────┘        │
│                                                     │              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐        │              │
│  │ 7.SHARE  │◀──│ 6.VALID  │◀──│ 5.TEST   │◀───────┘              │
│  │Publish & │   │Validate &│   │Experiment│                         │
│  │Transfer  │   │Verify    │   │Design    │                         │
│  └──────────┘   └──────────┘   └──────────┘                        │
│                                                                     │
│  + META-LAYER: Collaboration, Reproducibility, Ethics, Learning    │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Текущее покрытие TURBO-CDI по фазам

| Фаза | Покрытие | Сильные стороны | Пробелы |
|------|----------|-----------------|---------|
| **1. FRAME** | 🟡 40% | IMPACT, C4 fingerprinting, TRIZ contradiction | Нет AHP, QFD, SODA, Rich Pictures, CATWOE |
| **2. SEARCH** | 🟡 35% | Prior art (arXiv, PubMed, USPTO), KG (88 узлов) | Нет SLR, meta-analysis, citation sentiment, contradiction mining |
| **3. SYNTH** | 🟢 65% | LLM multi-provider, MP rotation, 20 plugins | Нет abduction engine, Strong Inference, conceptual blending |
| **4. MODEL** | 🟡 40% | 95+ simulation patterns, TRIZ trends, S-curve | Нет System Dynamics, custom model builder, UQ framework |
| **5. TEST** | 🔴 5% | A/B testing (базовый) | **Полностью отсутствует**: DOE, sample size, power analysis |
| **6. VALID** | 🟡 30% | TOTE, consensus meter, empirical layer | Нет falsification engine, Lakatos/Kuhn frameworks |
| **7. SHARE** | 🟡 25% | Markdown/HTML export | Нет paper writing, journal matching, reproducibility pack |
| **META** | 🔴 10% | Auth, caching, WASM sandbox | Нет collaboration, provenance, ethics, ELN integration |

**Среднее покрытие: ~30%**

### 1.3 Что есть в индустрии, но нет в TURBO-CDI

Исследование показало, что рынок **фрагментирован**: есть инструменты для поиска литературы (Elicit, Scite, Semantic Scholar), для ML-экспериментов (W&B, MLflow), для лабораторных записей (Benchling). Но **никто не объединил их в единый closed-loop scientific discovery**.

**Уникальные ниши (никем не занятые):**
- 🔴 **Kuhnian paradigm shift detection** — не существует нигде
- 🔴 **Cross-domain contradiction/anomaly mining** — не существует
- 🔴 **Temporal knowledge graph научных утверждений** — не существует
- 🔴 **Automated reproducibility verification из литературы** — не существует
- 🔴 **«Zombie theory» detection** (опровергнутые, но цитируемые) — не существует
- 🟠 **Closed-loop: hypothesis → model → experiment → result** — фрагментарно (Benchling — только biotech)

---

## 2. Архитектура Функционального Апгрейда: 8 Новых Когнитивных Слоёв

### 2.1 Обзорная Архитектура Полной Системы

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     TURBO-CDI v7 — ПОЛНАЯ АРХИТЕКТУРА                        │
│                                                                              │
│  СУЩЕСТВУЮЩИЕ СЛОИ:                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ C4 Cog.  │ │ LLM Layer│ │ Plugin   │ │ Pattern  │ │ TRIZ     │          │
│  │ Engine   │ │ (7 prov.)│ │ System   │ │ Sim. (95)│ │ System   │          │
│  │ (Z₃³)    │ │          │ │ (20+)    │ │          │ │ (39×39)  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│                                                                              │
│  НОВЫЕ СЛОИ (FUNCGRADE v7):                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ L1. CAUSAL   │ │ L2. BAYESIAN │ │ L3. SYSTEM   │ │ L4. DECISION │        │
│  │ ENGINE       │ │ ENGINE       │ │ DYNAMICS     │ │ ENGINE       │        │
│  │ do-calculus  │ │ MCMC, BMA    │ │ Stock&Flow   │ │ AHP/TOPSIS/  │        │
│  │ SCM, DAG     │ │ Conj.Priors  │ │ CLD, SD DSL  │ │ GameTheory   │        │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ L5. DISCOV.  │ │ L6. LITERAT. │ │ L7. EXPERIM. │ │ L8. META     │        │
│  │ METHODOLOGY  │ │ INTELLIGENCE │ │ DESIGN &     │ │ LAYER        │        │
│  │ Abduction    │ │ Paradigm     │ │ VALIDATION   │ │ Collab       │        │
│  │ Strong Inf.  │ │ Detection    │ │ DOE + Reprod │ │ Reproduc.    │        │
│  │ Cncpt.Blend  │ │ Contradict.  │ │ Falsification│ │ Ethics       │        │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘        │
│                                                                              │
│  ИНТЕГРАЦИОННАЯ ШИНА: Knowledge Graph + Protocol Buffers + Pipeline           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Детализация Каждого Слоя

---

## СЛОЙ L1: CAUSAL ENGINE (Причинный Движок)

**Приоритет: 🔴 CRITICAL**
**Оценка: ~6,000 LOC**

### Концепция
Переход от корреляционного мышления к каузальному — ключевой скачок для научного problem-solving. Реализует Pearl's Causal Hierarchy (association → intervention → counterfactuals).

### Компоненты

| Компонент | Описание | LOC |
|-----------|----------|-----|
| **SCM Engine** | Structural Causal Models: nodes = variables, edges = causal mechanisms. DSL для определения SCM | 1,500 |
| **Do-Calculus** | Правила do-исчисления (3 правила). Автоматическое применение для identifiability causal effects | 1,000 |
| **Causal Effect Estimation** | Back-door, front-door критерии. Adjustment formula. Instrumental variables. Mediation analysis | 1,500 |
| **Counterfactual Engine** | 3-step counterfactual computation: abduction → action → prediction. Что-если анализ результатов экспериментов | 1,000 |
| **Causal Discovery** | PC, FCI, GES, LiNGAM, NOTEARS алгоритмы. Извлечение каузальных графов из наблюдательных данных | 1,000 |

### Интеграция с существующим
- **Knowledge Graph**: Каузальные DAG — подграфы KG
- **Simulation Patterns**: CFD/FEM/SEIR результаты как observational data для causal discovery
- **C4 Engine**: Causal states как расширение C4 cognitive состояний
- **TRIZ**: Contradiction matrix как causal conflict detection

### API (Proto)
```protobuf
service CausalService {
  rpc BuildSCM(BuildSCMRequest) returns (SCMResponse);
  rpc DoCalculus(DoRequest) returns (CausalEffectResponse);
  rpc EstimateEffect(EffectRequest) returns (CausalEffectResponse);
  rpc Counterfactual(CounterfactualRequest) returns (CounterfactualResponse);
  rpc DiscoverCausalGraph(DiscoveryRequest) returns (GraphResponse);
}
```

---

## СЛОЙ L2: BAYESIAN ENGINE (Байесовский Движок)

**Приоритет: 🔴 CRITICAL**
**Оценка: ~7,000 LOC** (включая DST и Fuzzy)

### Концепция
Системная работа с неопределённостью — от байесовского обновления убеждений до комбинирования свидетельств из множественных источников.

### Компоненты

| Компонент | Описание | LOC |
|-----------|----------|-----|
| **Bayesian Core** | Conjugate priors (Normal, Beta, Gamma, Dirichlet). Posterior computation. Bayesian updating pipeline | 1,500 |
| **MCMC Sampler** | Metropolis-Hastings, Gibbs sampling, Hamiltonian MC (NUTS). Параллельные цепочки | 2,000 |
| **Bayesian Model Averaging** | BMA над альтернативными моделями. Model evidence (marginal likelihood). Bayes factors | 1,000 |
| **Bayesian Optimization** | Gaussian Process surrogate. Acquisition functions (EI, UCB, Thompson sampling). Multi-objective | 1,500 |
| **Dempster-Shafer Engine** | Frame of discernment, basic belief assignment, belief/plausibility functions. Dempster's rule of combination | 1,500 |
| **Fuzzy Logic Engine** | Fuzzy sets, membership functions, fuzzy inference (Mamdani/Sugeno). Fuzzy Cognitive Maps (FCM) | 1,500 |

### Интеграция
- **Causal Engine**: Bayesian priors для каузальных параметров
- **LLM Layer**: Bayesian aggregation LLM outputs (модель уверенности)
- **Simulation Patterns**: Uncertainty quantification через Bayesian posteriors
- **Experiment Design**: Bayesian optimal experimental design

---

## СЛОЙ L3: SYSTEM DYNAMICS ENGINE (Системная Динамика)

**Приоритет: 🔴 CRITICAL**
**Оценка: ~5,000 LOC**

### Концепция
Моделирование систем с обратными связями, stocks & flows, и emergent behaviour — критически важно для понимания сложных научно-инженерных систем.

### Компоненты

| Компонент | Описание | LOC |
|-----------|----------|-----|
| **Stock-Flow Engine** | DSL для stocks, flows, auxiliaries. Компиляция в ODE систему. Интегратор (RK4, adaptive) | 1,500 |
| **Causal Loop Diagram** | CLD визуализация, автоматическое построение из KG. Идентификация reinforcing/balancing loops | 1,000 |
| **System Archetypes** | Библиотека предобученных архетипов (Senge: limits to growth, shifting the burden, tragedy of the commons, etc.) | 500 |
| **SD Model Fitting** | Калибровка SD моделей по данным. MCMC parameter estimation. Sensitivity analysis (Sobol, Morris) | 1,000 |
| **Scenario Explorer** | Multi-run simulation, параметрические развёртки, policy analysis | 1,000 |

### Интеграция
- **Simulation Patterns**: DSGE — частный случай SD. CFG/FEM/SEIR как stock-flow системы
- **Knowledge Graph**: Stocks → nodes, Flows → edges
- **Bayesian Engine**: Параметрическая неопределённость через Bayesian posteriors

---

## СЛОЙ L4: DECISION ENGINE (Движок Принятия Решений)

**Приоритет: 🟠 HIGH**
**Оценка: ~13,000 LOC** (включая все MCDA методы)

### Концепция
Формальные методы многокритериального анализа и теории игр для structured decision-making.

### Компоненты

| Компонент | Важность | Описание | LOC |
|-----------|----------|----------|-----|
| **AHP Plugin** | 🔴 Critical | Иерархии, попарные сравнения, собственные векторы, consistency ratio. Интеграция с KG | 1,500 |
| **TOPSIS Plugin** | 🟠 High | Distance to ideal/anti-ideal. Ideal для инженерных trade-off | 800 |
| **Game Theory Plugin** | 🟠 High | Nash equilibrium (pure/mixed), Shapley value, extensive-form игры | 3,500 |
| **PROMETHEE Plugin** | 🟡 Medium | Outranking с порогами безразличия/предпочтения. GAIA визуализация | 2,500 |
| **Robust Decision Making** | 🟠 High | XLRM framework, exploratory modelling, scenario discovery (PRIM) | 4,500 |

### Интеграция
- Все плагины — надстройки над Knowledge Graph + Bayesian Engine
- Game Theory использует Simulation Patterns как payoff functions
- RDM использует System Dynamics для exploratory modelling

---

## СЛОЙ L5: SCIENTIFIC DISCOVERY METHODOLOGY (Методология Научного Открытия)

**Приоритет: 🔴 CRITICAL**
**Оценка: ~15,500 LOC**

### Концепция
Формализация самого процесса научного открытия — от генерации гипотез до строгого тестирования. Это мета-уровень, превращающий TURBO-CDI из инструмента в **автономного научного агента**.

### Компоненты

| Компонент | Важность | Описание | LOC |
|-----------|----------|----------|-----|
| **Abduction Engine** | 🔴 Critical | Inference to the Best Explanation (Peirce). IBE scoring. Retroduction | 3,000 |
| **Strong Inference Engine** | 🔴 Critical | Platt's method: multiple hypotheses → crucial experiment → Bayesian update → recycle. Анти-confirmation bias | 3,000 |
| **Falsification Engine** | 🔴 Critical | Popper: проверка фальсифицируемости, severity scoring, modus tollens. Отличение науки от не-науки | 2,000 |
| **Conceptual Blending** | 🟠 High | Fauconnier & Turner: generic + input spaces → blended space с emergent structure. Генерация гипотез через блендинг далёких доменов | 4,000 |
| **Lakatos Framework** | 🟠 High | Research programmes: hard core + protective belt. Прогрессивный vs дегенеративный сдвиг | 2,000 |
| **Kuhn Framework** | 🟠 High | Парадигмы, аномалии, кризис, научная революция. Детекция сдвига парадигм | 2,000 |

### Интеграция
- **C4 Engine**: C4 states → states of scientific discovery process
- **Knowledge Graph**: Гипотезы, теории, парадигмы как evolving KG
- **Causal Engine**: Causal hypotheses testing
- **Bayesian Engine**: Bayesian updating гипотез

---

## СЛОЙ L6: LITERATURE INTELLIGENCE (Литературный Интеллект)

**Приоритет: 🔴 CRITICAL**
**Оценка: ~8,000 LOC**

### Концепция
Переход от простого поиска литературы к **глубокому анализу** научного корпуса: обнаружение противоречий, сдвига консенсуса, зарождающихся фронтов и «зомби-теорий».

### Компоненты

| Компонент | Описание | LOC |
|-----------|----------|-----|
| **Contradiction Miner** | Автоматическое обнаружение противоречащих утверждений между статьями. NLP-based claim extraction + contradiction detection. Citation-level sentiment (supporting/disputing) | 2,000 |
| **Paradigm Shift Detector** | Отслеживание temporal dynamics научных утверждений. Обнаружение anomalies, кризисов, сдвигов консенсуса. Kuhnian shift early warning system | 2,000 |
| **Emerging Front Detector** | Обнаружение rapidly growing research clusters. Co-citation burst detection. Interdisciplinary bridge detection | 1,500 |
| **Zombie Theory Detector** | Идентификация опровергнутых теорий, продолжающих цитироваться. Retraction-aware citation analysis | 1,000 |
| **Temporal Knowledge Graph** | Научные утверждения как evolving KG. Time-stamped nodes/edges. Запросы типа «как изменился консенсус о X за последние 10 лет» | 1,500 |

### Интеграция
- **Prior Art Search**: Входной поток статей
- **Knowledge Graph**: Хранение temporal claim graph
- **Causal Engine**: Каузальные связи между утверждениями
- **Abduction Engine**: Генерация объяснений обнаруженных противоречий

---

## СЛОЙ L7: EXPERIMENTAL DESIGN & VALIDATION

**Приоритет: 🟠 HIGH**
**Оценка: ~5,000 LOC**

### Концепция
Design of Experiments, power analysis и automated reproducibility testing — закрывает «мокрую» часть научного цикла.

### Компоненты

| Компонент | Описание | LOC |
|-----------|----------|-----|
| **DOE Engine** | Factorial designs (full, fractional). Response surface methodology. Optimal designs (D-optimal, I-optimal). Orthogonal arrays (Taguchi) | 2,000 |
| **Power Analysis** | Sample size calculation. Effect size estimation. Power curves. Type I/II error control | 1,000 |
| **Reproducibility Validator** | Автоматическая проверка воспроизводимости: extraction методов/данных из статьи → виртуальное воспроизведение → сравнение результатов | 2,000 |

### Интеграция
- **Simulation Patterns**: Simulation-based эксперименты → DOE выбор параметров
- **Bayesian Engine**: Bayesian optimal experimental design
- **Falsification Engine**: Severe testing

---

## СЛОЙ L8: META LAYER (Коллаборация, Воспроизводимость, Этика)

**Приоритет: 🟡 MEDIUM**
**Оценка: ~10,000 LOC**

### Компоненты

| Компонент | Описание | LOC |
|-----------|----------|-----|
| **Collaboration Engine** | Multi-user проекты, роли (PI/Researcher/Reviewer), real-time collaborative solving. Shared KG | 3,000 |
| **Provenance Tracker** | Full lineage: data → analysis → result. Git-like экспериментов. FAIR compliance | 2,000 |
| **Ethics & RRI** | Ethics impact assessment, bias detection, dual-use risk, stakeholder analysis | 1,500 |
| **Paper Composer** | Автоматическая генерация разделов статьи (Methods, Results, Discussion). Journal matching. Citation formatting | 2,500 |
| **ELN Bridge** | Интеграция с Electronic Lab Notebooks (Benchling, RSpace). IoT/sensor data ingestion | 1,000 |

---

## 3. Дорожная Карта Реализации

### Фаза A: Когнитивное Ядро (Недели 1–8)

```
Приоритет: Максимальный impact на научный problem-solving
```

| # | Компонент | Слой | Недели |
|---|-----------|------|--------|
| A1 | Causal Engine (do-calculus, SCM, counterfactuals) | L1 | 1–3 |
| A2 | Abduction Engine (Peirce IBE) | L5 | 2–4 |
| A3 | Strong Inference Engine (Platt) | L5 | 3–5 |
| A4 | Falsification Engine (Popper) | L5 | 4–6 |
| A5 | Bayesian Engine (MCMC, BMA) | L2 | 5–8 |
| A6 | System Dynamics Engine | L3 | 6–8 |

**Результат фазы A:** TURBO-CDI может самостоятельно: формулировать гипотезы (Abduction) → проверять их фальсифицируемость (Popper) → дизайнить решающие эксперименты (Strong Inference) → обновлять убеждения (Bayesian) → моделировать системы (System Dynamics).

### Фаза B: Литературный Интеллект (Недели 9–14)

| # | Компонент | Слой | Недели |
|---|-----------|------|--------|
| B1 | Contradiction Miner | L6 | 9–11 |
| B2 | Temporal Knowledge Graph | L6 | 10–12 |
| B3 | Paradigm Shift Detector | L6 | 11–13 |
| B4 | Conceptual Blending Engine | L5 | 12–14 |
| B5 | Emerging Front + Zombie Theory Detectors | L6 | 13–14 |

**Результат фазы B:** TURBO-CDI видит научный ландшафт: где противоречия, где зарождаются новые фронты, где парадигма в кризисе, какие теории — «зомби».

### Фаза C: Инструменты Принятия Решений (Недели 15–20)

| # | Компонент | Слой | Недели |
|---|-----------|------|--------|
| C1 | AHP Plugin | L4 | 15–16 |
| C2 | Game Theory Plugin | L4 | 16–18 |
| C3 | Robust Decision Making | L4 | 17–19 |
| C4 | TOPSIS + PROMETHEE | L4 | 18–19 |
| C5 | DST + Fuzzy Logic | L2 | 19–20 |

### Фаза D: Эксперименты и Валидация (Недели 21–26)

| # | Компонент | Слой | Недели |
|---|-----------|------|--------|
| D1 | DOE Engine | L7 | 21–23 |
| D2 | Reproducibility Validator | L7 | 22–24 |
| D3 | Lakatos + Kuhn Frameworks | L5 | 23–25 |
| D4 | Boundary Objects + Trading Zones | L5+ | 24–26 |

### Фаза E: Мета-слой и Экосистема (Недели 27–32)

| # | Компонент | Слой | Недели |
|---|-----------|------|--------|
| E1 | Collaboration Engine | L8 | 27–29 |
| E2 | Provenance Tracker | L8 | 28–30 |
| E3 | Paper Composer | L8 | 29–31 |
| E4 | Ethics & RRI | L8 | 30–31 |
| E5 | ELN Bridge | L8 | 31–32 |

---

## 4. Сводная Таблица Функционального Покрытия

```
┌──────────────────────────────┬────────────┬─────────────────────────┐
│ Функциональная область       │ ДО v7      │ ПОСЛЕ FUNCGRADE v7     │
│                              │ (покрытие) │ (покрытие)              │
├──────────────────────────────┼────────────┼─────────────────────────┤
│ Problem Framing              │ 🟡 40%     │ 🟢🟢🟢 95% (+AHP,QFD,SSM)│
│ Knowledge Discovery          │ 🟡 35%     │ 🟢🟢🟢 95% (+Contrad.,TKG)│
│ Hypothesis Generation        │ 🟢 65%     │ 🟢🟢🟢 100% (+Abduction) │
│ Modeling & Simulation        │ 🟡 40%     │ 🟢🟢🟢 95% (+SD,UQ)     │
│ Experiment Design            │ 🔴 5%      │ 🟢🟢 85% (+DOE,Power)   │
│ Validation & Verification    │ 🟡 30%     │ 🟢🟢🟢 95% (+Popper et al)│
│ Decision Making              │ 🟡 20%     │ 🟢🟢🟢 95% (+MCDA,Game)  │
│ Literature Intelligence      │ 🔴 15%     │ 🟢🟢🟢 100% (+L6 fully) │
│ Causality & Uncertainty      │ 🔴 10%     │ 🟢🟢🟢 95% (+L1,L2)     │
│ Collaboration & Sharing      │ 🔴 10%     │ 🟢🟢 80% (+Paper,Collab) │
│ Reproducibility              │ 🔴 5%      │ 🟢🟢 85% (+Provenance)   │
│ Ethics & RRI                 │ 🔴 0%      │ 🟢🟢 75% (+Ethics)       │
│ Paradigm Detection           │ 🔴 0%      │ 🟢🟢🟢 100% (уникально!) │
├──────────────────────────────┼────────────┼─────────────────────────┤
│ СРЕДНЕЕ                      │ ~23%       │ ~92%                     │
└──────────────────────────────┴────────────┴─────────────────────────┘
```

---

## 5. Уникальные Фичи — То, Чего Нет Ни У Кого

После реализации FUNCGRADE v7 TURBO-CDI станет единственной платформой, которая:

1. **Обнаруживает сдвиг научных парадигм** (Kuhnian shift detection) — не существует нигде
2. **Автоматически находит противоречия в научной литературе** (contradiction mining)
3. **Отслеживает «зомби-теории»** — опровергнутые, но продолжающие цитироваться
4. **Проверяет воспроизводимость** научных результатов по тексту статьи
5. **Генерирует гипотезы через концептуальный блендинг** далёких доменов
6. **Выполняет полный closed-loop scientific discovery**: frame → search → hypothesize → model → design experiment → validate → share
7. **Работает как автономный научный агент**, а не просто инструмент поиска

---

## 6. Метрики Успеха

- [ ] Causal Engine: do-calculus идентифицирует 90%+ каузальных эффектов на тестовых DAG
- [ ] Abduction Engine: IBE scoring совпадает с экспертными оценками в 85%+ случаев
- [ ] Contradiction Miner: F1-score > 0.85 на task detection противоречий
- [ ] Paradigm Shift Detector: обнаружение известных сдвигов с опережением на 2+ года (ретроспективно)
- [ ] AHP: consistency ratio detection с точностью RI-таблиц Саати
- [ ] System Dynamics: ODE simulation accuracy в пределах 1e-6 от эталонных решателей
- [ ] Все компоненты: покрытие тестами > 70%
- [ ] Все компоненты: proto-контракты (клиент + сервер + OpenAPI 3.1)

---

## 7. Оценка Ресурсов

| Параметр | Значение |
|----------|----------|
| **Суммарный объём нового кода** | ~69,500 LOC Python + ~8,000 LOC TypeScript |
| **Новые proto-контракты** | ~30 service definitions |
| **Новые тесты** | ~15,000 LOC |
| **Общая длительность** | 32 недели (8 месяцев) |
| **Команда** | 4–6 разработчиков |
| **Фаза A (Critical)** | 8 недель, 25,000 LOC |
| **Фаза B (Lit Intel)** | 6 недель, 8,000 LOC |
| **Фаза C (Decision)** | 6 недель, 13,000 LOC |
| **Фаза D (Validation)** | 6 недель, 9,000 LOC |
| **Фаза E (Meta)** | 6 недель, 10,000 LOC |

---

## 8. Связь с PROGRADE_PLAN_v7

PROGRADE_PLAN_v7 (инженерный апгрейд) и FUNCGRADE_PLAN_v7 (функциональный апгрейд) — это два комплементарных трека:

```
PROGRADE (инженерия)              FUNCGRADE (функциональность)
─────────────────────────         ────────────────────────────
• Тесты, mypy, модульность        • Causal Engine, Bayesian
• CI/CD, pre-push hooks           • Abduction, Strong Inference
• Proto-контракты                 • Paradigm Shift Detection
• Observability, Sentry           • Contradiction Mining
• Desktop app (Tauri)             • System Dynamics
• Multi-variant, i18n             • MCDA Decision Tools
• Документация, Community         • Experimental Design

ОБА ТРЕКА ВМЕСТЕ = TURBO-CDI v7
```

**Рекомендуемая стратегия:** PROGRADE (3 недели фундамента) → параллельно PROGRADE+Фаза A FUNCGRADE (8 недель) → продолжение FUNCGRADE (фазы B–E)

---

**Этот документ — живая дорожная карта. Каждый завершённый компонент обновляет статус и процент покрытия.**
