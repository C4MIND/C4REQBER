# 🎯 Специализированные Harness-системы: карта голубых океанов 2026–2028
## Качественный анализ доменов, где generic agent — это мёртвый подход

**Дата:** Май 2026 | **Аналитический фрейм:** Constraint-Driven Specialization

---

## 📌 Тезис

Generic harness (типа Claude Code или Hermes) решает 80% задач для 20% рынка. 
Оставшиеся 80% рынка — это **вертикали, где generic агент мгновенно терпит крах** из-за:
- **Regulatory constraints** ( compliance нельзя «добавить потом»)
- **Safety-critical requirements** (ошибка стоит жизней или миллионов)
- **Domain-specific ontologies** (медицинская терминология ≠ код)
- **Legacy integration complexity** (COBOL не говорит на JSON)
- **Real-time physical constraints** (робот не ждёт 30-секундного API-ответа)

Каждая такая вертикаль требует **harness-first, model-second** подхода. 
Модель меняется — harness домена остаётся. Это и есть moat.

---

## 🗺️ Карта доменов: 10 категорий специализации

| # | Категория | Размер рынка (2026) | Сложность входа | Готовность технологий | Окно для входа |
|---|-----------|---------------------|-----------------|----------------------|----------------|
| 1 | **Regulated Finance** | $400B+ | 🔴 Высокая | 🟡 Средняя | 2026–2027 |
| 2 | **Healthcare & Clinical** | $300B+ | 🔴 Высокая | 🟡 Средняя | 2026–2028 |
| 3 | **Legal & Compliance** | $200B+ | 🟡 Средняя | 🟢 Высокая | 2026–2027 |
| 4 | **Legacy Enterprise Integration** | $500B+ | 🟡 Средняя | 🟡 Средняя | 2026–2028 |
| 5 | **Physical World / Embodied** | $150B+ | 🔴 Высокая | 🔴 Низкая | 2027–2029 |
| 6 | **Privacy-First / Sovereign** | $100B+ | 🟢 Низкая | 🟢 Высокая | 2026–2027 |
| 7 | **Scientific Research / Lab** | $80B+ | 🟡 Средняя | 🟡 Средняя | 2026–2028 |
| 8 | **Cybersecurity (Red/Blue)** | $60B+ | 🟡 Средняя | 🟢 Высокая | 2026–2027 |
| 9 | **SMB / Non-Tech Vertical OS** | $200B+ | 🟢 Низкая | 🟢 Высокая | 2026–2027 |
| 10 | **Crisis & Critical Infrastructure** | $50B+ | 🔴 Высокая | 🔴 Низкая | 2027–2029 |

---

## 1. 🏦 Regulated Finance Harness

### Почему generic не работает
- **Explainability requirement:** регулятор (SEC, FINRA, ECB) требует объяснить ЛЮБОЕ решение. Generic агент — black box.
- **Audit trail:** каждое действие должно быть неизменно задокументировано (WORM — Write Once Read Many).
- **Latency constraints:** high-frequency trading требует <1ms. LLM inference — 100-1000ms.
- **Data residency:** клиентские данные не могут покидать юрисдикцию.

### Что должен делать специализированный harness

```
┌─────────────────────────────────────────────────────────────┐
│              FINANCE HARNESS ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────┤
│  COMPLIANCE LAYER                                           │
│  • Pre-trade risk checks (Reg T, MiFID II)                  │
│  • Post-trade audit trail (immutable, WORM)                 │
│  • Explainability engine (decision → natural language)      │
│  • Regulatory sandbox (test against rule engine)            │
├─────────────────────────────────────────────────────────────┤
│  GOVERNANCE LAYER                                           │
│  • 4-eyes principle (human approval для trades >$X)         │
│  • Risk-tiered execution (read → analyze → recommend → act) │
│  • Circuit breakers (market volatility → halt)              │
├─────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                 │
│  • On-premise / air-gapped deployment                       │
│  • Real-time market data feeds (Bloomberg, Refinitiv)       │
│  • Historical backtesting engine                            │
├─────────────────────────────────────────────────────────────┤
│  MODEL LAYER                                                │
│  • Small models for latency-critical (classifiers)          │
│  • Large models for research (slow path)                    │
│  • Deterministic rules engine + probabilistic LLM           │
└─────────────────────────────────────────────────────────────┘
```

### Уникальные компоненты harness
1. **Rule Engine Integration** — harness не просто вызывает LLM, а сначала проверяет через deterministic rule engine (Drools, custom).
2. **Explainability Tracing** — каждое решение LLM декомпозируется на chain-of-thought + mapping к regulatory requirements.
3. **WORM Audit Log** — append-only, cryptographically signed, tamper-evident.
4. **Market Data Context** — real-time feeds как first-class citizens в context system, не через generic web search.

### Кто платит
- Hedge funds (quant research, compliance automation)
- Banks (KYC/AML automation, regulatory reporting)
- Insurance (underwriting, claims analysis)
- Fintech startups (embedded compliance)

### Почему ещё никто не доминирует
- **Regulatory moat:** нужны сертификации (SOC 2 Type II, ISO 27001, специфичные для finance).
- **Data access:** интеграция с Bloomberg Terminal, Refinitiv — дорого и сложно.
- **Trust:** финансовые институты не доверяют «ещё одному стартапу».

### Тайминг
**2026–2027:** появятся первые vertical-specific harnesses для:
- KYC/AML automation (уже начинается)
- Regulatory report generation (MiFID II, SEC filings)
- Quant research assistants (backtesting + hypothesis generation)

**2028:** полноценные «agentic trading desks» с human-in-the-loop.

---

## 2. 🏥 Healthcare & Clinical Harness

### Почему generic не работает
- **Evidence-based requirement:** любое медицинское утверждение должно быть обосновано evidence (pubmed, clinical trials).
- **HIPAA/GDPR:** PHI (Protected Health Information) не может попасть в облачный LLM.
- **Hallucination = malpractice:** ошибочный диагноз — судебный иск.
- **Multi-modal:** медицинские данные — рентген, МРТ, геномика, ЭКГ. Generic harness не понимает DICOM.

### Что должен делать специализированный harness

```
┌─────────────────────────────────────────────────────────────┐
│            CLINICAL HARNESS ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────┤
│  EVIDENCE LAYER                                             │
│  • PubMed / Cochrane / ClinicalTrials.gov RAG               │
│  • Evidence grading (GRADE framework)                       │
│  • Conflict-of-interest detection                           │
│  • Citation tracing (primary → secondary sources)           │
├─────────────────────────────────────────────────────────────┤
│  SAFETY LAYER                                               │
│  • Drug interaction checker (FDA, EMA databases)            │
│  • Contraindication analysis                                │
│  • Human-in-the-loop для diagnosis/treatment                │
│  • Second-opinion subagent (всегда cross-check)             │
├─────────────────────────────────────────────────────────────┤
│  MULTI-MODAL LAYER                                          │
│  • DICOM viewer + LLM vision                                │
│  • Genomic data parser (VCF, BAM)                           │
│  • EKG / time-series analysis                               │
│  • FHIR (Fast Healthcare Interoperability Resources)        │
├─────────────────────────────────────────────────────────────┤
│  PRIVACY LAYER                                              │
│  • On-device / hospital-local deployment                    │
│  • Differential privacy для analytics                       │
│  • Audit trail для PHI access                               │
└─────────────────────────────────────────────────────────────┘
```

### Уникальные компоненты harness
1. **Evidence Grading Engine** — не просто RAG, а оценка качества evidence по GRADE (Grading of Recommendations Assessment, Development and Evaluation).
2. **DICOM + FHIR Context** — медицинские стандарты как first-class citizens.
3. **Drug Interaction Graph** — real-time проверка через FDA Orange Book, EMA.
4. **Second-Opinion Subagent** — любой diagnosis/treatment recommendation проходит через verifier-агента с другой моделью.

### Кто платит
- Больницы (clinical decision support)
- Фармацевтические компании (drug discovery, clinical trials)
- Страховые (prior authorization automation)
- Telemedicine platforms

### Почему ещё никто не доминирует
- **Regulatory hell:** FDA approval для AI-based medical devices — 12-24 месяца.
- **Data silos:** EHR системы (Epic, Cerner) закрыты и сложны в интеграции.
- **Liability:** кто отвечает за ошибку агента? Врач? Больница? Разработчик?

### Тайминг
**2026:** harnesses для administrative tasks (scheduling, billing, prior auth) — низкий риск.
**2027:** clinical decision support (non-diagnostic) — second opinion, literature review.
**2028:** diagnostic assistants с FDA clearance (radiology, pathology).

---

## 3. ⚖️ Legal & Compliance Harness

### Почему generic не работает
- **Attorney-client privilege:** разговоры с агентом могут быть privileged. Облако — риск.
- **Jurisdiction-specific:** законодательство различается по странам, штатам, отраслям.
- **Precedent-based reasoning:** legal reasoning — не просто RAG, а аналогия, distinguishing, overturning.
- **Contract complexity:** 100+ страничные контракты с cross-references, schedules, amendments.

### Что должен делать специализированный harness

```
┌─────────────────────────────────────────────────────────────┐
│              LEGAL HARNESS ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────┤
│  PRIVILEGE LAYER                                            │
│  • Air-gapped deployment (данные не покидают офис)          │
│  • Encryption at rest + in transit (AES-256, TLS 1.3)       │
│  • Access logging (кто, когда, что спрашивал)               │
│  • Data retention policies (auto-delete по сроку)           │
├─────────────────────────────────────────────────────────────┤
│  REASONING LAYER                                            │
│  • Precedent graph (case law as knowledge graph)            │
│  • Distinguishing engine (почему этот case не применим)     │
│  • Jurisdiction router (какой law применять)                │
│  • Risk scoring (вероятность проигрыша)                     │
├─────────────────────────────────────────────────────────────┤
│  DOCUMENT LAYER                                             │
│  • Contract parsing (1000+ pages, cross-references)         │
│  • Redline generation (сравнение версий)                    │
│  • Clause library (pre-approved language)                   │
│  • Playbook automation (если X → делай Y)                   │
├─────────────────────────────────────────────────────────────┤
│  COMPLIANCE LAYER                                           │
│  • GDPR / CCPA / HIPAA checklists                           │
│  • Regulatory change tracking (новые законы → alert)        │
│  • Audit trail для всех recommendations                     │
└─────────────────────────────────────────────────────────────┘
```

### Уникальные компоненты harness
1. **Precedent Knowledge Graph** — не просто RAG, а граф связей между cases (followed, distinguished, overruled).
2. **Contract DNA Parser** — разбор сложных контрактов с cross-references, schedules, defined terms.
3. **Jurisdiction-Aware Context** — автоматическое определение applicable law и routing к нужной базе.
4. **Privilege Firewall** — гарантия, что communication не попадёт в discovery.

### Кто платит
- BigLaw firms (due diligence, contract review)
- Corporate legal departments (compliance, contract management)
- RegTech startups (automated compliance)
- Government (regulatory drafting)

### Почему ещё никто не доминирует
- **Trust:** юристы консервативны, не доверяют AI.
- **Complexity:** legal reasoning требует deep domain expertise.
- **Ethics:** bar associations ещё не определились с rules для AI.

### Тайминг
**2026:** contract review, NDAs, standard agreements — low-risk automation.
**2027:** due diligence, regulatory research, compliance checklists.
**2028:** litigation support, precedent analysis, predictive case outcomes.

---

## 4. 🏭 Legacy Enterprise Integration Harness

### Почему generic не работает
- **COBOL, Fortran, RPG:** эти языки не в training data современных LLM.
- **Monolithic databases:** DB2, IMS, Adabas — нет стандартных драйверов.
- **No API:** legacy системы работают через screenscraping, file drops, message queues.
- **Business logic:** 40 лет накопленных rules, которые никто не документировал.

### Что должен делать специализированный harness

```
┌─────────────────────────────────────────────────────────────┐
│         LEGACY INTEGRATION HARNESS ARCHITECTURE             │
├─────────────────────────────────────────────────────────────┤
│  DISCOVERY LAYER                                            │
│  • Code archaeology (COBOL → pseudocode → documentation)    │
│  • Data lineage tracing (where does this field come from?)  │
│  • Business rule extraction (from code + docs + interviews) │
│  • Dependency mapping (what breaks if we change X?)         │
├─────────────────────────────────────────────────────────────┤
│  ADAPTER LAYER                                              │
│  • Screen scraping (3270, 5250 terminals)                   │
│  • File-based integration (CSV, fixed-width, EDI)           │
│  • Message queue adapters (MQSeries, Kafka bridge)          │
│  • API facade generation (REST over legacy)                 │
├─────────────────────────────────────────────────────────────┤
│  MIGRATION LAYER                                            │
│  • Incremental migration (strangler fig pattern)            │
│  • Data synchronization (dual-write, CDC)                   │
│  • Rollback harness (если миграция fail → revert)           │
│  • Testing parity (legacy output == new output)             │
├─────────────────────────────────────────────────────────────┤
│  SAFETY LAYER                                               │
│  • Read-only mode (сначала анализ, потом действия)          │
│  • Shadow mode (новый код работает параллельно, не влияет)  │
│  • Canary deployments (1% traffic → 100%)                   │
└─────────────────────────────────────────────────────────────┘
```

### Уникальные компоненты harness
1. **COBOL-to-Pseudocode Decompiler** — специализированный parser для legacy языков.
2. **Screen Scraping Agent** — работа с 3270/5250 терминалами как с API.
3. **Data Lineage Tracer** — ответ на вопрос «откуда взялось это поле?» через 5 систем и 3 decades.
4. **Shadow Execution Mode** — новый код работает параллельно со старым, результаты сравниваются.

### Кто платит
- Fortune 500 (modernization initiatives)
- System integrators (IBM, Accenture, TCS)
- Government (legacy systems в IRS, SSA, NHS)
- Banks (core banking modernization)

### Почему ещё никто не доминирует
- **Knowledge gap:** мало людей понимают И COBOL, И AI.
- **Risk:** legacy = mission-critical. Ошибка = downtime = миллионы.
- **Sales cycle:** enterprise sales — 12-18 месяцев.

### Тайминг
**2026:** code archaeology, documentation generation, impact analysis.
**2027:** automated refactoring, API facade generation, test generation.
**2028:** autonomous migration (agent сам переписывает и деплоит).

---

## 5. 🤖 Physical World / Embodied AI Harness

### Почему generic не работает
- **Real-time constraints:** робот не может ждать 2 секунды на API-ответ. Требуется <10ms.
- **Safety-critical:** ошибка = физический вред людям.
- **Sensor fusion:** камера + лидар + IMU + GPS — нужна multi-modal обработка в real-time.
- **Edge compute:** роботы работают там, где нет интернета.

### Что должен делать специализированный harness

```
┌─────────────────────────────────────────────────────────────┐
│          EMBODIED AI HARNESS ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────┤
│  SAFETY LAYER                                               │
│  • Hard real-time guarantees (deterministic latency)        │
│  • Safety envelope (запретные зоны, speed limits)           │
│  • Emergency stop (hardware-level, не через LLM)            │
│  • Human override (всегда возможен)                         │
├─────────────────────────────────────────────────────────────┤
│  PERCEPTION LAYER                                           │
│  • Sensor fusion (camera + lidar + radar → unified world)   │
│  • Object detection + tracking (YOLO, etc.)                 │
│  • SLAM (Simultaneous Localization and Mapping)             │
│  • Anomaly detection (неожиданное препятствие)              │
├─────────────────────────────────────────────────────────────┤
│  PLANNING LAYER                                             │
│  • Motion planning (RRT*, A*, MPC)                          │
│  • Task planning (LLM для high-level, classical для low)    │
│  • Fallback strategies (если plan A fail → plan B/C/D)      │
├─────────────────────────────────────────────────────────────┤
│  EXECUTION LAYER                                            │
│  • Real-time OS (ROS 2, QNX, VxWorks)                       │
│  • Motor control (PID, impedance control)                   │
│  • Edge inference (TensorRT, ONNX Runtime)                  │
└─────────────────────────────────────────────────────────────┘
```

### Уникальные компоненты harness
1. **Hybrid Planner** — LLM для high-level task decomposition, classical algorithms (MPC, RRT*) для low-level control.
2. **Safety Envelope** — hard constraints, которые LLM не может нарушить (физический барьер).
3. **Edge-First Architecture** — inference на борту, cloud только для обучения/логирования.
4. **Sim-to-Real Bridge** — harness для transfer learning из симуляции в реальный мир.

### Кто платит
- Автономные транспорт (Waymo, Tesla, trucking)
- Промышленная робототехника (Boston Dynamics, Fanuc)
- Дроны (доставка, agriculture, inspection)
- Smart manufacturing (cobots)

### Почему ещё никто не доминирует
- **Hardware dependency:** нужны роботы/дроны/автомобили для тестирования.
- **Safety certification:** ISO 26262 (automotive), DO-178C (avionics) — годы.
- **Sim-to-real gap:** то, что работает в симуляции, часто не работает в реальности.

### Тайминг
**2026:** warehouse robotics, indoor navigation (controlled environment).
**2027:** outdoor logistics (last-mile delivery, agriculture).
**2028:** autonomous vehicles L4-L5, humanoid robots.

---

## 6. 🔒 Privacy-First / Sovereign AI Harness

### Почему generic не работает
- **Data sovereignty:** GDPR, China PIPL, Russia data localization laws.
- **Enterprise paranoia:** компании не хотят отправлять данные в OpenAI/Anthropic.
- **Personal privacy:** пользователи не хотят, чтобы их переписки обучали модели.
- **Cost at scale:** облачные API дороги для high-volume use cases.

### Что должен делать специализированный harness

```
┌─────────────────────────────────────────────────────────────┐
│          PRIVACY-FIRST HARNESS ARCHITECTURE                 │
├─────────────────────────────────────────────────────────────┤
│  DEPLOYMENT LAYER                                           │
│  • On-device (phone, laptop, edge device)                   │
│  • Self-hosted (VPS, on-premise)                            │
│  • Federated (learning across devices, no central data)     │
├─────────────────────────────────────────────────────────────┤
│  MODEL LAYER                                                │
│  • Small models (<7B) для edge                              │
│  • Quantization (INT4, INT8) для скорости                   │
│  • Model swapping (local → cloud по запросу)                │
│  • Encrypted weights (защита IP модели)                     │
├─────────────────────────────────────────────────────────────┤
│  MEMORY LAYER                                               │
│  • Local vector DB (Chroma, LanceDB)                        │
│  • Encrypted persistent storage                             │
│  • Differential privacy для analytics                       │
│  • User-controlled data deletion                            │
├─────────────────────────────────────────────────────────────┤
│  GOVERNANCE LAYER                                           │
│  • Zero-knowledge proofs (verify without reveal)            │
│  • Homomorphic encryption (compute on encrypted data)       │
│  • Audit trail (что агент делал, без раскрытия данных)     │
└─────────────────────────────────────────────────────────────┘
```

### Уникальные компоненты harness
1. **Local-First Architecture** — всё работает на устройстве, cloud — опционально.
2. **Model Swapping** — простые задачи на локальной модели, сложные — на облачной (с explicit consent).
3. **Federated Memory** — learning across users без централизации данных.
4. **Zero-Knowledge Verification** — prove that computation was correct without revealing input.

### Кто платит
- Privacy-conscious consumers (Proton, Signal users)
- Enterprise (banks, healthcare, government)
- EU companies (GDPR compliance)
- Journalists, activists, dissidents

### Почему ещё никто не доминирует
- **Performance gap:** локальные модели слабее облачных.
- **Battery/heat:** edge inference жрёт батарею и греет устройство.
- **UX friction:** пользователи хотят «просто работает», а не выбирать модель.

### Тайминг
**2026:** personal assistants на Mac/PC (Hermes, Ollama-based).
**2027:** on-device mobile agents (iPhone/Android с local LLM).
**2028:** federated enterprise agents (learning across organization без data sharing).

---

## 7. 🔬 Scientific Research / Lab Automation Harness

### Почему generic не работает
- **Verifiable feedback loops:** научный метод требует reproducibility. Generic агент не гарантирует.
- **Multi-modal data:** spectroscopy, chromatography, microscopy, sequencing — каждый формат уникален.
- **Instrument control:** роботы для wet lab (pipetting, incubation) требуют real-time control.
- **Hypothesis generation:** не просто анализ данных, а generation of testable hypotheses.

### Что должен делать специализированный harness

```
┌─────────────────────────────────────────────────────────────┐
│         LAB AUTOMATION HARNESS ARCHITECTURE                 │
├─────────────────────────────────────────────────────────────┤
│  EXPERIMENT LAYER                                           │
│  • Protocol generation (из literature + constraints)        │
│  • Reproducibility tracking (exact versions, parameters)    │
│  • Negative result logging (что НЕ сработало)               │
│  • Hypothesis registry (что тестируем, почему)              │
├─────────────────────────────────────────────────────────────┤
│  INSTRUMENT LAYER                                           │
│  • Lab equipment APIs (Opentrons, Tecan, Hamilton)          │
│  • Sensor integration (pH, temperature, OD)                 │
│  • Real-time monitoring (alert на anomaly)                  │
│  • Calibration tracking (when was last calibration?)        │
├─────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                 │
│  • ELN (Electronic Lab Notebook) integration                │
│  • LIMS (Lab Information Management System)                 │
│  • Raw data preservation (immutable, versioned)             │
│  • Analysis pipeline (Jupyter → automated)                  │
├─────────────────────────────────────────────────────────────┤
│  KNOWLEDGE LAYER                                            │
│  • Literature RAG (PubMed, arXiv, patents)                  │
│  • Prior art search                                         │
│  • Collaboration graph (кто работал над чем)                │
│  • Funding opportunity matching                             │
└─────────────────────────────────────────────────────────────┘
```

### Уникальные компоненты harness
1. **Protocol Verifier** — generated protocol проверяется на safety, feasibility, reproducibility.
2. **Negative Result Database** — что НЕ сработало, чтобы не повторять ошибки.
3. **Instrument Orchestrator** — управление физическим оборудованием через standardized API.
4. **Reproducibility Engine** — exact environment capture (versions, parameters, random seeds).

### Кто платит
- Big Pharma (drug discovery)
- Biotech startups (synthetic biology)
- Materials science (battery research, catalysts)
- Academic labs (grant-funded)

### Почему ещё никто не доминирует
- **Fragmentation:** каждая лаборатория уникальна.
- **Hardware diversity:** сотни типов оборудования, нет стандартов.
- **Scientific skepticism:** учёные не доверяют «чёрным ящикам».

### Тайминг
**2026:** literature review, hypothesis generation, data analysis.
**2027:** computational experiment design (in silico).
**2028:** closed-loop wet lab automation (design → execute → analyze → repeat).

---

## 8. 🛡️ Cybersecurity Harness (Red/Blue Team)

### Почему generic не работает
- **Adversarial environment:** attacker адаптируется. Static rules не работают.
- **Speed:** attack window — минуты. Manual analysis — часы.
- **Noise:** SOC получает тысячи alerts/day. 99% — false positives.
- **Tool sprawl:** 50+ security tools, каждый со своим API и форматом.

### Что должен делать специализированный harness

```
┌─────────────────────────────────────────────────────────────┐
│         CYBERSECURITY HARNESS ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────┤
│  THREAT INTELLIGENCE LAYER                                  │
│  • IOC ingestion (STIX/TAXII feeds)                         │
│  • TTP mapping (MITRE ATT&CK framework)                     │
│  • Dark web monitoring (leaks, chatter)                     │
│  • Vulnerability prioritization (CVSS + exploitability)     │
├─────────────────────────────────────────────────────────────┤
│  DETECTION LAYER                                            │
│  • Alert triage (false positive filtering)                  │
│  • Correlation (разрозненные alerts → incident)             │
│  • Behavioral analysis (baseline → anomaly)                 │
│  • Threat hunting (proactive search)                        │
├─────────────────────────────────────────────────────────────┤
│  RESPONSE LAYER                                             │
│  • Automated containment (isolate host, block IP)           │
│  • Forensic collection (memory dump, logs)                  │
│  • Playbook execution (если X → делай Y)                    │
│  • Human escalation (когда автоматика не справляется)       │
├─────────────────────────────────────────────────────────────┤
│  RED TEAM LAYER                                             │
│  • Automated pentesting ( recon → exploit → report)         │
│  • Social engineering simulation                            │
│  • Lateral movement simulation                              │
│  • Report generation (executive + technical)                │
└─────────────────────────────────────────────────────────────┘
```

### Уникальные компоненты harness
1. **MITRE ATT&CK Mapping** — каждый alert автоматически маппится на TTP.
2. **Adversarial Simulation** — red team агент, который постоянно атакует систему.
3. **Alert Correlation Engine** — 1000 alerts → 3 incidents с confidence score.
4. **Automated Containment** — isolation, blocking, quarantine без human approval (для known threats).

### Кто платит
- Enterprise SOC teams
- MSSP (Managed Security Service Providers)
- Government (cyber defense)
- Bug bounty platforms

### Почему ещё никто не доминирует
- **False positives:** автоматика может заблокировать legitimate traffic.
- **Liability:** если агент ошибочно удалит данные — кто отвечает?
- **Tool fragmentation:** интеграция с 50+ security tools — ад.

### Тайминг
**2026:** alert triage, threat hunting, vulnerability prioritization.
**2027:** automated response (containment для known threats).
**2028:** autonomous red teaming, continuous security validation.

---

## 9. 🏪 SMB / Non-Tech Vertical OS

### Почему generic не работает
- **Non-tech users:** владелец кафе не знает, что такое MCP.
- **Vertical specificity:** ресторан ≠ салон красоты ≠ строительная фирма.
- **Integration:** POS, accounting, scheduling, CRM — всё в разных системах.
- **Cost sensitivity:** SMB не платит $500/месяц за enterprise software.

### Что должен делать специализированный harness

```
┌─────────────────────────────────────────────────────────────┐
│            SMB VERTICAL OS ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────┤
│  USER INTERFACE LAYER                                       │
│  • Natural language (нет кнопок, только разговор)           │
│  • Voice-first (для мастеров, поваров, водителей)           │
│  • Mobile-first (всё управление с телефона)                 │
├─────────────────────────────────────────────────────────────┤
│  INTEGRATION LAYER                                          │
│  • POS (Square, Toast, Clover)                              │
│  • Accounting (QuickBooks, Xero)                            │
│  • Scheduling (Calendly, Acuity)                            │
│  • CRM (HubSpot, Pipedrive)                                 │
│  • Payroll (Gusto, ADP)                                     │
├─────────────────────────────────────────────────────────────┤
│  AUTOMATION LAYER                                           │
│  • Inventory management (auto-order при low stock)          │
│  • Customer follow-up (birthday, abandoned cart)            │
│  • Staff scheduling (optimal shifts)                        │
│  • Marketing (social media posts, email campaigns)          │
├─────────────────────────────────────────────────────────────┤
│  INTELLIGENCE LAYER                                         │
│  • P&L analysis ("почему вчера было меньше продаж?")        │
│  • Competitor monitoring (reviews, pricing)                 │
│  • Demand forecasting (weather → foot traffic)              │
└─────────────────────────────────────────────────────────────┘
```

### Уникальные компоненты harness
1. **Zero-Config Onboarding** — подключение к существующим системам через OAuth, не через API keys.
2. **Voice-First Interface** — работает hands-free для busy owners.
3. **Vertical Playbooks** — предустановленные workflows для конкретной индустрии.
4. **Cost-Optimized Inference** — использует cheapest adequate model, aggressive caching.

### Кто платит
- Restaurant owners
- Salons, spas, clinics
- Small retail
- Trades (plumbers, electricians)
- Freelancers / solopreneurs

### Почему ещё никто не доминирует
- **CAC:** привлечение SMB дорогое (high churn, low LTV).
- **Integration hell:** каждая POS-система — свой API, свои quirks.
- **Support:** non-tech users требуют hand-holding.

### Тайминг
**2026:** restaurant OS, salon OS — vertical-specific agents.
**2027:** multi-vertical platform (один агент для любого SMB).
**2028:** autonomous business management (agent ведёт бизнес за владельца).

---

## 10. 🚨 Crisis & Critical Infrastructure Harness

### Почему generic не работает
- **No internet:** ЧС часто означает отсутствие связи.
- **Life-critical:** ошибка = жертвы.
- **Multi-agency coordination:** полиция, пожарные, скорая, армия — разные системы.
- **Time pressure:** решения за секунды, не минуты.

### Что должен делать специализированный harness

```
┌─────────────────────────────────────────────────────────────┐
│         CRISIS RESPONSE HARNESS ARCHITECTURE                │
├─────────────────────────────────────────────────────────────┤
│  CONNECTIVITY LAYER                                         │
│  • Mesh networking (device-to-device, без internet)         │
│  • Satellite fallback (Starlink, Iridium)                   │
│  • Offline mode (полная автономность)                       │
│  • Inter-agency protocol (shared situational awareness)     │
├─────────────────────────────────────────────────────────────┤
│  SITUATIONAL AWARENESS LAYER                                │
│  • Sensor fusion (drones, cameras, IoT, social media)       │
│  • Damage assessment (AI vision для разрушений)             │
│  • Resource tracking (где техника, сколько топлива)         │
│  • Casualty prediction (based on building type, time)       │
├─────────────────────────────────────────────────────────────┤
│  DECISION SUPPORT LAYER                                     │
│  • Evacuation routing (real-time, с учётом damage)         │
│  • Resource allocation (кто куда едет, зачем)               │
│  • Scenario simulation ("что если дамба прорвётся?")        │
│  • Chain-of-command routing (кто принимает решения)         │
├─────────────────────────────────────────────────────────────┤
│  RESILIENCE LAYER                                           │
│  • Graceful degradation (если часть системы down → работаем)│
│  • Data replication (между агентами, P2P)                   │
│  • Post-incident analysis (lessons learned, auto-report)    │
└─────────────────────────────────────────────────────────────┘
```

### Уникальные компоненты harness
1. **Mesh Networking Agent** — работает без центрального сервера, P2P между устройствами.
2. **Offline-First AI** — модели и данные на устройстве, cloud — опционально.
3. **Multi-Agency Orchestration** — единый протокол для полиции, пожарных, скорой.
4. **Scenario Engine** — «what-if» simulation для принятия решений.

### Кто платит
- Government (FEMA, МЧС)
- Military (C4ISR systems)
- Utilities (grid management, water treatment)
- NGOs (disaster response)

### Почему ещё никто не доминирует
- **Procurement:** government sales — 2-3 года.
- **Reliability:** 99.99% uptime — минимум, а не цель.
- **Interoperability:** агентства не хотят делиться данными.

### Тайминг
**2026:** simulation and training (digital twins for crisis scenarios).
**2027:** drone-assisted assessment, resource optimization.
**2028:** autonomous crisis response coordination.

---

## 🔮 Скрытые специализации (неочевидные, но масштабные)

### A. **Religious / Spiritual Guidance Harness**
- **Проблема:** 84% мира верит в религию. Generic агент даёт secular ответы, которые могут оскорбить.
- **Специализация:** harness с sacred texts RAG, theological reasoning, denominational-specific doctrine.
- **Рынок:** $100B+ (religious education, counseling, content).
- **Статус:** практически пусто.

### B. **Agricultural Agent Harness**
- **Проблема:** фермеры не программисты. Precision agriculture требует интеграции дронов, датчиков, погоды, рынков.
- **Специализация:** harness для «digital farming» — от посева до продажи.
- **Рынок:** $400B+ (agtech).
- **Статус:** фрагментированные решения, нет unified harness.

### C. **Construction / BIM Harness**
- **Проблема:** строительные проекты — сотни подрядчиков, изменения, задержки.
- **Специализация:** harness для управления стройкой: BIM integration, schedule optimization, safety compliance.
- **Рынок:** $200B+ (construction management software).
- **Статус:** Autodesk пытается, но нет agentic layer.

### D. **Sports Analytics / Coaching Harness**
- **Проблема:** тренеры анализируют видео вручную. Generic агент не понимает тактику.
- **Специализация:** harness для tactical analysis, player development, opponent scouting.
- **Рынок:** $50B+ (sports tech).
- **Статус:** почти пусто.

### E. **Music / Audio Production Harness**
- **Проблема:** музыканты работают с DAW (Logic, Ableton). Generic агент не понимает music theory + production.
- **Специализация:** harness для composition, mixing, mastering, sample management.
- **Рынок:** $30B+ (music production software).
- **Статус:** AI tools есть, но нет unified harness.

---

## 📊 Матрица: Куда входить one-person бизнесу?

| Домен | Стартовый капитал | Время до MVP | Время до revenue | Технический порог | Потенциал для соло |
|-------|-------------------|--------------|------------------|-------------------|-------------------|
| **Legal (contract review)** | $0 | 2-4 недели | 1-2 месяца | 🟢 Низкий | ⭐⭐⭐⭐⭐ |
| **SMB Vertical OS** | $0 | 4-8 недель | 2-3 месяца | 🟢 Низкий | ⭐⭐⭐⭐⭐ |
| **Privacy-First Personal Agent** | $0 | 2-4 недели | 1-2 месяца | 🟢 Низкий | ⭐⭐⭐⭐⭐ |
| **Cybersecurity (alert triage)** | $0 | 4-6 недель | 2-4 месяца | 🟡 Средний | ⭐⭐⭐⭐ |
| **Legacy Code Archaeology** | $0 | 4-8 недель | 3-6 месяцев | 🟡 Средний | ⭐⭐⭐⭐ |
| **Scientific Literature Review** | $0 | 2-4 недели | 1-3 месяца | 🟢 Низкий | ⭐⭐⭐⭐ |
| **Regulated Finance** | $10K+ | 3-6 месяцев | 6-12 месяцев | 🔴 Высокий | ⭐⭐ |
| **Healthcare Clinical** | $50K+ | 6-12 месяцев | 12-24 месяца | 🔴 Высокий | ⭐ |
| **Physical World / Robotics** | $50K+ | 6-12 месяцев | 12-24 месяца | 🔴 Высокий | ⭐ |
| **Crisis Response** | $100K+ | 12+ месяцев | 24+ месяцев | 🔴 Высокий | ⭐ |

---

## 🎯 Итоговые инсайты

### 1. Специализация — это не «фича», а архитектурная необходимость
Generic harness работает там, где ошибка стоит $0.01. В regulated/safety-critical доменах ошибка стоит $1M+ или жизнь. Там нужен **domain-constrained harness**, который физически не может совершить определённые ошибки.

### 2. Самые жирные возможности — на пересечении
- **Legal + Privacy** = attorney-client privilege harness
- **Healthcare + Edge** = on-device clinical assistant
- **Finance + Legacy** = mainframe modernization для banks
- **SMB + Voice** = voice-first business OS для trades

### 3. Технологический стек 2026-2028 для специализированных harness
- **Base:** Hermes / Kilo CLI / OpenClaw (open-source core)
- **Memory:** SQLite FTS5 + vector (local), PostgreSQL + pgvector (cloud)
- **MCP:** специализированные серверы под домен
- **Models:** hybrid (Mamba-Transformer-MoE) для efficiency
- **Deployment:** Docker + VPS (self-hosted) для privacy
- **Observability:** Langfuse + custom evals

### 4. Главный moat — не код, а domain knowledge
Любой может скопировать код. Но **ontology домена** (как думает юрист, как работает больница, как устроен COBOL) — это moat, который невозможно скопировать за неделю.

### 5. Тайминг — сейчас
2026 — это **окно перед тем, как big tech зайдёт в вертикали**. К 2028 Microsoft, Google, Amazon будут у всех. Сейчас — момент для solopreneur с domain expertise.

---

> **«Не строй ещё одного generic агента. Строй harness, который решает одну конкретную боль так хорошо, что клиент готов платить за него в 10 раз больше, чем за generic tool.»**

---

*Анализ составлен на основе: трендов 2026 в agentic AI, regulatory landscape, enterprise pain points, hardware constraints, и логических выводов из архитектуры harness-систем.*
