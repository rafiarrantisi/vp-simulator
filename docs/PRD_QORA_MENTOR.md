# Qora Mentor — Product Requirements Document

> **Version:** 1.0  
> **Date:** August 15, 2026  
> **Author:** Hermes Agent (Ker)  
> **Status:** Approved (Aug 16, 2026 — Arran) — Phase 1-3 shipped  
> **Design Constraint:** MUST use existing design system (design.css tokens, no CSS changes)

---

## 1. Executive Summary

**Qora Mentor** is a conversational AI learning path system that transforms Qora from a "case library" into a "personal clinical mentor". Users tell Qora about their exam goals in natural language; Qora proposes a structured learning journey, tracks progress across sessions, and provides metacognitive feedback through Clinical Reasoning Autopsy and Patient Continuity.

**Core Value Proposition:**  
> "Ceritain ujian kamu ke Qora. Dia susun rencana belajar, ingetin progress, dan kasih tau kapan kamu siap."

**Three Integrated Pillars:**
1. **Conversational Journey Builder** — User cerita → LLM propose → User customize → Journey dimulai
2. **Clinical Reasoning Autopsy** — Post-session analysis of reasoning pathway, not just checklist
3. **Patient Memory & Continuity** — Returning patients with evolving conditions based on previous errors

---

## 2. Problem Statement

### Current State (Qora v0.16)
- 92 cases across 10 specialties, all `in_review`
- Users browse catalogue → pick random case → session → score → repeat
- No structure, no progression, no cross-session learning
- Gamification: XP, streak, badges — but disconnected from actual learning goals
- Readiness unknown: users don't know "am I ready for OSCE?"

### Pain Points
| Pain | Evidence | Impact |
|:-----|:---------|:-------|
| "Ga tau mulai dari mana" | 92 cases, no guidance | Decision paralysis, random learning |
| "Ga tau siap apa engga" | No readiness metric | Anxiety, over/under-preparation |
| "Belajar tapi ga improve" | No feedback on reasoning | Repeated mistakes, plateau |
| "Kasusnya sama semua" | Static one-shot scenarios | Boredom, no continuity |

### Competitor Context
- **Cogni by Mediko**: Static OSCE simulation, topup quota, no journey, no continuity
- **Geeky Medics**: B2B institutional, video avatars, no personalization
- **Qora opportunity**: Personal, adaptive, conversational mentor

---

## 3. Solution Overview

### 3.1 User Flow (End-to-End)

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: STORY (Natural Language Input)                     │
│                                                              │
│  User opens "Mentor" tab → sees chat interface              │
│  User types: "Ujian gua 1 minggu lagi, masih bego pediatrik"│
│  System: Extracts context (timeline, level, weakness, goal)  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: PROPOSAL (LLM-Generated Journey)                   │
│                                                              │
│  Qora responds: "Oke, 7 hari ya. Ini rencana gua:           │
│  • Hari 1-2: Anamnesis dasar anak (bronchiolitis, febrile) │
│  • Hari 3-4: Red flags & emergency (dehydration, resp)     │
│  • Hari 5-6: Kompleks (abdominal, neuro)                    │
│  • Hari 7: Mock exam + review                               │
│  Estimasi 45-60 menit/hari. Siap?"                          │
│                                                              │
│  User: "Gas" / "Hari 3 ganti stunting dong" / "Terlalu berat"│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: JOURNEY EXECUTION (Daily Structured Learning)      │
│                                                              │
│  Tab "My Journey" shows:                                    │
│  • Progress bar (Day 3 of 7, 43% complete)                  │
│  • Today's case card (locked/unlocked/completed)            │
│  • Readiness meter (62% → target 80%)                       │
│  • Recent autopsy insights                                   │
│                                                              │
│  User clicks case → normal Qora session (chat → assess → score)│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4: REASONING AUTOPSY (Post-Session)                   │
│                                                              │
│  After score reveal, new section: "Clinical Reasoning Autopsy"│
│  • "Your pathway" vs "Expert pathway" side-by-side          │
│  • Errors detected: anchoring, premature closure, missed RF │
│  • "Pearl" insight card                                     │
│  • Readiness impact: +3% / -2% / 0%                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 5: PATIENT CONTINUITY (Cross-Session)                 │
│                                                              │
│  If autopsy detects missed red flag → trigger continuity:   │
│  "Returning patient: Ibu Siti (Visit 2)"                    │
│  Context: "Kemarin kamu diagnosa gastritis, kasih antasida" │
│  New complaint: "Dok, BAB saya hitam..."                    │
│  User must connect previous error to new presentation       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 6: READINESS ASSESSMENT (Journey Complete)            │
│                                                              │
│  "UKNPDPD Readiness Report"                                 │
│  • Overall: 78% (borderline pass)                           │
│  • Per dimension breakdown                                   │
│  • Weakest: Clinical safety (3 missed critical RFs)         │
│  • Recommendation: "Repeat Day 3-4" / "Focus on red flags"  │
│  • Disclaimer: "Estimasi, bukan guarantee"                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Feature Specification

### 4.1 Feature 1: Conversational Journey Builder

#### 4.1.1 User Story Input

**Interface:** Chat-style input in "Mentor" tab  
**Placeholder:** "Ceritain ke Qora: ujian apa, kapan, masih kurang di mana..."

**Example inputs:**
- "Ujian gua 1 minggu lagi, masih bego pediatrik"
- "Stase bedah bulan depan, belum pernah latihan appendicitis"
- "Mau latihan anamnesis dari nol, ga tau mulai dari mana"
- "Besok OSCE, panik banget"

**Backend Processing:**
```python
# LLM Prompt: Context Extraction
def extract_context(user_story: str) -> dict:
    prompt = f"""
    You are a medical education advisor. Extract learning context from this student's message.
    
    Student: "{user_story}"
    
    Return ONLY valid JSON:
    {{
        "timeline_days": 7 | 30 | 90 | null,
        "level": "preklinik" | "koas" | "ppds" | "general",
        "weaknesses": ["pediatrik", "bedah", "internal_medicine", ...],
        "goal": "osce" | "stase" | "general" | "mock_exam",
        "emotional_state": "panik" | "confident" | "overwhelmed" | "neutral",
        "special_needs": "string" | null,
        "confidence_score": 0-100  # self-reported
    }}
    """
    # Use deepseek-v4-flash with reasoning disabled
```

**Validation:**
- `timeline_days`: clamp to [1, 90]
- `level`: map Indonesian terms (preklinik=1, koas=2, ppds=3)
- `weaknesses`: map to specialty vocabulary (internal_medicine, surgery, paediatrics, etc.)

#### 4.1.2 Case Selection Algorithm

**Input:** context dict + available cases (92 cases from catalogue)  
**Output:** ordered list of case_ids with day assignment

**Algorithm:**
```python
def select_cases(context: dict, cases: list) -> list:
    # 1. Filter by level (difficulty)
    level_map = {"preklinik": 1, "koas": 2, "ppds": 3}
    target_difficulty = level_map.get(context["level"], 2)
    filtered = [c for c in cases if c["difficulty"] == target_difficulty]
    
    # 2. Prioritize weaknesses
    if context["weaknesses"]:
        priority = [c for c in filtered if c["specialty"] in context["weaknesses"]]
        others = [c for c in filtered if c["specialty"] not in context["weaknesses"]]
        filtered = priority + others
    
    # 3. Ensure mode mix (if timeline >= 3 days, include at least 1 osce_full)
    if context["timeline_days"] >= 3:
        osce_cases = [c for c in filtered if c["mode"] == "osce_full"]
        if not osce_cases:
            # Promote an anamnesis case to osce_full if available
            pass
    
    # 4. Order: foundational → advanced → mock exam
    # Sort by: red_flags count (asc), then complexity (asc)
    
    # 5. Assign to days
    days = context["timeline_days"]
    cases_per_day = max(1, len(filtered) // days)
    # Distribute evenly, with mock exam on last day
```

**LLM Refinement:**
```python
def generate_proposal(context: dict, selected_cases: list) -> dict:
    prompt = f"""
    Create a personalized learning journey proposal.
    
    Student context: {json.dumps(context)}
    Selected cases: {json.dumps(selected_cases)}
    
    Return JSON:
    {{
        "package_name": "string (e.g., 'Pediatrik Crash 7-Day')",
        "duration_days": {context['timeline_days']},
        "cases": [
            {{
                "day": 1,
                "case_id": "paed_bronchiolitis_001",
                "focus": "Anamnesis dasar anak",
                "estimated_minutes": 45,
                "learning_objective": "Menguasai anamnesis pada pasien anak dengan keluhan pernapasan"
            }}
        ],
        "reasoning": "Explain WHY this sequence helps the student",
        "readiness_start": 40,  # estimated from self-report
        "readiness_target": 80,
        "milestones": [
            {{"day": 3, "checkpoint": "Red flags pediatrik mastered"}},
            {{"day": 7, "checkpoint": "Ready for exam"}}
        ]
    }}
    """
```

#### 4.1.3 Proposal Presentation

**UI Component:** `QJourneyProposal` (new file: `qora-mentor.jsx`)

**Layout (matching existing design system):**
```
┌────────────────────────────────────────┐
│  🎓 Your Learning Journey              │
│  ─────────────────────────────────     │
│                                        │
│  📋 Pediatrik Crash 7-Day              │
│  ⏱ 7 days · ~45-60 min/day            │
│  🎯 Target: 80% readiness              │
│                                        │
│  [Progress bar: 0% → 80%]              │
│                                        │
│  ┌────────────────────────────────┐   │
│  │ Day 1: Anamnesis dasar anak    │   │
│  │ 🩺 Bronchiolitis               │   │
│  │ ~45 min · Available now        │   │
│  └────────────────────────────────┘   │
│  ┌────────────────────────────────┐   │
│  │ Day 2: Red flags demam anak    │   │
│  │ 🔒 Febrile child               │   │
│  │ Complete Day 1 to unlock       │   │
│  └────────────────────────────────┘   │
│  ...                                   │
│                                        │
│  [Reasoning card]                      │
│  "Karena ujian 1 minggu lagi dan       │
│   fokus pediatrik, saya susun dari     │
│   presentasi umum ke kompleks..."      │
│                                        │
│  [Accept Journey] [Customize] [Cancel] │
└────────────────────────────────────────┘
```

**Design tokens used:**
- Background: `var(--bg)`
- Card: `var(--surface)`, `var(--border)`, `var(--r-lg)`, `var(--sh-sm)`
- Primary button: `var(--primary)`, `#fff`
- Locked state: `var(--surface-2)`, `var(--text-3)`
- Progress bar: `var(--primary)` fill, `var(--surface-3)` track

#### 4.1.4 User Customization

**Options:**
1. **Accept** — Journey starts, first case unlocked
2. **Customize** — Chat-based adjustment:
   - "Hari 3 ganti stunting dong"
   - "Terlalu berat, ada yang lebih basic?"
   - "Tambahin kasus bedah dong"
3. **Cancel** — Back to free mode

**Customization flow:**
```
User: "Hari 3 ganti stunting"
  → LLM re-generates Day 3 case selection
  → Updated proposal shown
  → User accepts or further customizes
```

**Backend endpoint:**
```
POST /api/v2/journeys/{id}/customize
Body: { "feedback": "hari 3 ganti stunting" }
Response: { "updated_proposal": {...}, "changes": ["day_3: paed_stunting_001"] }
```

---

### 4.2 Feature 2: Clinical Reasoning Autopsy

#### 4.2.1 Concept

After each session, Qora doesn't just show score — it **dissects the user's reasoning process** and compares it to an expert pathway.

**Output sections:**
1. **Your Pathway** — Extracted from transcript + DDx + reasoning text
2. **Expert Pathway** — Gold standard from case + LLM generation
3. **Errors Detected** — Pattern-matched cognitive biases
4. **Pearl** — Actionable insight for improvement
5. **Readiness Impact** — How this session affects overall readiness

#### 4.2.2 Data Flow

```
Session transcript + DDx + management + score
  → Reasoning Autopsy Generator (LLM)
    → Extract user pathway:
      - Question sequence (open → closed → leading?)
      - Hypothesis generation (when, what)
      - Data gathering (targeted vs scattergun)
      - Synthesis (premature closure? anchoring?)
    → Generate expert pathway:
      - Ideal question sequence for this presentation
      - Key decision points
      - Red flag screening timing
      - Hypothesis refinement
    → Compare:
      - Identify divergence points
      - Classify error types
      - Assess severity (critical/moderate/minor)
    → Generate pearl:
      - "You anchored on gastritis after antasida response.
         In patients >45 with epigastric pain, always screen
         for GI bleeding before closing on benign diagnosis."
  → Store in reasoning_autopsies table
  → Update journey readiness (if in journey)
```

#### 4.2.3 Error Taxonomy

| Error Type | Description | Detection Pattern | Severity |
|:-----------|:------------|:------------------|:---------|
| **Anchoring** | Fixating on initial hypothesis | First DDx mentioned in first 3 turns, never changed | Moderate |
| **Premature closure** | Stopping data gathering too early | DDx stated before red flags screened | Critical |
| **Confirmation bias** | Only asking questions that confirm hypothesis | Question pattern matches expected DDx, no disconfirming questions | Moderate |
| **Scattergun** | Ordering too many investigations | >5 investigations without clear hypothesis | Minor |
| **Missed red flag** | Failing to screen critical red flag | Critical red flag in case, not elicited | Critical |
| **Poor signposting** | Disorganized interview flow | Random topic jumps, no transitions | Minor |
| **Leading questions** | Suggesting answers | "It's painful when you cough, right?" | Moderate |
| **Ignoring ICE** | Not exploring ideas/concerns/expectations | No ICE questions in transcript | Moderate |

#### 4.2.4 LLM Prompt: Autopsy Generation

```python
def generate_autopsy(case: CaseV2, transcript: list, ddx: dict, 
                     management: dict, score: dict) -> dict:
    prompt = f"""
    You are a senior clinical examiner performing a "reasoning autopsy" — 
    analyzing not just WHAT the student asked, but HOW they thought.
    
    CASE GROUND TRUTH:
    {json.dumps(build_judge_ground_truth(case))}
    
    STUDENT TRANSCRIPT:
    {format_transcript(transcript)}
    
    STUDENT DECISIONS:
    DDx: {ddx}
    Management: {management}
    Score: {score}
    
    EXPERT PATHWAY (generate this):
    1. Opening: How should the expert start?
    2. Data gathering: What sequence of questions?
    3. Hypothesis generation: When and what?
    4. Red flag screening: When and how?
    5. Synthesis: How to arrive at diagnosis?
    6. Management: Appropriate workup and treatment
    
    YOUR TASK:
    1. Extract the student's reasoning pathway from the transcript
    2. Compare with the expert pathway
    3. Identify errors from this taxonomy:
       - anchoring, premature_closure, confirmation_bias, scattergun,
         missed_red_flag, poor_signposting, leading_questions, ignoring_ice
    4. Generate a "clinical pearl" — one actionable insight
    
    Return JSON:
    {{
        "user_pathway": ["step1", "step2", ...],
        "expert_pathway": ["step1", "step2", ...],
        "divergence_points": [
            {{"step": 3, "user": "...", "expert": "...", "error_type": "..."}}
        ],
        "errors_detected": [
            {{"type": "premature_closure", "severity": "critical", 
              "description": "...", "evidence": "transcript quote"}}
        ],
        "pearl": "One actionable insight for improvement",
        "readiness_impact": -5  # +/- points to readiness score
    }}
    """
```

#### 4.2.5 UI Component: `QAutopsyCard`

**Layout (matching existing design):**
```
┌────────────────────────────────────────┐
│  🔬 Clinical Reasoning Autopsy         │
│  ─────────────────────────────────     │
│                                        │
│  [Tabs: Your Pathway | Expert | Errors]│
│                                        │
│  ┌─ Your Pathway ─────────────────┐   │
│  │ 1. "Sakit perut" → Gastritis   │   │
│  │ 2. "Nyeri 2 hari" → No RF      │   │
│  │ 3. "Antasida membantu" → Closed│   │
│  │ 4. ❌ Missed: "BAB hitam?"     │   │
│  └────────────────────────────────┘   │
│                                        │
│  ┌─ Expert Pathway ───────────────┐   │
│  │ 1. "Sakit perut" → Broad DDx   │   │
│  │ 2. SOCRATES + red flags        │   │
│  │ 3. "Antasida partial" → Alarm? │   │
│  │ 4. ✅ Screened: GI bleeding    │   │
│  └────────────────────────────────┘   │
│                                        │
│  ⚠️ Errors Detected                    │
│  ┌────────────────────────────────┐   │
│  │ 🔴 Premature closure (critical)│   │
│  │ "You stopped gathering data    │   │
│  │  after antasida response..."   │   │
│  └────────────────────────────────┘   │
│  ┌────────────────────────────────┐   │
│  │ 🟡 Anchoring (moderate)        │   │
│  │ "First hypothesis (gastritis)  │   │
│  │  never reconsidered..."        │   │
│  └────────────────────────────────┘   │
│                                        │
│  💎 Pearl                              │
│  ┌────────────────────────────────┐   │
│  │ "In patients >45 with epigastric│   │
│  │  pain, always screen for GI    │   │
│  │  bleeding before closing on    │   │
│  │  benign diagnosis."            │   │
│  └────────────────────────────────┘   │
│                                        │
│  Readiness impact: -3%                 │
│  [Got it] [Discuss with mentor]        │
└────────────────────────────────────────┘
```

**Design tokens:**
- Error card: `var(--red-l)` background, `var(--red-d)` text for critical
- Warning card: `var(--amber-l)` background, `var(--amber-d)` text
- Pearl card: `var(--teal-l)` background, `var(--teal-d)` text
- Tab active: `var(--primary)` border-bottom

---

### 4.3 Feature 3: Patient Memory & Continuity

#### 4.3.1 Concept

Patients return with evolving conditions based on what the user missed in previous sessions. This creates **longitudinal learning** — users see consequences of their reasoning errors.

**Example:**
- Visit 1: Ibu Siti, 45, epigastric pain → User diagnoses gastritis, misses "tinja hitam" red flag
- Visit 2 (3 days later): Ibu Siti returns — "Dok, obatnya habis, BAB saya hitam" → User must recognize GI bleeding complication
- Visit 3 (1 week later): Post-endoscopy follow-up → Management and safety-netting

#### 4.3.2 Data Model

```sql
-- Patient series (linked cases)
CREATE TABLE patient_series (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,                    -- "Ibu Siti"
    base_condition TEXT NOT NULL,          -- "gastritis"
    age INTEGER,
    gender TEXT,
    occupation TEXT,
    
    -- Case sequence
    case_sequence JSONB NOT NULL,          -- ["im_gastritis_001", "im_gi_bleeding_001", "im_gastritis_fu_001"]
    
    -- Trigger conditions
    triggers JSONB NOT NULL,               -- [{"type": "missed_red_flag", "value": "gi_bleeding", "target_case": "im_gi_bleeding_001"}]
    
    -- Context for next visit
    next_visit_context JSONB,              -- {"days_later": 3, "reason": "obat habis, gejala memburuk", "new_symptoms": ["tinja hitam"]}
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- User patient history (which series user has encountered)
CREATE TABLE user_patient_history (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    series_id TEXT REFERENCES patient_series(id),
    current_visit INTEGER DEFAULT 1,       -- which visit user is on
    last_session_id TEXT REFERENCES sessions(id),
    errors_detected JSONB,                 -- errors from last visit
    status TEXT DEFAULT 'active',          -- active, completed, abandoned
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 4.3.3 Trigger Logic

**When to trigger continuity:**
1. Autopsy detects `missed_red_flag` with severity = critical
2. Check if case has associated patient_series
3. If yes, queue next visit for user's next session
4. Next visit case = trigger's `target_case`

**Example:**
```python
def check_continuity_trigger(autopsy: dict, case_id: str, user_id: str) -> dict | None:
    # Find critical missed red flags
    critical_errors = [e for e in autopsy.get("errors_detected", []) 
                       if e.get("severity") == "critical" and e.get("type") == "missed_red_flag"]
    
    if not critical_errors:
        return None
    
    # Find matching patient series
    series = find_series_by_trigger(case_id, critical_errors[0]["value"])
    if not series:
        return None
    
    # Create or update user patient history
    history = get_or_create_history(user_id, series["id"])
    history["current_visit"] += 1
    history["errors_detected"] = autopsy["errors_detected"]
    history["status"] = "active"
    
    return {
        "next_case_id": series["case_sequence"][history["current_visit"] - 1],
        "context": series["next_visit_context"],
        "visit_number": history["current_visit"],
        "total_visits": len(series["case_sequence"])
    }
```

#### 4.3.4 Case File Format Extension

**New frontmatter fields for continuity cases:**
```yaml
# In case file: im_gi_bleeding_001.md
---
id: im_gi_bleeding_001
schema_version: 2
status: in_review
specialty: internal_medicine
system: gastrointestinal
presentation: "Melena (black stool)"
target_condition: "Upper GI bleeding"
difficulty: 2
estimated_minutes: 15
mode_default: osce_full

# NEW: Continuity fields
continuity:
  is_continuity: true
  series_id: "siti_gastritis_series"
  visit_number: 2
  previous_case_id: "im_gastritis_001"
  days_since_last: 3
  context_for_patient: |
    Kamu adalah Ibu Siti yang sama dari kunjungan sebelumnya.
    Kemarin kamu didiagnosis gastritis dan diberi antasida.
    Obatnya sudah habis, tapi sakitnya tidak membaik.
    Sekarang kamu mengalami BAB hitam (melena) sejak 2 hari yang lalu.
    Kamu khawatir ini sesuatu yang serius.

# ... rest of case
---
```

#### 4.3.5 Patient Prompt Extension

**Continuity context injection:**
```python
def build_patient_prompt(case: CaseV2, continuity_context: dict | None = None) -> str:
    base = case.body.strip()
    
    if continuity_context:
        context_block = f"""
===== CONTINUITY CONTEXT =====
You are a RETURNING patient. You have seen this doctor before.
Previous visit: {continuity_context.get('days_since_last', 'a few')} days ago.
Previous diagnosis: {continuity_context.get('previous_diagnosis', 'unknown')}.
Previous treatment: {continuity_context.get('previous_treatment', 'unknown')}.
Your current concern: {continuity_context.get('current_concern', 'something got worse')}.

IMPORTANT: You remember the previous visit. You can reference it naturally.
("Dok, kemarin saya ke sini..." / "Obat yang kemarin sudah habis...")
But you don't know medical details — you only know what you feel.
"""
        base = context_block + "\n\n" + base
    
    return base + "\n\n" + ANSWER_RESTRAINT + "\n\n" + GUARDRAIL
```

#### 4.3.6 UI Component: `QContinuityBanner`

**Shown in session setup when continuity case:**
```
┌────────────────────────────────────────┐
│  🔄 Returning Patient                  │
│  ─────────────────────────────────     │
│                                        │
│  👤 Ibu Siti, 45 · Visit 2 of 3       │
│                                        │
│  📋 Story so far:                      │
│  "Kemarin kamu didiagnosis gastritis,  │
│   diberi antasida. Obat habis,         │
│   gejala tidak membaik."               │
│                                        │
│  🆕 New complaint:                     │
│  "BAB hitam sejak 2 hari"              │
│                                        │
│  💡 This is your chance to correct     │
│     what you missed last time.         │
│                                        │
│  [Start Visit 2] [View Visit 1 Summary]│
└────────────────────────────────────────┘
```

**Design tokens:**
- Background: `var(--violet-l)` (continuity = purple theme)
- Border: `var(--violet)`
- Icon: 🔄 for returning patient
- Text: `var(--text-1)`, `var(--text-2)`

---

### 4.4 Feature 4: Journey Tracking & Readiness Score

#### 4.4.1 Journey Dashboard

**New tab in navigation:** "Mentor" (icon: 🎓)

**Layout (matching existing design):**
```
┌────────────────────────────────────────┐
│  🎓 My Mentor                          │
│  ─────────────────────────────────     │
│                                        │
│  [If no active journey:]               │
│  ┌────────────────────────────────┐   │
│  │  💬 Ceritain ke Qora           │   │
│  │  "Ujian gua 1 minggu lagi..."  │   │
│  │  [Start chatting]              │   │
│  └────────────────────────────────┘   │
│                                        │
│  [If active journey:]                  │
│  ┌────────────────────────────────┐   │
│  │  📋 Pediatrik Crash 7-Day      │   │
│  │  ████████░░ Day 3 of 7 (43%)   │   │
│  │                                │   │
│  │  Readiness: 62% → Target: 80%  │   │
│  │  ██████████░░░░░░░░░░░░        │   │
│  │                                │   │
│  │  Today: Dehydration Assessment │   │
│  │  🩺 paed_dehydration_001       │   │
│  │  [Start Case]                  │   │
│  │                                │   │
│  │  Recent Autopsy:               │   │
│  │  💎 "Improved on red flags!"   │   │
│  │  ⚠️ "Watch for anchoring"      │   │
│  └────────────────────────────────┘   │
│                                        │
│  [If completed journey:]               │
│  ┌────────────────────────────────┐   │
│  │  🎉 Journey Complete!          │   │
│  │  Final Readiness: 78%          │   │
│  │  [View Full Report]            │   │
│  │  [Start New Journey]           │   │
│  └────────────────────────────────┘   │
└────────────────────────────────────────┘
```

#### 4.4.2 Readiness Score Calculation

**Formula:**
```python
def calculate_readiness(user_id: str, journey_id: str | None = None) -> dict:
    # Get all completed sessions (journey or all)
    sessions = get_completed_sessions(user_id, journey_id)
    
    if not sessions:
        return {"score": 0, "confidence": "insufficient_data"}
    
    # Base score: weighted dimension averages
    dims = aggregate_dimensions(sessions)
    base_score = (
        0.20 * dims.get("history_coverage", 0) +
        0.15 * dims.get("red_flags", 0) +
        0.15 * dims.get("diagnostic_reasoning", 0) +
        0.15 * dims.get("management", 0) +
        0.10 * dims.get("physical_exam", 0) +
        0.10 * dims.get("communication", 0) +
        0.10 * dims.get("ice_fife", 0) +
        0.05 * dims.get("questioning_technique", 0)
    )
    
    # Trajectory bonus: improving vs declining
    scores = [s["overall"] for s in sessions[-5:]]  # last 5 sessions
    if len(scores) >= 3:
        trajectory = (scores[-1] - scores[0]) / len(scores)
        trajectory_bonus = min(1.1, max(0.9, 1.0 + trajectory / 100))
    else:
        trajectory_bonus = 1.0
    
    # Consistency bonus: regular practice
    dates = [s["completed_at"].date() for s in sessions]
    unique_dates = len(set(dates))
    total_days = (max(dates) - min(dates)).days + 1 if dates else 1
    consistency = min(1.0, unique_dates / max(1, total_days))
    consistency_bonus = 0.9 + (0.1 * consistency)
    
    # Autopsy penalty: unresolved critical errors
    unresolved_errors = count_unresolved_critical_errors(user_id)
    error_penalty = min(10, unresolved_errors * 2)
    
    # Final calculation
    raw_score = base_score * trajectory_bonus * consistency_bonus
    final_score = max(0, min(100, raw_score - error_penalty))
    
    # Confidence interval
    session_count = len(sessions)
    confidence = "high" if session_count >= 10 else "medium" if session_count >= 5 else "low"
    
    return {
        "score": round(final_score),
        "confidence": confidence,
        "session_count": session_count,
        "base_score": round(base_score),
        "trajectory_bonus": round(trajectory_bonus, 2),
        "consistency_bonus": round(consistency_bonus, 2),
        "error_penalty": error_penalty,
        "dimensions": dims,
        "interpretation": interpret_score(final_score)
    }

def interpret_score(score: int) -> dict:
    if score >= 90:
        return {"level": "distinction", "label": "Exam ready — predicted distinction", "color": "var(--teal)"}
    elif score >= 75:
        return {"level": "pass", "label": "Ready — predicted clear pass", "color": "var(--green)"}
    elif score >= 60:
        return {"level": "borderline", "label": "Borderline — needs targeted improvement", "color": "var(--amber)"}
    elif score >= 40:
        return {"level": "not_ready", "label": "Not ready — significant gaps", "color": "var(--red)"}
    else:
        return {"level": "foundation", "label": "Foundation needed — repeat basics", "color": "var(--red-d)"}
```

#### 4.4.3 Readiness Report UI

**Component:** `QReadinessReport`

```
┌────────────────────────────────────────┐
│  📊 UKNPDPD Readiness Report           │
│  ─────────────────────────────────     │
│                                        │
│  ┌────────────────────────────────┐   │
│  │         78%                    │   │
│  │    ████████████████░░░░        │   │
│  │                                │   │
│  │  Borderline — needs targeted   │   │
│  │  improvement                   │   │
│  │                                │   │
│  │  Confidence: Medium (7 sessions)│   │
│  └────────────────────────────────┘   │
│                                        │
│  Dimension Breakdown                   │
│  ┌────────────────────────────────┐   │
│  │  History coverage      85% ✅  │   │
│  │  Red flags            62% ⚠️   │   │
│  │  Diagnostic reasoning 71% ✅   │   │
│  │  Management           68% ⚠️   │   │
│  │  Communication        78% ✅   │   │
│  │  Clinical safety      55% 🔴   │   │
│  └────────────────────────────────┘   │
│                                        │
│  🔴 Critical: Clinical Safety          │
│  You missed 3 critical red flags in    │
│  your last 5 sessions. Focus on red    │
│  flag screening before your exam.      │
│                                        │
│  Recommended actions:                  │
│  1. Repeat Day 3-4 of journey          │
│  2. Practice red flag scenarios        │
│  3. Review safety-netting principles   │
│                                        │
│  ⚠️ Disclaimer                         │
│  Readiness score adalah estimasi       │
│  berdasarkan rubrik OSCE dan performa  │
│  latihan. Bukan guarantee kelulusan.   │
│  Gunakan sebagai panduan, bukan        │
│  pengganti persiapan resmi.            │
│                                        │
│  [Download PDF] [Share with Mentor]    │
└────────────────────────────────────────┘
```

---

## 5. Technical Architecture

### 5.1 Database Schema (New Tables)

```sql
-- ============================================
-- Qora Mentor Schema Extensions
-- Migration: alembic/versions/xxxx_add_mentor_system.py
-- ============================================

-- Learning journeys (conversational package)
CREATE TABLE learning_journeys (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    
    -- User input (raw)
    user_story TEXT NOT NULL,
    extracted_context JSONB NOT NULL,  -- {timeline_days, level, weaknesses, goal, emotional_state}
    
    -- LLM proposal
    proposed_plan JSONB NOT NULL,      -- full case sequence + reasoning
    user_feedback TEXT,                -- feedback if user requested changes
    final_plan JSONB,                  -- after adjustments
    
    -- State
    status TEXT DEFAULT 'proposed',    -- proposed, active, completed, abandoned
    current_day INTEGER DEFAULT 1,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Metrics
    readiness_start INTEGER,           -- estimated from self-report
    readiness_current INTEGER,
    readiness_target INTEGER DEFAULT 80,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Journey cases (ordered)
CREATE TABLE journey_cases (
    id TEXT PRIMARY KEY,
    journey_id TEXT NOT NULL REFERENCES learning_journeys(id) ON DELETE CASCADE,
    day_number INTEGER NOT NULL,
    case_id TEXT NOT NULL,
    focus_area TEXT,
    learning_objective TEXT,
    estimated_minutes INTEGER DEFAULT 45,
    
    -- State
    status TEXT DEFAULT 'locked',      -- locked, available, in_progress, completed
    session_id TEXT REFERENCES sessions(id),
    score INTEGER,
    completed_at TIMESTAMP,
    
    UNIQUE(journey_id, day_number)
);

-- Reasoning autopsy (post-session analysis)
CREATE TABLE reasoning_autopsies (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    journey_id TEXT REFERENCES learning_journeys(id),
    
    -- Analysis
    user_pathway JSONB,                -- extracted reasoning steps
    expert_pathway JSONB,              -- gold standard
    divergence_points JSONB,           -- where user diverged from expert
    errors_detected JSONB,             -- [{type, severity, description, evidence}]
    pearl TEXT,                        -- actionable insight
    
    -- Impact
    readiness_impact INTEGER DEFAULT 0,  -- +/- points
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Patient series (linked continuity cases)
CREATE TABLE patient_series (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_condition TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    occupation TEXT,
    
    -- Sequence
    case_sequence JSONB NOT NULL,      -- [case_id_1, case_id_2, ...]
    
    -- Triggers
    triggers JSONB NOT NULL,           -- [{type, value, target_case}]
    
    -- Context
    next_visit_context JSONB,          -- {days_later, reason, new_symptoms}
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- User patient history (continuity tracking)
CREATE TABLE user_patient_history (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    series_id TEXT NOT NULL REFERENCES patient_series(id),
    current_visit INTEGER DEFAULT 1,
    last_session_id TEXT REFERENCES sessions(id),
    errors_detected JSONB,
    status TEXT DEFAULT 'active',      -- active, completed, abandoned
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, series_id)
);

-- Indexes
CREATE INDEX idx_journeys_user ON learning_journeys(user_id, status);
CREATE INDEX idx_journey_cases_journey ON journey_cases(journey_id, day_number);
CREATE INDEX idx_autopsies_session ON reasoning_autopsies(session_id);
CREATE INDEX idx_autopsies_journey ON reasoning_autopsies(journey_id);
CREATE INDEX idx_user_patient_history ON user_patient_history(user_id, status);
```

### 5.2 Backend Services (New Modules)

```
backend/app/domains/
├── mentor/                          # NEW: Mentor system
│   ├── __init__.py
│   ├── models.py                    # SQLAlchemy models (journey, autopsy, series)
│   ├── schemas.py                   # Pydantic schemas
│   ├── router.py                    # API endpoints
│   ├── service.py                   # Business logic
│   ├── journey_builder.py           # LLM pipeline: story → context → proposal
│   ├── case_selector.py             # Case selection algorithm
│   ├── autopsy_generator.py         # Reasoning autopsy LLM pipeline
│   ├── continuity_engine.py         # Patient series trigger & resolution
│   └── readiness_calculator.py      # Readiness score computation
```

### 5.3 API Endpoints

```
# Journey Builder
POST   /api/v2/mentor/story                    # Submit user story, get proposal
POST   /api/v2/mentor/journeys/{id}/customize  # Request changes to proposal
POST   /api/v2/mentor/journeys/{id}/accept     # Accept and start journey
POST   /api/v2/mentor/journeys/{id}/abandon    # Abandon journey

# Journey Tracking
GET    /api/v2/mentor/journeys                 # List user's journeys
GET    /api/v2/mentor/journeys/{id}            # Get journey detail + progress
GET    /api/v2/mentor/journeys/{id}/next-case  # Get next available case
POST   /api/v2/mentor/journeys/{id}/complete-case  # Mark case completed

# Reasoning Autopsy
GET    /api/v2/mentor/sessions/{id}/autopsy    # Get autopsy for session
POST   /api/v2/mentor/sessions/{id}/autopsy    # Generate autopsy (post-score)

# Patient Continuity
GET    /api/v2/mentor/continuity/pending       # Check for pending continuity case
GET    /api/v2/mentor/series/{id}              # Get patient series detail

# Readiness
GET    /api/v2/mentor/readiness                # Get current readiness score
GET    /api/v2/mentor/readiness/report         # Get full readiness report
GET    /api/v2/mentor/readiness/history        # Get readiness over time
```

### 5.4 Frontend Architecture

```
sistemnya/
├── qora-mentor.jsx                  # NEW: Mentor system components
│   ├── QMentorChat                  # Story input chat interface
│   ├── QJourneyProposal             # Journey proposal display
│   ├── QJourneyDashboard            # Active journey tracking
│   ├── QAutopsyCard                 # Reasoning autopsy display
│   ├── QContinuityBanner            # Returning patient banner
│   ├── QReadinessReport             # Readiness score report
│   └── QReadinessGauge              # Visual readiness meter
```

**Load order in `bundle-legacy.mjs`:**
```javascript
const LOAD_ORDER = [
  // ... existing
  'qora-v2.jsx',
  'qora-enhancements.jsx',
  'qora-mentor.jsx',        // NEW: after enhancements
];
```

**Integration in `Virtual Patient Simulator.html`:**
- Add "Mentor" to navigation: `['dashboard','Dashboard'],['cases','Cases'],['mentor','Mentor'],['sessions','Sessions'],...`
- Add screen: `screen === 'mentor' && React.createElement(QMentorScreen, { onNav: navigate })`
- Mobile bottom bar: add `['mentor','🎓','Mentor']`

---

## 6. Design System Compliance

### 6.1 Strict Rules

| Rule | Enforcement |
|:-----|:------------|
| **NO design.css changes** | All new UI uses inline styles with existing CSS custom properties |
| **No new CSS files** | All styling via `style={{}}` with `var(--token)` |
| **Existing components reused** | QV2Pill, QV2Stat, QV2SkillBar, QV2Badges, QDStat, etc. |
| **Animation classes** | `.au`, `.af`, `.as`, `.ab`, `.ar`, `.al` for entrances |
| **Border radius** | `var(--r-sm)`, `var(--r-md)`, `var(--r-lg)`, `var(--r-xl)`, `var(--r-2xl)` |
| **Shadows** | `var(--sh-xs)`, `var(--sh-sm)`, `var(--sh-md)`, `var(--sh-lg)`, `var(--sh-xl)` |
| **Colors** | `var(--primary)`, `var(--teal)`, `var(--amber)`, `var(--red)`, `var(--green)`, `var(--violet)`, `var(--gold)` |
| **Typography** | Poppins, sizes 10-38px, weights 400-800 |

### 6.2 New Components (Design-Compliant)

**QMentorChat:**
- Uses same chat bubble style as QV2Session: `borderRadius: 16`, `padding: '10px 14px'`
- User bubble: `background: 'var(--primary)'`, `color: '#fff'`
- Qora bubble: `background: 'var(--surface)'`, `border: '1px solid var(--border)'`
- Input: same style as QV2Session input

**QJourneyProposal:**
- Card style: `background: 'var(--surface)'`, `border: '1px solid var(--border)'`, `borderRadius: 'var(--r-lg)'`, `boxShadow: 'var(--sh-sm)'`
- Locked case: `opacity: 0.6`, `background: 'var(--surface-2)'`
- Available case: normal, with `cursor: 'pointer'`
- Completed case: `border: '1px solid var(--teal)'`, checkmark icon

**QAutopsyCard:**
- Tabs: same style as QV2Assess tabs (border-bottom active indicator)
- Error card: `background: 'var(--red-l)'`, `border: '1px solid var(--red)'`
- Pearl card: `background: 'var(--teal-l)'`, `border: '1px solid var(--teal)'`
- Pathway comparison: two-column layout, `gridTemplateColumns: '1fr 1fr'`

**QContinuityBanner:**
- Background: `var(--violet-l)`
- Border: `1px solid var(--violet)`
- Icon: 🔄 (returning patient)
- Badge: `background: 'var(--violet)'`, `color: '#fff'`, "Visit X of Y"

**QReadinessGauge:**
- Circular progress: SVG with `var(--primary)` stroke
- Score text: `fontSize: 38`, `fontWeight: 800`, `color: 'var(--primary)'`
- Interpretation label: `fontSize: 13`, `color: 'var(--text-2)'`

**QReadinessReport:**
- Same card layout as QV2Result
- Dimension bars: same style as QV2SkillBar
- Disclaimer: `fontSize: 11`, `color: 'var(--text-3)'`, `fontStyle: 'italic'`

---

## 7. Implementation Plan

### 7.1 Phase 1: Foundation (Week 1)

| Day | Task | Deliverable | Effort |
|:----|:-----|:------------|:-------|
| 1 | DB schema + migrations | `learning_journeys`, `journey_cases`, `reasoning_autopsies`, `patient_series`, `user_patient_history` tables | 4h |
| 1 | Backend models + schemas | SQLAlchemy models, Pydantic schemas | 3h |
| 2 | Journey builder LLM pipeline | `journey_builder.py`: story → context → proposal | 6h |
| 2 | Case selector | `case_selector.py`: filter, prioritize, order | 4h |
| 3 | Journey API endpoints | `POST /story`, `POST /customize`, `POST /accept`, `GET /journeys`, `GET /journeys/{id}` | 6h |
| 4 | Frontend: QMentorChat | Story input interface | 4h |
| 4 | Frontend: QJourneyProposal | Proposal display + customize | 4h |
| 5 | Integration + testing | End-to-end journey creation flow | 4h |

### 7.2 Phase 2: Core Features (Week 2)

| Day | Task | Deliverable | Effort |
|:----|:-----|:------------|:-------|
| 6 | Autopsy generator LLM | `autopsy_generator.py`: transcript → pathway → errors → pearl | 6h |
| 6 | Autopsy API | `GET/POST /sessions/{id}/autopsy` | 3h |
| 7 | Frontend: QAutopsyCard | Autopsy display in result screen | 5h |
| 7 | Continuity engine | `continuity_engine.py`: trigger detection, next visit resolution | 5h |
| 8 | Continuity API | `GET /continuity/pending`, series management | 3h |
| 8 | Frontend: QContinuityBanner | Returning patient UI | 3h |
| 9 | Readiness calculator | `readiness_calculator.py`: formula + interpretation | 4h |
| 9 | Readiness API | `GET /readiness`, `GET /readiness/report` | 3h |
| 10 | Frontend: QReadinessReport | Full readiness report UI | 4h |
| 10 | Integration + testing | Complete journey with autopsy + continuity | 4h |

### 7.3 Phase 3: Polish & Ship (Week 3)

| Day | Task | Deliverable | Effort |
|:----|:-----|:------------|:-------|
| 11 | Patient series seed data | 3-5 continuity series (gastritis→GI bleeding, UTI→pyelonephritis, etc.) | 4h |
| 11 | Case file updates | Add `continuity` frontmatter to linked cases | 3h |
| 12 | Journey dashboard polish | Progress tracking, day unlocking, completion states | 4h |
| 12 | Readiness gauge | Visual circular progress | 3h |
| 13 | Mobile responsiveness | All new components mobile-friendly | 4h |
| 13 | i18n translations | EN + ID strings for all new UI | 3h |
| 14 | End-to-end testing | Full user journey from story to readiness report | 4h |
| 14 | Documentation | API docs, user guide, admin guide | 3h |
| 15 | Bug fixes + polish | Address testing findings | 4h |
| 15 | Deploy + monitor | Push to prod, monitor errors | 2h |

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
# tests/test_mentor.py

def test_context_extraction():
    """LLM extracts correct context from user story."""
    story = "Ujian gua 1 minggu lagi, masih bego pediatrik"
    context = extract_context(story)
    assert context["timeline_days"] == 7
    assert "pediatrik" in context["weaknesses"]
    assert context["level"] == "koas"  # default

def test_case_selection():
    """Case selector returns correct number and order."""
    context = {"timeline_days": 7, "level": "koas", "weaknesses": ["paediatrics"]}
    cases = select_cases(context, load_all_cases())
    assert len(cases) == 7
    assert cases[0]["difficulty"] <= cases[-1]["difficulty"]
    assert any(c["specialty"] == "paediatrics" for c in cases)

def test_readiness_calculation():
    """Readiness score computes correctly."""
    sessions = create_test_sessions(5, avg_score=70)
    readiness = calculate_readiness("user_1", sessions=sessions)
    assert 60 <= readiness["score"] <= 80
    assert readiness["confidence"] == "medium"

def test_continuity_trigger():
    """Missed red flag triggers continuity."""
    autopsy = {"errors_detected": [{"type": "missed_red_flag", "severity": "critical", "value": "gi_bleeding"}]}
    result = check_continuity_trigger(autopsy, "im_gastritis_001", "user_1")
    assert result is not None
    assert result["next_case_id"] == "im_gi_bleeding_001"
    assert result["visit_number"] == 2
```

### 8.2 Integration Tests

```python
def test_full_journey_flow():
    """End-to-end: story → proposal → accept → complete → readiness."""
    # 1. Submit story
    resp = client.post("/api/v2/mentor/story", json={"story": "Ujian 1 minggu, pediatrik"})
    assert resp.status_code == 200
    journey_id = resp.json()["data"]["journey_id"]
    
    # 2. Accept journey
    resp = client.post(f"/api/v2/mentor/journeys/{journey_id}/accept")
    assert resp.status_code == 200
    
    # 3. Get next case
    resp = client.get(f"/api/v2/mentor/journeys/{journey_id}/next-case")
    assert resp.status_code == 200
    case = resp.json()["data"]["case"]
    assert case["day"] == 1
    
    # 4. Complete case (simulate session)
    session = create_test_session(case["id"])
    resp = client.post(f"/api/v2/mentor/journeys/{journey_id}/complete-case", 
                       json={"case_id": case["id"], "session_id": session.id, "score": 75})
    assert resp.status_code == 200
    
    # 5. Check readiness updated
    resp = client.get("/api/v2/mentor/readiness")
    assert resp.status_code == 200
    assert resp.json()["data"]["score"] > 0
```

### 8.3 LLM Quality Tests

```python
def test_autopsy_quality():
    """Autopsy generates reasonable output."""
    case = load_case("im_gastritis_001")
    transcript = create_test_transcript(missed_red_flag="gi_bleeding")
    autopsy = generate_autopsy(case, transcript, {}, {}, {})
    
    assert "errors_detected" in autopsy
    assert len(autopsy["errors_detected"]) > 0
    assert any(e["type"] == "missed_red_flag" for e in autopsy["errors_detected"])
    assert autopsy["pearl"] is not None
    assert len(autopsy["pearl"]) > 20
```

---

## 9. Gamification Integration

### 9.1 Mastery Streak (Replaces Daily Streak)

| Current | New |
|:--------|:----|
| Daily streak (open app every day) | Mastery streak (complete journey days) |
| Streak breaks if miss a day | Streak breaks if abandon journey |
| +10 XP per day | +50 XP per journey day completed |
| Badge: "7 day streak" | Badge: "Journey completed" |

**Implementation:**
- `user_profiles.extra` gains `mastery_streak`, `journeys_completed`, `current_journey_id`
- Streak increments on journey day completion, resets on journey abandon
- Bonus XP: +50 per day, +200 bonus for full journey completion

### 9.2 New Badges

| Badge | Criteria | Icon |
|:------|:---------|:-----|
| 🎓 First Journey | Complete first learning journey | 🎓 |
| 🔄 Continuity Master | Complete a patient series (3 visits) | 🔄 |
| 🔬 Reasoning Detective | View 10 reasoning autopsies | 🔬 |
| 💎 Pearl Collector | Collect 20 clinical pearls | 💎 |
| 🎯 Ready or Not | Achieve 80%+ readiness score | 🎯 |
| 🏆 Exam Ready | Complete journey + achieve target readiness | 🏆 |

### 9.3 Level System Integration

- Journey completion: +200 XP
- Autopsy viewed: +10 XP
- Pearl collected: +5 XP
- Continuity visit completed: +75 XP
- Readiness milestone (60%, 80%, 90%): +100 XP each

---

## 10. Privacy & Safety

### 10.1 Data Privacy

| Data | Storage | Retention | Access |
|:-----|:--------|:----------|:-------|
| User story text | `learning_journeys.user_story` | Until journey deleted | User + backend |
| Extracted context | `learning_journeys.extracted_context` | Until journey deleted | Backend only |
| Reasoning autopsy | `reasoning_autopsies` | 90 days | User only |
| Patient history | `user_patient_history` | Until series completed | User + backend |
| Readiness score | Computed on-demand | Not stored | User only |

### 10.2 Disclaimer

**Required on all readiness reports:**
> "Readiness score adalah estimasi berdasarkan rubrik OSCE dan performa latihan. Bukan guarantee kelulusan. Gunakan sebagai panduan, bukan pengganti persiapan resmi. Selalu konsultasikan dengan pembimbing klinis Anda."

**Required on autopsy:**
> "Clinical Reasoning Autopsy adalah analisis AI terhadap pola pikir Anda. Bukan pengganti feedback dari supervisor klinis. Gunakan sebagai bahan refleksi, bukan penilaian mutlak."

---

## 11. Success Metrics

### 11.1 Product Metrics

| Metric | Target | Measurement |
|:-------|:-------|:------------|
| Journey adoption rate | 30% of active users | `journeys_started / active_users_30d` |
| Journey completion rate | 60% | `journeys_completed / journeys_started` |
| Autopsy engagement | 70% view rate | `autopsies_viewed / sessions_completed` |
| Continuity completion | 40% | `series_completed / series_triggered` |
| Readiness improvement | +15% avg | `readiness_final - readiness_start` |
| Session frequency | +25% increase | `sessions_per_user_30d` before vs after |

### 11.2 Business Metrics

| Metric | Target | Measurement |
|:-------|:-------|:------------|
| Premium conversion | +20% | `paid_users / total_users` |
| Retention (30d) | +15% | `active_users_day_30 / new_users` |
| Session duration | +30% | `avg_session_minutes` |
| NPS score | +10 points | Survey |

---

## 12. Risk Analysis

| Risk | Probability | Impact | Mitigation |
|:-----|:------------|:-------|:-----------|
| LLM proposes irrelevant journey | Medium | High | User feedback loop + template fallback |
| Readiness score inaccurate | Medium | High | Disclaimer + confidence interval + collect validation data |
| Continuity confusing | Low | Medium | Clear "story so far" + max 3 visits |
| Autopsy hallucination | Medium | Medium | Evidence-based prompt + quote verification |
| Over-engineering | Medium | High | Keep free mode, journey as optional |
| User abandons journey | High | Medium | Reminder system + pause/resume + shorter journeys |

---

## 13. Future Enhancements (Post-MVP)

| Feature | Description | Priority |
|:--------|:------------|:---------|
| **Peer Benchmark** | Compare readiness vs anonymized cohort | P2 |
| **Faculty Dashboard** | Dosen assign journeys, monitor progress | P2 |
| **Voice Mentor** | TTS for Qora responses | P3 |
| **Adaptive Difficulty** | Real-time adjustment based on performance | P3 |
| **Mock Exam Mode** | Full OSCE simulation with multiple stations | P2 |
| **Integration with PNPK** | Link cases to official guidelines | P2 |

---

## 14. Appendix

### 14.1 Example Patient Series

**Series 1: Ibu Siti (Gastritis → GI Bleeding)**
```yaml
series_id: siti_gastritis_series
name: Ibu Siti
base_condition: gastritis
age: 45
gender: female
occupation: Ibu rumah tangga

case_sequence:
  - im_gastritis_001          # Visit 1: epigastric pain
  - im_gi_bleeding_001        # Visit 2: melena (triggered by missed red flag)
  - im_gastritis_fu_001       # Visit 3: post-endoscopy follow-up

triggers:
  - type: missed_red_flag
    value: gi_bleeding
    target_case: im_gi_bleeding_001
    description: "User missed 'tinja hitam' in Visit 1"

next_visit_context:
  days_later: 3
  reason: "Obat habis, gejala tidak membaik, BAB hitam"
  new_symptoms: ["melena", "fatigue", "dizziness"]
```

**Series 2: Pak Budi (UTI → Pyelonephritis)**
```yaml
series_id: budi_uti_series
name: Pak Budi
base_condition: urinary_tract_infection
age: 52
gender: male
occupation: Supir

case_sequence:
  - im_uti_001                # Visit 1: dysuria
  - im_pyelonephritis_001     # Visit 2: fever, flank pain (triggered by missed fever)
  - im_uti_fu_001             # Visit 3: post-antibiotic follow-up

triggers:
  - type: missed_red_flag
    value: fever
    target_case: im_pyelonephritis_001
```

### 14.2 LLM Prompt Library

**Journey Builder System Prompt:**
```
You are Qora Mentor, a supportive medical education advisor for Indonesian medical students.
Your role is to listen to the student's concerns, understand their exam goals, and propose a personalized learning journey.

Rules:
1. Be empathetic but professional — the student may be anxious
2. Ask clarifying questions if the story is vague
3. Propose a realistic, structured plan (not too ambitious)
4. Explain your reasoning — the student should understand WHY this plan helps
5. Use Indonesian medical education context (UKNPDPD, koas, stase, etc.)
6. Be encouraging — the goal is confidence, not just competence
```

**Autopsy System Prompt:**
```
You are a senior clinical examiner performing a "reasoning autopsy" — analyzing not just WHAT the student asked, but HOW they thought.

Your analysis should be:
1. Evidence-based — quote the transcript verbatim
2. Specific — identify exact moments of divergence
3. Constructive — focus on learning, not criticism
4. Actionable — provide a "clinical pearl" the student can apply

Error taxonomy:
- anchoring: fixating on initial hypothesis
- premature_closure: stopping data gathering too early
- confirmation_bias: only asking confirming questions
- scattergun: ordering too many tests without hypothesis
- missed_red_flag: failing to screen critical red flag
- poor_signposting: disorganized interview flow
- leading_questions: suggesting answers
- ignoring_ice: not exploring ideas/concerns/expectations
```

### 14.3 File Structure

```
backend/
├── app/
│   ├── domains/
│   │   ├── mentor/                    # NEW
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── journey_builder.py
│   │   │   ├── case_selector.py
│   │   │   ├── autopsy_generator.py
│   │   │   ├── continuity_engine.py
│   │   │   └── readiness_calculator.py
│   │   └── ...
│   └── rag/
│       └── prompt_v2.py               # MODIFIED: continuity context injection
├── alembic/
│   └── versions/
│       └── xxxx_add_mentor_system.py  # NEW
└── tests/
    └── test_mentor.py                 # NEW

sistemnya/
├── qora-mentor.jsx                    # NEW
├── qora-v2.jsx                        # MODIFIED: integrate autopsy in result
├── Virtual Patient Simulator.html     # MODIFIED: add mentor screen + nav
└── build/
    └── bundle-legacy.mjs              # MODIFIED: add qora-mentor.jsx to LOAD_ORDER
```

---

## 15. Sign-off

| Role | Name | Date | Signature |
|:-----|:-----|:-----|:----------|
| Product Owner | Arran | Aug 16, 2026 | ✅ (via Discord) |
| Tech Lead | Ker | Aug 16, 2026 | ✅ |
| Design Review | — | | |
| QA | Ker (E2E browser + API) | Aug 16, 2026 | ✅ |

---

**END OF PRD**
