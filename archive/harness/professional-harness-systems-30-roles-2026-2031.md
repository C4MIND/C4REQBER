# 🏭 Профессиональные Harness-системы: карта B2B-вертикалей 2026–2031
## 30+ специализированных агентских ОС для реальных рабочих ролей

**Тезис:** Consumer harness'ы решают «как прожить жизнь».  
**Professional harness'ы** решают «как выполнить работу, которую generic AI не понимает».  
Каждая профессия — это **ontology** (терминология, workflow, constraints, regulatory framework), которую LLM не знает из training data.

---

## 📊 Мета-карта: 8 индустриальных кластеров × 30+ ролей

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PROFESSIONAL HARNESS LANDSCAPE                       │
├─────────────────────────────────────────────────────────────────────────┤
│  🏗️ BUILT ENVIRONMENT          🚚 SUPPLY CHAIN & LOGISTICS             │
│  🏥 HEALTHCARE (Non-clinical)   ⚖️ LEGAL & REGULATORY                  │
│  🏦 FINANCIAL SERVICES          🎓 EDUCATION & RESEARCH                │
│  🏭 INDUSTRIAL & ENERGY         🎨 CREATIVE & MEDIA                    │
│  🌾 AGRICULTURE & FOOD          🛡️ PUBLIC SAFETY & DEFENSE             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## КЛАСТЕР 1: 🏗️ Built Environment (Строительная экосистема)

### 1.1 Construction Superintendent Harness
**Роль:** Управление стройплощадкой (100+ подрядчиков, сроки, безопасность, качество).

**Почему generic не работает:**
- **Submittal workflow:** материалы должны быть approved architect/engineer ДО установки. Generic агент не понимает эту последовательность.
- **RFI (Request for Information):** цикл вопрос-ответ между GC и design team может длиться недели. Нужен tracking + escalation.
- **Daily reports:** фото, weather, manpower, safety incidents — структурированный формат.
- **Schedule compression:** если дождь задержал concrete pour → cascade effect на 15 trades.

**Уникальная архитектура harness:**
```
┌─────────────────────────────────────────────────────────────┐
│  SUBMITTAL & RFI ORCHESTRATION                              │
│  • Submittal log (status: submitted → reviewed → approved → │
│    fabricated → delivered → installed)                      │
│  • RFI lifecycle (issued → assigned → responded → approved) │
│  • Ball-in-court tracking (кто сейчас блокирует?)           │
│  • Auto-escalation (если >5 дней без ответа)                │
├─────────────────────────────────────────────────────────────┤
│  DAILY REPORT AUTOMATION                                    │
│  • Photo organization (by location, date, trade)            │
│  • Weather integration (impact на schedule)                 │
│  • Manpower count (by trade, by subcontractor)              │
│  • Safety observation logging (near misses, violations)     │
├─────────────────────────────────────────────────────────────┤
│  SCHEDULE & COST CONTROL                                    │
│  • Critical path monitoring ( Primavera P6 / MS Project)    │
│  • Change order impact analysis ($ + schedule)              │
│  • Productivity tracking (planned vs actual units)          │
│  • Forecasting (will we finish by [date]?)                  │
├─────────────────────────────────────────────────────────────┤
│  SAFETY & QUALITY                                           │
│  • OSHA compliance checklist (daily, weekly, monthly)       │
│  • Inspection punch list (create → assign → verify → close) │
│  • Deficiency tracking (who, what, when, deadline)          │
│  • Safety meeting minutes (auto-generate from voice)        │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** Procore, Autodesk Construction Cloud, PlanGrid, Primavera P6, OSHA databases, weather APIs, subcontractor portals.

**Monetization:** $199/user/month (GC firms), $50/user/month (subcontractors).

---

### 1.2 BIM Coordinator Harness
**Роль:** Управление 3D-моделью здания, clash detection, coordination между MEP/structural/architectural.

**Почему generic не работает:**
- **Clash detection:** 10,000+ conflicts в модели. Нужен priority scoring (критичность × сложность fix).
- **Model versioning:** Revit/Navisworks файлы — 500MB+, 20+ disciplines. Generic агент не откроет.
- **LOD (Level of Development):** каждый элемент модели имеет «уровень детализации» — от conceptual до fabrication-ready.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  CLASH DETECTION INTELLIGENCE                               │
│  • Automated clash run (Navisworks API)                     │
│  • Clash classification (hard/soft/clearance/workflow)      │
│  • Priority matrix (impact on schedule × cost × safety)     │
│  • Resolution assignment (какой trade отвечает?)            │
├─────────────────────────────────────────────────────────────┤
│  MODEL COORDINATION                                         │
│  • Discipline sync tracking (кто обновил, когда)            │
│  • LOD compliance audit (соответствует ли требованиям?)     │
│  • COBie data extraction (handover to facility management)  │
│  • 4D/5D linking (model + schedule + cost)                  │
├─────────────────────────────────────────────────────────────┤
│  COORDINATION MEETINGS                                      │
│  • Meeting prep (список unresolved clashes + owners)        │
│  • Real-time resolution tracking (в процессе meeting)       │
│  • Action item extraction (кто, что, когда)                 │
│  • Follow-up automation (напоминание о deadline)            │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** Revit API, Navisworks, BIM 360, Solibri, IFC parsers.

---

### 1.3 MEP Estimator Harness
**Роль:** Составление смет на mechanical/electrical/plumbing системы.

**Почему generic не работает:**
- **Takeoff:** измерение длин труб, количества fittings из чертежей. Требует понимания символов и спецификаций.
- **Labor productivity:** сколько часов на установку 100ft 4" PVC pipe? Зависит от height, accessibility, jurisdiction.
- **Material pricing:** медные трубы — volatile pricing, regional variations, supplier relationships.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  AUTOMATED TAKEOFF                                          │
│  • PDF/blueprint parsing (symbol recognition)               │
│  • Quantity extraction (length, count, area, volume)        │
│  • Spec cross-reference (match spec section to drawing)     │
│  • Missing info flagging ("нет detail на connection X")     │
├─────────────────────────────────────────────────────────────┤
│  PRICING INTELLIGENCE                                       │
│  • Supplier quote aggregation (3+ quotes per item)          │
│  • Historical pricing (что стоило на прошлом проекте?)      │
│  • Escalation forecasting (inflation, tariffs, shortages)   │
│  • Alternate value engineering ("а если использовать Y?")   │
├─────────────────────────────────────────────────────────────┤
│  LABOR ANALYSIS                                             │
│  • Productivity tables (RS Means, local union rates)        │
│  • Crew composition (journeyman + apprentice ratios)        │
│  • Overtime impact (schedule compression cost)              │
│  • Jurisdiction analysis (prevailing wage, union vs open)   │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** Planswift, Bluebeam, RS Means, supplier portals, labor rate databases.

---

## КЛАСТЕР 2: 🚚 Supply Chain & Logistics

### 2.1 Freight Broker Harness
**Роль:** Matching грузов с грузовиками, rate negotiation, tracking, problem resolution.

**Почему generic не работает:**
- **Rate volatility:** spot rates меняются каждые часы. Нужен real-time market intelligence.
- **Carrier vetting:** insurance, authority, safety rating, double-brokering detection.
- **Load tracking:** где груз? ETA? Detention? Lumper fees?

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  LOAD-CARRIER MATCHING ENGINE                               │
│  • Capacity forecasting (где грузовики, куда едут)          │
│  • Rate optimization (spot vs contract, lane history)       │
│  • Carrier scoring (on-time, damage rate, communication)    │
│  • Double-brokering detection (MC number verification)      │
├─────────────────────────────────────────────────────────────┤
│  DOCUMENT AUTOMATION                                        │
│  • BOL generation (Bill of Lading)                          │
│  • Rate confirmation (auto-send, auto-confirm)              │
│  • POD collection (Proof of Delivery)                       │
│  • Invoice reconciliation (match BOL → POD → invoice)       │
├─────────────────────────────────────────────────────────────┤
│  EXCEPTION MANAGEMENT                                       │
│  • Delay prediction (traffic, weather, HOS violations)      │
│  • Detention calculation (free time vs actual)              │
│  • Claims processing (damage, shortage, refusal)            │
│  • Rerouting (accident ahead → alternate route)             │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** DAT Load Board, Truckstop, McLeod, Samsara, KeepTruckin, FMCSA SAFER.

---

### 2.2 Warehouse Operations Harness
**Роль:** Управление складом: receiving, putaway, picking, packing, shipping, inventory accuracy.

**Почему generic не работает:**
- **WMS integration:** каждый warehouse — свой workflow (batch picking vs zone picking vs wave picking).
- **Labor standards:** сколько секунд на pick? Зависит от SKU, location, equipment.
- **Slotting optimization:** где разместить товар, чтобы minimize travel distance?

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  INVENTORY INTELLIGENCE                                     │
│  • Cycle count optimization (ABC analysis + velocity)       │
│  • Shrinkage detection (anomaly in inventory movement)      │
│  • Expiration management (FEFO — First Expired First Out)   │
│  • Cross-dock coordination (не класть на полку — сразу ship)│
├─────────────────────────────────────────────────────────────┤
│  LABOR OPTIMIZATION                                         │
│  • Pick path optimization (traveling salesman для warehouse)│
│  • Task batching (group orders by zone)                     │
│  • Performance tracking (units/hour, accuracy rate)         │
│  • Training identification (кто медленнее → coaching)       │
├─────────────────────────────────────────────────────────────┤
│  RECEIVING & SHIPPING                                       │
│  • ASN matching (Advanced Shipping Notice vs reality)       │
│  • Damaged goods documentation (фото + claim initiation)    │
│  • Carrier appointment scheduling (dock door optimization)  │
│  • Manifest validation (что должно быть vs что есть)        │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** SAP EWM, Manhattan WMS, Blue Yonder, Locus Robotics, Zebra devices.

---

### 2.3 Customs Broker Harness
**Роль:** Таможенное оформление: HS codes, duties, documentation, compliance.

**Почему generic не работает:**
- **HS Classification:** 5,000+ commodity codes, country-specific rules, binding rulings.
- **Free Trade Agreements:** Rules of Origin (ROO) — where was it made? What %?
- **Document triage:** commercial invoice, packing list, COO, B/L, permits, licenses.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  HS CLASSIFICATION ENGINE                                   │
│  • Product description → HS code (with confidence score)    │
│  • Binding ruling lookup (CBP, EU TARIC, etc.)              │
│  • Classification consistency (same product = same code)    │
│  • New product onboarding (research + documentation)        │
├─────────────────────────────────────────────────────────────┤
│  DUTY OPTIMIZATION                                          │
│  • FTA eligibility (USMCA, EU-Japan, RCEP, etc.)            │
│  • Rules of Origin analysis (tariff shift vs value-added)   │
│  • Duty drawback identification (refund on exported goods)  │
│  • Anti-dumping/countervailing duty screening               │
├─────────────────────────────────────────────────────────────┤
│  COMPLIANCE & DOCUMENTATION                                 │
│  • Document checklist (by country, by product, by mode)     │
│  • Permit/license tracking (expiration, renewal)            │
│  • Entry summary validation (ACE, CHIEF, etc.)              │
│  • Audit preparation (CBP focused assessment readiness)     │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** ACE (Automated Commercial Environment), CHIEF/CDS, Descartes, Amber Road, Flexport API.

---

## КЛАСТЕР 3: 🏥 Healthcare (Non-clinical)

### 3.1 Medical Coder Harness
**Роль:** Перевод клинических записей в billing codes (ICD-10, CPT, HCPCS).

**Почему generic не работает:**
- **Specificity rules:** diabetes → E11.9 (unspecified) vs E11.65 (with hyperglycemia) vs E11.21 (with nephropathy). Один симптом — 20+ codes.
- **Documentation requirements:** чтобы bill определённый code, нужны конкретные elements в note.
- **Payer rules:** Medicare, Medicaid, commercial payers — каждый свои правила coverage.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  CLINICAL DOCUMENTATION ANALYSIS                            │
│  • Note parsing (H&P, progress notes, discharge summaries)  │
│  • Code suggestion (ICD-10-CM, CPT, HCPCS)                  │
│  • Specificity gap identification ("нужен laterality»)      │
│  • Query generation (вопросы врачу для clarification)       │
├─────────────────────────────────────────────────────────────┤
│  COMPLIANCE VALIDATION                                      │
│  • NCCI edits (National Correct Coding Initiative)          │
│  • MUE checks (Medically Unlikely Edits)                    │
│  • LCD/NCD verification (Local/National Coverage Determ)    │
│  • Modifier appropriateness (25, 59, etc.)                  │
├─────────────────────────────────────────────────────────────┤
│  REVENUE CYCLE IMPACT                                       │
│  • DRG optimization (inpatient reimbursement)               │
│  • Risk adjustment (HCC — Hierarchical Condition Categories)│
│  • Denial prediction (почему payer откажет?)                │
│  • Appeal letter generation (если denial)                   │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** Epic, Cerner, 3M Encoder, TruCode, Optum360, CMS databases.

---

### 3.2 Clinical Trial Coordinator Harness
**Роль:** Управление клиническими исследованиями: patient recruitment, visit scheduling, data collection, regulatory submissions.

**Почему generic не работает:**
- **Protocol compliance:** 200+ page protocol — каждое отклонение = deviation = regulatory risk.
- **Visit windows:** Visit 2 должна быть Day 15 ± 3 days. Нельзя просто «перенести».
- **Source data verification:** EDC (Electronic Data Capture) vs medical record — must match.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  PATIENT RECRUITMENT & RETENTION                            │
│  • Eligibility pre-screening (EMR → inclusion/exclusion)    │
│  • Recruitment forecasting (когда достигнем N=required?)    │
│  • Visit adherence tracking (missed visits → intervention)  │
│  • Retention strategies (transportation, reminders, compensation)│
├─────────────────────────────────────────────────────────────┤
│  PROTOCOL COMPLIANCE                                        │
│  • Visit window monitoring (±days enforcement)              │
│  • Concomitant medication screening (prohibited drugs)      │
│  • Adverse event detection (signal from EMR/lab values)     │
│  • Deviation documentation (what, why, corrective action)   │
├─────────────────────────────────────────────────────────────┤
│  REGULATORY & DATA QUALITY                                  │
│  • eCRF completion tracking (which fields missing?)         │
│  • Query management (data manager → site → response)        │
│  • Source document verification checklist                   │
│  • Submission readiness (CTD format, eCTD assembly)         │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** Veeva Vault, Medidata Rave, REDCap, CTMS systems, EMR integrations.

---

### 3.3 Revenue Cycle Management (RCM) Harness
**Роль:** Полный цикл: patient registration → charge capture → claim submission → payment posting → denial management → collections.

**Почему generic не работает:**
- **Payer-specific rules:** 1,000+ insurance companies, каждая свои формы, timelines, appeal processes.
- **Prior authorization:** многие процедуры требуют pre-approval. Denial = $0 revenue.
- **Patient responsibility:** deductible, copay, coinsurance — расчёт и collection.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  PRIOR AUTHORIZATION ORCHESTRATION                          │
│  • PA requirement detection (by procedure + payer)          │
│  • Clinical criteria matching (medical necessity)           │
│  • Submission automation (fax, portal, phone)               │
│  • Status tracking + escalation (peer-to-peer scheduling)   │
├─────────────────────────────────────────────────────────────┤
│  CLAIM SCRUBBING & SUBMISSION                               │
│  • Pre-submission validation (completeness, coding accuracy)│
│  • Payer-specific formatting (837P, 837I, paper)            │
│  • Real-time eligibility verification                       │
│  • Batch tracking (какие claims в пути, какие paid)         │
├─────────────────────────────────────────────────────────────┤
│  DENIAL MANAGEMENT                                          │
│  • Denial categorization (CO, PR, OA reason codes)          │
│  • Root cause analysis (что чаще всего отклоняется?)        │
│  • Appeal workflow (letter generation + evidence attachment)│
│  • Trend analysis (какой payer чаще отклоняет?)             │
├─────────────────────────────────────────────────────────────┤
│  PATIENT FINANCIAL EXPERIENCE                               │
│  • Cost estimation pre-service (good faith estimate)        │
│  • Payment plan setup (0% interest options)                 │
│  • Charity care screening (FPL qualification)               │
│  • Collection strategy (gentle → firm → agency)             │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** Epic Resolute, Cerner RevCycle, Waystar, Change Healthcare, Availity.

---

## КЛАСТЕР 4: ⚖️ Legal & Regulatory

### 4.1 eDiscovery Harness
**Роль:** Обработка электронных доказательств: preservation, collection, processing, review, production.

**Почему generic не работает:**
- **Data volumes:** 10TB+ emails, documents, chats. Нужен distributed processing.
- **Privilege detection:** attorney-client privileged communications must NOT be produced.
- **Production formats:** load files, Bates numbering, redactions, metadata.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  DATA PROCESSING PIPELINE                                   │
│  • Ingestion (email, files, databases, mobile, cloud)       │
│  • Deduplication (global + near-duplicate detection)        │
│  • De-NIST (remove system files, known irrelevant)          │
│  • OCR + text extraction (scanned docs, images)             │
├─────────────────────────────────────────────────────────────┤
│  INTELLIGENT REVIEW                                         │
│  • Privilege detection (attorney names, law firm domains)   │
│  • Responsiveness prediction (relevant to claims/defenses)  │
│  • Hot document identification (smoking gun)                │
│  • Issue coding (assign to legal issues)                    │
├─────────────────────────────────────────────────────────────┤
│  PRODUCTION & QUALITY                                       │
│  • Redaction automation (PII, privileged, irrelevant)       │
│  • Bates numbering (sequential, gapless)                    │
│  • Load file generation (Concordance, Relativity, etc.)     │
│  • QC validation ( completeness, formatting, metadata)      │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** Relativity, Logikcull, Everlaw, DISCO, Nuix, Brainspace.

---

### 4.2 Regulatory Affairs Harness
**Роль:** Управление жизненным циклом продукта: submissions, labeling, adverse events, recalls.

**Почему generic не работает:**
- **Submission formats:** FDA 510(k), NDA, ANDA, BLA — каждая своя структура, требования, timelines.
- **Labeling:** prescribing information, patient information, SPL (Structured Product Labeling).
- **Post-market surveillance:** MDR (Medical Device Reporting), PSUR (Periodic Safety Update Reports).

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  SUBMISSION MANAGEMENT                                      │
│  • Submission type selection (510k vs PMA vs De Novo)       │
│  • Document assembly (CTD modules 1-5)                      │
│  • eCTD publishing (XML, PDF, validation)                   │
│  • FDA correspondence tracking (IR, CRL, approval)          │
├─────────────────────────────────────────────────────────────┤
│  LABELING INTELLIGENCE                                      │
│  • SPL generation (XML format for FDA)                      │
│  • Label comparison (US vs EU vs Japan vs Canada)           │
│  • Change control (what changed, why, impact)               │
│  • Translation management (30+ languages)                   │
├─────────────────────────────────────────────────────────────┤
│  POST-MARKET SURVEILLANCE                                   │
│  • Adverse event triage (serious vs non-serious, expected)  │
│  • MDR/PSUR automation (data aggregation, narrative)        │
│  • Signal detection (trending AEs across products)          │
│  • Recall management (classification, notification, closeout)│
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** Veeva Vault RIM, MasterControl, SAP PLM, FDA ESG, EMA SPOR.

---

## КЛАСТЕР 5: 🏦 Financial Services

### 5.1 Underwriting Harness (P&C Insurance)
**Роль:** Оценка риска и pricing страховых полисов.

**Почему generic не работает:**
- **Risk factors:** 100+ variables (construction type, occupancy, protection class, CAT exposure, loss history).
- **Rating algorithms:** proprietary formulas, state filing requirements, reinsurance treaties.
- **Appetite matching:** не каждый риск подходит компании (capacity, concentration).

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  RISK ASSESSMENT ENGINE                                     │
│  • Property inspection analysis (photos, satellite, IoT)    │
│  • CAT modeling (flood, earthquake, hurricane zones)        │
│  • Loss history analysis (trending, development factors)    │
│  • Comparable benchmarking (what do peers charge?)          │
├─────────────────────────────────────────────────────────────┤
│  PRICING INTELLIGENCE                                       │
│  • Rate adequacy (premium vs expected loss + expense)       │
│  • Competitive positioning (market rate comparison)         │
│  • Reinsurance impact (how much ceded, at what cost?)       │
│  • State filing compliance (rates must be approved)         │
├─────────────────────────────────────────────────────────────┤
│  APPETITE & CAPACITY                                        │
│  • Underwriting guidelines enforcement (auto-decline rules) │
│  • Concentration monitoring (too much in one zip code?)     │
│  • Reinsurance treaty compliance (max retention)            │
│  • Exception tracking (who approved outside guidelines?)    │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** Verisk (ISO), CoreLogic, RMS/Moody's, Duck Creek, Guidewire.

---

### 5.2 Claims Adjuster Harness
**Роль:** Обработка страховых claims: investigation, evaluation, negotiation, settlement.

**Почему generic не работает:**
- **Fraud detection:** staged accidents, inflated damages, phantom injuries.
- **Coverage analysis:** does this policy cover this peril? Exclusions? Limits?
- **Reserve setting:** сколько денег зарезервировать? Under-reserve = bad. Over-reserve = capital inefficiency.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  FRAUD DETECTION                                            │
│  • Red flag identification (inconsistent statements, timing)│
│  • Social media surveillance (claimant activities)          │
│  • Network analysis (connections to known fraud rings)      │
│  • Medical bill review (upcoding, unbundling, phantom)      │
├─────────────────────────────────────────────────────────────┤
│  COVERAGE & LIABILITY                                       │
│  • Policy interpretation (what's covered, what's excluded)  │
│  • Liability assessment (% fault allocation)                │
│  • Subrogation identification (can we recover from 3rd party?)│
│  • Statute of limitations tracking (deadline to file suit)  │
├─────────────────────────────────────────────────────────────┤
│  SETTLEMENT OPTIMIZATION                                    │
│  • Reserve adequacy (current vs projected settlement)       │
│  • Negotiation strategy (initial offer → walk-away point)   │
│  • Comparable settlements (what paid for similar injuries?) │
│  • Litigation risk scoring (probability of going to trial)  │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** ClaimCenter, Mitchell, CCC, ISO ClaimSearch, medical bill review platforms.

---

## КЛАСТЕР 6: 🎓 Education & Research

### 6.1 Grant Writer Harness
**Роль:** Подготовка grant proposals: NIH, NSF, ERC, Wellcome Trust, etc.

**Почему generic не работает:**
- **Specific aims:** 1-page summary, которое определяет судьбу $5M+ funding. Требует deep scientific reasoning.
- **Review criteria:** significance, innovation, approach, investigator, environment — каждый критерий оценивается отдельно.
- **Budget justification:** salaries, equipment, indirect costs — must comply with institutional rates.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  FUNDING OPPORTUNITY MATCHING                               │
│  • PI profile → relevant RFPs (based on past work, keywords)│
│  • Deadline tracking (LOI, full proposal, JIT, just-in-time)│
│  • Eligibility verification (career stage, citizenship, etc)│
│  • Success probability scoring (based on past awards)       │
├─────────────────────────────────────────────────────────────┤
│  PROPOSAL DEVELOPMENT                                       │
│  • Specific Aims crafting (1 page, compelling narrative)    │
│  • Literature gap analysis (what's missing, why it matters) │
│  • Approach design (aims → experiments → milestones)        │
│  • Preliminary data integration (what we already have)      │
├─────────────────────────────────────────────────────────────┤
│  COMPLIANCE & SUBMISSION                                    │
│  • Budget construction (salary, fringe, equipment, indirect)│
│  • Biosketch formatting (NIH format, ongoing support)       │
│  • Collaboration letters (template + customization)         │
│  • System validation (SciENcv, Research.gov, etc.)          │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** NIH Reporter, NSF Award Search, Pivot, Grants.gov, SciENcv, institutional systems.

---

### 6.2 Accreditation Coordinator Harness
**Роль:** Подготовка к аккредитации университетов/программ (regional, programmatic, specialized).

**Почему generic не работает:**
- **Standards mapping:** 50+ standards, каждый с sub-criteria, evidence requirements.
- **Self-study:** 200+ page document, cross-referencing policies, data, assessment results.
- **Site visit:** coordinating schedules, rooms, documents, interviews, logistics.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  STANDARDS COMPLIANCE TRACKING                              │
│  • Standard-by-standard gap analysis (met / partially / not)│
│  • Evidence inventory (policies, minutes, reports, data)    │
│  • Continuous improvement tracking (closing gaps over time) │
│  • Peer institution benchmarking (how do we compare?)       │
├─────────────────────────────────────────────────────────────┤
│  SELF-STUDY ORCHESTRATION                                   │
│  • Chapter assignment (who writes what, by when)            │
│  • Cross-reference validation (no contradictions)           │
│  • Data integration (enrollment, retention, graduation, jobs)│
│  • Review cycles (draft → feedback → revision → final)      │
├─────────────────────────────────────────────────────────────┤
│  SITE VISIT MANAGEMENT                                      │
│  • Schedule optimization (interviews, tours, meetings)      │
│  • Document room preparation (physical + digital)           │
│  • Stakeholder briefing (what to say, what not to say)      │
│  • Exit report anticipation (likely findings → prep)        │
└─────────────────────────────────────────────────────────────┘
```

---

## КЛАСТЕР 7: 🏭 Industrial & Energy

### 7.1 Process Safety Engineer Harness
**Роль:** Управление рисками на химических/нефтеперерабатывающих объектах: HAZOP, LOPA, MOC, incident investigation.

**Почему generic не работает:**
- **HAZOP:** structured hazard analysis — каждый parameter (temperature, pressure, flow) × guideword (high, low, no, reverse) = deviation. Нужен facilitator + scribe.
- **LOPA:** Layer of Protection Analysis — quantifying risk reduction.
- **MOC:** Management of Change — любое изменение (valve type, software version) требует safety review.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  HAZOP / LOPA AUTOMATION                                    │
│  • Deviation generation (parameter × guideword matrix)      │
│  • Cause-consequence mapping (what happens, how bad?)       │
│  • Safeguard identification (what prevents/mitigates?)      │
│  • Risk ranking (frequency × consequence = risk matrix)     │
├─────────────────────────────────────────────────────────────┤
│  MANAGEMENT OF CHANGE (MOC)                                 │
│  • Change categorization (minor vs significant vs emergency)│
│  • Safety review routing (who must approve?)                │
│  • PSSR (Pre-Startup Safety Review) checklist               │
│  • Closeout verification (all actions complete before start)│
├─────────────────────────────────────────────────────────────┤
│  INCIDENT INVESTIGATION                                     │
│  • Timeline reconstruction (what happened, when, sequence)  │
│  • Root cause analysis (5 Whys, fishbone, bow-tie)          │
│  • Action item tracking (who, what, when, verification)     │
│  • Lessons learned dissemination (cross-plant sharing)      │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** PHA-Pro, BowTieXP, SAP MOC, OSIsoft PI (process data), incident databases.

---

### 7.2 Grid Operator Harness
**Роль:** Управление электросетью: dispatch, load balancing, contingency analysis, renewables integration.

**Почему generic не работает:**
- **Real-time:** decisions за секунды. LLM inference — слишком медленно.
- **Deterministic rules:** N-1 contingency (сеть должна выдержать отключение ЛЮБОГО одного элемента).
- **Market rules:** ISO/RTO markets — complex bidding, clearing, settlement.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  REAL-TIME DISPATCH SUPPORT                                 │
│  • Load forecasting (next hour, next day, next week)        │
│  • Generation scheduling (economic dispatch)                │
│  • Renewable forecasting (solar/wind variability)           │
│  • Reserve adequacy (spinning, non-spinning, replacement)   │
├─────────────────────────────────────────────────────────────┤
│  CONTINGENCY ANALYSIS                                       │
│  • N-1 screening (what if each element fails?)              │
│  • Voltage stability assessment                             │
│  • Thermal limit monitoring (line overload)                 │
│  • Remedial action scheme (automatic response if contingency)│
├─────────────────────────────────────────────────────────────┤
│  MARKET OPERATIONS                                          │
│  • Bid optimization (maximize revenue for generator)        │
│  • Congestion management (transmission constraints)         │
│  • Settlement verification (did we get paid correctly?)     │
│  • FERC compliance (market manipulation rules)              │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** SCADA/EMS, GE PSLF, Siemens PSS/E, ISO/RTO market systems, weather APIs.

---

### 7.3 Oil & Gas Reservoir Engineer Harness
**Роль:** Оценка и управление нефтяными/газовыми месторождениями: reserves estimation, production optimization, EOR.

**Почему generic не работает:**
- **Reserves classification:** P1 (proved), P2 (probable), P3 (possible) — strict SEC/PRMS rules.
- **Decline curve analysis:** Arps, Duong, stretched exponential — each applicable in different contexts.
- **Simulation:** reservoir simulation models — 1M+ grid cells, run for days on HPC.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  RESERVES ESTIMATION & REPORTING                            │
│  • Decline curve analysis (fit + forecast + uncertainty)    │
│  • Material balance (volumetric method)                     │
│  • Simulation post-processing (3D model → reserves)         │
│  • SEC/PRMS compliance (documentation, audit trail)         │
├─────────────────────────────────────────────────────────────┤
│  PRODUCTION OPTIMIZATION                                    │
│  • Well performance analysis (skin, productivity index)     │
│  • Artificial lift optimization (ESP, gas lift, rod pump)   │
│  • Workover candidate identification (which well to fix?)   │
│  • EOR screening (which method for this reservoir?)         │
├─────────────────────────────────────────────────────────────┤
│  FIELD DEVELOPMENT PLANNING                                 │
│  • Well placement optimization (where to drill next?)       │
│  • Facility sizing (processing capacity, pipelines)         │
│  • Economic evaluation (NPV, IRR, break-even)               │
│  • Risk analysis (geologic, technical, commercial, political)│
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** Petrel, Eclipse, CMG, IHS Harmony, ARIES economics, OFM production analysis.

---

## КЛАСТЕР 8: 🌾 Agriculture & Food

### 8.1 Agronomist Harness
**Роль:** Управление сельскохозяйственным производством: crop planning, pest management, irrigation, fertilization.

**Почему generic не работает:**
- **Soil variability:** одно поле — 5+ soil types, each with different nutrient needs.
- **Weather dependency:** frost, drought, heat stress — decisions за часы.
- **Pest lifecycle:** scouting, threshold levels, resistance management, spray timing.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  PRECISION CROP MANAGEMENT                                  │
│  • Variable rate prescriptions (seed, fertilizer, chemicals)│
│  • Yield map analysis (why low here, high there?)           │
│  • Satellite imagery analysis (NDVI, moisture stress)       │
│  • Soil sampling optimization (where to sample, how often)  │
├─────────────────────────────────────────────────────────────┤
│  INTEGRATED PEST MANAGEMENT                                 │
│  • Scouting log (pest counts, damage ratings, locations)    │
│  • Threshold alerts (when to spray, not just «if seen»)     │
│  • Resistance management (rotate modes of action)           │
│  • Spray record (what, when, where, rate, weather)          │
├─────────────────────────────────────────────────────────────┤
│  IRRIGATION OPTIMIZATION                                    │
│  • Soil moisture monitoring (sensors + ET calculation)      │
│  • Crop water demand (growth stage × weather)               │
│  • Scheduling (when and how much to irrigate)               │
│  • Energy cost optimization (pump during off-peak)          │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** Climate FieldView, Granular, John Deere Operations Center, soil sensors, weather APIs, drone imagery.

---

### 8.2 Food Safety & Quality Harness
**Роль:** Управление безопасностью пищевых продуктов: HACCP, supplier audits, recalls, lab testing.

**Почему generic не работает:**
- **HACCP:** Hazard Analysis Critical Control Points — 7 principles, each with monitoring, corrective actions, verification.
- **Supplier approval:** audits, certifications, COAs, specifications.
- **Traceability:** one-up, one-back — where did this ingredient come from? Where did it go?

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  HACCP PLAN MANAGEMENT                                      │
│  • Hazard analysis (biological, chemical, physical)         │
│  • CCP monitoring (critical limits, frequency, records)     │
│  • Deviation handling (corrective actions, verification)    │
│  • Plan reassessment (annual + trigger-based)               │
├─────────────────────────────────────────────────────────────┤
│  SUPPLIER QUALITY                                           │
│  • Approval workflow (audit, cert, COA, spec match)         │
│  • Performance scorecard (quality, delivery, service)       │
│  • Risk ranking (high/medium/low — audit frequency)         │
│  • Issue tracking (complaints, rejections, CAPA)            │
├─────────────────────────────────────────────────────────────┤
│  TRACEABILITY & RECALL                                      │
│  • Lot genealogy (raw material → WIP → finished → customer) │
│  • Mock recall execution (can we trace in 2 hours?)         │
│  • Recall simulation (scope, notification, effectiveness)   │
│  • Regulatory notification (FDA, FSIS, CFIA timelines)      │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** Safefood 360, IFS, SQF databases, SAP QM, laboratory information systems (LIMS).

---

## КЛАСТЕР 9: 🎨 Creative & Media

### 9.1 Film/TV Production Coordinator Harness
**Роль:** Управление производством: scheduling, budgeting, locations, cast/crew, permits, post-production.

**Почему generic не работает:**
- **Shooting schedule:** 100+ scenes, each with location, cast, props, special effects, weather dependencies.
- **Day-out-of-days:** когда каждый актёр нужен на площадке. Нельзя пересечь с другим проектом.
- **Budget tracking:** above-the-line (talent) vs below-the-line (crew, equipment, locations).

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  SCHEDULE ORCHESTRATION                                     │
│  • Stripboard management (scene order, locations, setups)   │
│  • Cast availability (conflicts with other projects)        │
│  • Location permitting (parks, streets, private property)   │
│  • Weather contingency (rain day planning)                  │
├─────────────────────────────────────────────────────────────┤
│  BUDGET & COST CONTROL                                      │
│  • Cost report generation (actual vs budget, by category)   │
│  • Purchase order tracking (who approved, what's delivered) │
│  • Petty cash reconciliation                                │
│  • Tax incentive optimization (where to shoot for credits)  │
├─────────────────────────────────────────────────────────────┤
│  POST-PRODUCTION COORDINATION                               │
│  • Dailies management (upload, review, select, note)        │
│  • VFX shot tracking (vendor, version, approval status)     │
│  • Music licensing (clearance, rights, usage)               │
│  • Delivery specs (Netflix, Amazon, theatrical — each different)│
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** Movie Magic Scheduling, Scenechronize, Wrapbook, SetHero, StudioBinder.

---

### 9.2 Game Localization Harness
**Роль:** Перевод и адаптация видеоигр: text, voice, UI, cultural references, compliance.

**Почему generic не работает:**
- **Context dependency:** «Attack!» может быть глаголом или существительным. Нужен in-game context.
- **String limits:** UI text must fit within pixel constraints (Japanese → German expansion).
- **Cultural adaptation:** jokes, references, colors, symbols — каждая культура своя.
- **Rating compliance:** ESRB, PEGI, CERO — each region different requirements.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  CONTEXTUAL TRANSLATION                                     │
│  • In-game screenshot reference (see the UI before translating)│
│  • String ID mapping (connect text to game object)          │
│  • Length validation (fit within UI constraints)            │
│  • Terminology consistency (glossary enforcement)           │
├─────────────────────────────────────────────────────────────┤
│  CULTURAL ADAPTATION                                        │
│  • Reference replacement (local celebrities, holidays)      │
│  • Humor adaptation (what's funny in target culture?)       │
│  • Symbol/color review (avoid cultural offense)             │
│  • Voice direction (tone, accent, casting notes)            │
├─────────────────────────────────────────────────────────────┤
│  COMPLIANCE & TESTING                                       │
│  • Rating requirements (blood, gambling, language, nudity)  │
│  • Legal text (EULA, privacy policy, credits)               │
│  • Linguistic QA (in-game testing for truncation, context)  │
│  • Bug reporting (translation bugs → dev tracking)          │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** Crowdin, Phrase, MemoQ, XLOC, proprietary game engines (Unity, Unreal).

---

## КЛАСТЕР 10: 🛡️ Public Safety & Defense

### 10.1 Emergency Dispatcher Harness
**Роль:** Приём и маршрутизация экстренных вызовов: 911/112, prioritization, resource dispatch, pre-arrival instructions.

**Почему generic не работает:**
- **Life-or-death latency:** каждая секунда считается. LLM inference — риск.
- **Protocol adherence:** каждый тип incident (cardiac arrest, structure fire, active shooter) — strict protocol.
- **Multi-agency coordination:** police, fire, EMS — каждая своя dispatch, но нужна unified situational awareness.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  CALL INTAKE & TRIAGE                                       │
│  • Protocol-guided questioning (MPDS, FPDS, PPDS)           │
│  • Location verification (address, cross-street, landmarks) │
│  • Severity assessment (Alpha/Bravo/Charlie/Delta/Echo)     │
│  • Language translation (real-time for non-English callers) │
├─────────────────────────────────────────────────────────────┤
│  RESOURCE DISPATCH                                          │
│  • Unit recommendation (closest available, right capability)│
│  • Mutual aid coordination (neighboring jurisdictions)      │
│  • Staging area management (mass casualty incidents)        │
│  • Helicopter/ specialty team dispatch                      │
├─────────────────────────────────────────────────────────────┤
│  PRE-ARRIVAL SUPPORT                                        │
│  • CPR instructions (real-time, step-by-step)               │
│  • Bleeding control (tourniquet, wound packing)             │
│  • Childbirth assistance                                    │
│  • Evacuation guidance (fire, hazmat, active shooter)       │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** CAD (Computer-Aided Dispatch), NG911, GIS/mapping, radio systems, ProQA protocols.

---

### 10.2 Military Mission Planning Harness
**Роль:** Планирование военных операций: intelligence, logistics, force protection, ROE.

**Почему generic не работает:**
- **Classification:** most data is classified. Cloud LLM — невозможен.
- **ROE (Rules of Engagement):** when can you shoot? Complex legal/moral framework.
- **Multi-domain:** air, land, sea, space, cyber — each with different constraints.

**Уникальная архитектура:**
```
┌─────────────────────────────────────────────────────────────┐
│  INTELLIGENCE FUSION                                        │
│  • Multi-source integration (SIGINT, HUMINT, GEOINT, OSINT) │
│  • Threat assessment (capability × intent × opportunity)    │
│  • Pattern of life analysis (enemy behavior prediction)     │
│  • Deception detection (is this real or feint?)             │
├─────────────────────────────────────────────────────────────┤
│  COURSE OF ACTION DEVELOPMENT                               │
│  • COA generation (multiple options with pros/cons)         │
│  • Wargaming (red team vs blue team simulation)             │
│  • Risk assessment (casualty estimate, mission success)     │
│  • ROE compliance check (legal review of each action)       │
├─────────────────────────────────────────────────────────────┤
│  LOGISTICS & SUSTAINMENT                                    │
│  • Supply chain (ammo, fuel, food, medical, spare parts)    │
│  • Maintenance scheduling (preventive, corrective, overhaul)│
│  • Medical evacuation planning (MEDEVAC routes, times)      │
│  • Personnel rotation (rest, recuperation, replacement)     │
└─────────────────────────────────────────────────────────────┘
```

**Tool Surface:** C2 systems, Palantir, DCGS-A, classified networks, simulation tools (JTLS, VBS).

---

## 📊 Матрица: Все 30+ ролей одним взглядом

| # | Кластер | Роль | Размер рынка | Сложность | Технология | Окно |
|---|---------|------|-------------|-----------|-----------|------|
| 1 | 🏗️ Built Env | Construction Superintendent | $50B | 🔴 Высокая | 🟡 Средняя | 2026–2027 |
| 2 | 🏗️ Built Env | BIM Coordinator | $20B | 🔴 Высокая | 🟡 Средняя | 2026–2027 |
| 3 | 🏗️ Built Env | MEP Estimator | $15B | 🟡 Средняя | 🟢 Высокая | 2026–2027 |
| 4 | 🚚 Supply Chain | Freight Broker | $80B | 🟡 Средняя | 🟢 Высокая | 2026–2027 |
| 5 | 🚚 Supply Chain | Warehouse Operations | $40B | 🟡 Средняя | 🟢 Высокая | 2026–2027 |
| 6 | 🚚 Supply Chain | Customs Broker | $25B | 🟡 Средняя | 🟡 Средняя | 2026–2027 |
| 7 | 🏥 Healthcare | Medical Coder | $30B | 🟡 Средняя | 🟢 Высокая | 2026–2027 |
| 8 | 🏥 Healthcare | Clinical Trial Coordinator | $20B | 🔴 Высокая | 🟡 Средняя | 2026–2028 |
| 9 | 🏥 Healthcare | RCM Specialist | $50B | 🟡 Средняя | 🟢 Высокая | 2026–2027 |
| 10 | ⚖️ Legal | eDiscovery Specialist | $15B | 🟡 Средняя | 🟢 Высокая | 2026–2027 |
| 11 | ⚖️ Legal | Regulatory Affairs | $25B | 🔴 Высокая | 🟡 Средняя | 2026–2028 |
| 12 | 🏦 Finance | P&C Underwriter | $40B | 🔴 Высокая | 🟡 Средняя | 2026–2028 |
| 13 | 🏦 Finance | Claims Adjuster | $35B | 🟡 Средняя | 🟢 Высокая | 2026–2027 |
| 14 | 🎓 Education | Grant Writer | $10B | 🟡 Средняя | 🟢 Высокая | 2026–2027 |
| 15 | 🎓 Education | Accreditation Coordinator | $5B | 🟡 Средняя | 🟢 Высокая | 2026–2027 |
| 16 | 🏭 Industrial | Process Safety Engineer | $20B | 🔴 Высокая | 🔴 Низкая | 2027–2029 |
| 17 | 🏭 Industrial | Grid Operator | $30B | 🔴 Высокая | 🔴 Низкая | 2027–2029 |
| 18 | 🏭 Industrial | Reservoir Engineer | $15B | 🔴 Высокая | 🔴 Низкая | 2027–2029 |
| 19 | 🌾 Agriculture | Agronomist | $25B | 🟡 Средняя | 🟢 Высокая | 2026–2027 |
| 20 | 🌾 Agriculture | Food Safety Manager | $20B | 🟡 Средняя | 🟢 Высокая | 2026–2027 |
| 21 | 🎨 Creative | Film Production Coordinator | $15B | 🟡 Средняя | 🟢 Высокая | 2026–2027 |
| 22 | 🎨 Creative | Game Localization Manager | $5B | 🟡 Средняя | 🟢 Высокая | 2026–2027 |
| 23 | 🛡️ Public Safety | 911 Dispatcher | $10B | 🔴 Высокая | 🔴 Низкая | 2027–2029 |
| 24 | 🛡️ Public Safety | Military Mission Planner | $50B | 🔴 Высокая | 🔴 Низкая | 2027–2030 |

*(+ ещё 6+ ролей в расширенной версии: Real Estate Appraiser, Social Worker, Archaeologist, Museum Registrar, Diplomatic Protocol Officer, Urban Planner)*

---

## 🎯 Мета-инсайты

### 1. **Professional harness = ontology + workflow + compliance**
Generic агент не знает:
- Что такое «submittal log» в строительстве
- Что такое «N-1 contingency» в энергетике
- Что такое «binding ruling» в таможне
- Что такое «DRG optimization» в медицинском биллинге

Это не «ещё немного контекста» — это **целые миры знаний**, которых нет в training data.

### 2. **Sub-professional roles — это where the money is**
Не «строительство», а **MEP Estimator**.  
Не «логистика», а **Customs Broker**.  
Не «энергетика», а **Grid Operator**.  

Каждая sub-role — это $5B–$50B рынок с **zero competition** от AI.

### 3. **Tool integration — главный барьер**
Professional harness'ы требуют интеграции с:
- Legacy ERP (SAP, Oracle)
- Industry-specific software (Procore, Revit, Veeva, Relativity)
- Regulatory systems (FDA ESG, ACE, FERC)
- Hardware (SCADA, sensors, drones)

Это **moat**, который не скопировать за неделю.

### 4. **B2B sales cycle = 6–18 месяцев**
Но **land-and-expand** работает:
- Начни с одного user (один estimator, один coder)
- Покажи ROI (сэкономил 10 часов/неделю)
- Распространи на команду, потом на отдел, потом на компанию

### 5. **The «Workflow Archaeology» problem**
Многие professional workflows **не документированы**. Они живут в головах 55-летних специалистов, которые уходят на пенсию. Harness — это способ **capture и preserve** этот tribal knowledge.

---

> **«Не строй агента для „строительства". Строй harness для superintendent'а, который в 6 утра проверяет, приехал ли concrete, и знает, что если нет — cascade delay на $50K.»**

---

*Анализ составлен на основе: архитектурных паттернов harness-систем, industry-specific workflows, regulatory frameworks, и логических выводов из специализации agentic systems для B2B вертикалей.*
