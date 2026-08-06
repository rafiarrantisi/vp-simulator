# Qora — Investor Information Memorandum

> **Company:** PT Qora Cendekia Medika
> **Product:** Qora — AI-powered clinical interview trainer
> **Stage:** MVP complete, pre-revenue, launching
> **Document version:** v1.0 — July 2026
> **Prepared for:** Angel investors, seed funds, strategic partners

---

## 1. Executive Summary

**Qora is an AI-powered clinical interview trainer that lets medical students practise patient consultations against realistic virtual patients, then receive instant, exam-grade scoring and a full model-answer reveal.**

Qora solves a global problem: medical students don't get enough supervised practice. Real patients are scarce, supervisors have limited time, and existing exam-prep tools (UWorld, AMBOSS) cost $79–99/month — unaffordable for students in emerging markets. Qora delivers unlimited, realistic, standardised practice at a fraction of the cost, with a differentiated AI assessment engine calibrated to real OSCE examiner standards.

**The ask:** $100K–$200K seed round for marketing (Meta Ads), product development (mobile app), and operations.

---

## 2. The Problem

### 2.1 Students cannot practise enough
- Clinical history-taking is the #1 skill in medicine, yet students get limited reps: real patients are scarce, ward time is shrinking, and supervisors are overworked.
- In Indonesia and ASEAN, cohorts of 200+ students compete for the same few clinical opportunities.
- IMG candidates (USMLE Step 2 CS, PLAB, AMC) face the same problem with even higher stakes — a single failed attempt can cost months and thousands of dollars.

### 2.2 Feedback is slow and inconsistent
- Traditional supervision gives feedback days or weeks after the encounter.
- Every supervisor scores differently — students cannot calibrate to an objective standard.
- OSCE (Objective Structured Clinical Examination) is the global standard for assessing clinical competence, and preparation is expensive and logistically heavy.

### 2.3 Existing tools are overpriced and static
| Tool | Price | Gap |
|---|---|---|
| UWorld | $79–99/mo | Expensive; question-bank, not conversational practice |
| AMBOSS | $99/mo | Clinical decision support; not simulation-based |
| Geeky Medics | £10/mo | UK-centric, English-only, static cases |
| Mock OSCE services | $50–100/session | Expensive per session, not scalable |

None combine: **conversational AI patients + objective exam-grade scoring + multilingual support + emerging-market pricing.**

---

## 3. The Solution

### 3.1 What Qora does
Students interview an **AI patient** that behaves like a real lay patient — it only answers what is asked, never volunteers the full story. The student must actively elicit the history, list differentials, order investigations, and propose management. Then an **AI examiner** scores the performance against a hidden checklist with transparent per-item hit/miss evidence, and reveals the complete model answer.

### 3.2 Product pillars
1. **Answer-restrained AI patients** — pedagogically superior: students learn to elicit, not receive (validated leak-prevention architecture).
2. **Exam-grade assessment** — 9 scoring dimensions calibrated to real OSCE examiner standards, with borderline regression calibration (60 = pass, 75 = clear pass, 85+ = excellent), per-item evidence, and constructive supervisor-style feedback.
3. **Multilingual** — English, Bahasa Indonesia, Malay, Tagalog, Vietnamese, Thai (6 languages) — patients respond and judges assess in the student's language.
4. **Region-aware pricing** — PPP-adjusted for emerging markets (see §7).
5. **Comprehensive clinical content** — 82+ cases across 10 specialties, 3 difficulty levels; 500+ investigation options; 250+ therapy options.

### 3.3 How it works (3 steps)
```
1. Interview   → Ask questions in free text or voice; the AI patient answers only what you ask
2. Assess      → List differentials, order investigations, propose management
3. Learn       → Instant per-item scoring + full answer-key reveal + supervisor-style feedback
```

---

## 4. Market Opportunity

### 4.1 Target segments
| Segment | Size | Willingness to pay |
|---|---|---|
| Medical students (Indonesia) | ~70,000 active | High (exam-critical) |
| Medical students (ASEAN) | ~200,000 | High |
| Medical students (global) | ~1.5M | High |
| IMG exam candidates | ~500K/year globally | Very high (licensing stakes) |
| Residents (PPDS) | ~50K Indonesia | Medium-high |

### 4.2 Market size
- **Global medical education software market:** ~$2.5B (2024), growing ~10% CAGR
- **Medical simulation market:** ~$1.8B (2024), ~12% CAGR
- **Qora's serviceable market (APAC + IMG):** conservatively $500M+

### 4.3 Moats
1. **Assessment IP** — the calibrated judge (9 dimensions, borderline calibration, evidence-based scoring) is a proprietary engineered system, not a generic chatbot wrapper.
2. **Content moat** — 82+ structured cases with hidden scoring checklists (Part A) separated from patient personas (Part B) — a validated schema that scales.
3. **Multilingual first-mover** — no competitor serves ASEAN medical students in their own language with AI simulation.
4. **PPP pricing** — hard for US-centric incumbents to replicate profitably.

---

## 5. Product Status & Traction

### 5.1 Current state (July 2026)
- ✅ **MVP complete** — landing, auth, 82 cases, streaming chat, voice input, full assessment, answer key, gamification, i18n, region-aware pricing
- ✅ **Backend live** on VPS (FastAPI + Supabase PostgreSQL + OpenRouter LLM), auto-restart via systemd
- ✅ **Frontend live** at vp-simulator.vercel.app (Vercel, auto-deploy from GitHub)
- ✅ **Multilingual AI** (EN/ID/MS/TL/VI/TH) — patient + judge
- ✅ **Assessment system v2** — 9 dimensions, borderline calibration, per-item evidence
- ✅ **Billing infrastructure** — Midtrans (Indonesia, IDR) planned first; Xendit (international, USD) as secondary gateway
- ✅ **Legal entity** — PT Qora Cendekia Medika registered (NIB issued)
- ⏳ **Payments live** — Midtrans onboarding in progress
- ⏳ **Domain** — qora.ai purchase in progress
- ⏳ **Revenue** — first paying customers pending payment gateway activation

### 5.2 Metrics so far
- 82 cases across 10 specialties (internal medicine, surgery, paediatrics, OB-GYN, psychiatry, neurology, ENT, dermatology, ophthalmology, emergency)
- 3 difficulty levels (pre-clinical, clerkship, advanced)
- 500+ investigation items, 250+ therapy items in clinical catalogues
- 6 languages supported
- Full i18n (100+ UI strings, EN/ID)
- Assessment: 9 dimensions, per-item evidence, answer-key reveal

---

## 6. Technology & Architecture

| Layer | Stack | Status |
|---|---|---|
| Frontend | React 18 + Vite, Vercel hosting | LIVE |
| Backend | FastAPI (Python 3.11), VPS (Alibaba Cloud) | LIVE |
| Database | Supabase PostgreSQL (RLS enabled) | LIVE |
| LLM | OpenRouter (DeepSeek v4 Flash) — patient + judge | LIVE |
| Payments | Midtrans (IDR, Indonesia) + Xendit (USD, intl) | Integration in progress |
| Auth | JWT (access + refresh, silent refresh) | LIVE |
| Voice | Browser Web Speech API (multilingual) | LIVE |

### 6.1 Key technical differentiators
- **Structural leakage prevention (P1 guarantee):** patient persona (Part B) and scoring truth (Part A) are architecturally separated — the patient model literally cannot see the answer key.
- **Server-side scoring recomputation:** the LLM never sets its own total; the server recomputes from per-dimension scores (anti-hallucination arithmetic).
- **Cost-optimised LLM:** DeepSeek Flash keeps marginal cost ~$0.05–0.10/session → >90% gross margin.
- **Security:** RLS on all Supabase tables, rate limiting, CORS whitelist, JWT rotation.

---

## 7. Business Model

### 7.1 Pricing (PPP-adjusted, region-aware)
| Region | Monthly | Annual | Rationale |
|---|---|---|---|
| Indonesia | Rp119.000 (~$7.50) | Rp999.000 | Affordable for Indonesian students |
| ASEAN | $9.99 | $84 | Mid-tier purchasing power |
| Rest of World | $14.99 | $119 | Still 80% cheaper than UWorld |

### 7.2 Revenue model
- **Freemium:** 3 free sessions/month (no card) → paid conversion
- **Monthly subscription:** unlimited practice
- **Annual subscription:** best value (~34% discount)
- **Exam pass:** one-time 1-month unlimited (exam-season spike)
- **Future:** B2B institutional licenses (medical schools), bulk residency packages

### 7.3 Unit economics (estimates)
| Metric | Value |
|---|---|
| LLM cost per session | ~$0.05–0.10 |
| Gross margin | ~90%+ |
| Target CAC | <$20 (Meta Ads) |
| Target LTV | $150+ (10-month avg retention) |
| LTV:CAC target | >7:1 |

---

## 8. Competitive Landscape

| Competitor | Price | Model | AI conversation | Multilingual | Emerging-market pricing |
|---|---|---|---|---|---|
| UWorld | $79–99/mo | Q-bank | ✗ | ✗ | ✗ |
| AMBOSS | $99/mo | Decision support | ✗ | ✗ | ✗ |
| Osmosis | $15/mo | Video learning | ✗ | ✗ | ✗ |
| Geeky Medics | £10/mo | Static cases | ✗ | ✗ | ✗ |
| **Qora** | **$7.50–14.99/mo** | **AI simulation** | **✅** | **✅ (6 languages)** | **✅** |

**Qora's positioning:** the only AI-simulation trainer with exam-grade assessment, multilingual support, and PPP pricing for emerging markets.

---

## 9. Financials

### 9.1 Current monthly burn (pre-launch)
| Item | Cost |
|---|---|
| VPS hosting | ~$30–50 |
| LLM API (dev) | ~$100–200 |
| Domain + email | ~$5 |
| Vercel + Supabase | $0 (free tiers) |
| **Total** | **~$150–250/month** |

### 9.2 Projected revenue (conservative)
| Phase | Users | MRR | Annual |
|---|---|---|---|
| Months 1–3 | 50 | ~Rp6M (~$400) | — |
| Months 4–6 | 200 | ~Rp24M (~$1.6K) | — |
| Months 7–12 | 500 | ~Rp60M (~$4K) | ~Rp400–500M (~$25–30K) |
| Year 2 | 2,000 | ~Rp240M (~$16K) | ~Rp2.9B (~$180K) |

---

## 10. The Ask

### 10.1 Funding request: $100K–$200K seed
| Allocation | % |
|---|---|
| Marketing (Meta Ads, content, growth) | 40% |
| Product development (mobile app, features) | 30% |
| Operations (hiring, infrastructure) | 20% |
| Buffer | 10% |

### 10.2 Use of funds — what $150K buys
1. **12 months runway** at $8–10K/month burn
2. **Meta Ads engine** — $2–3K/month testing → validate CAC/LTV at scale
3. **Mobile app (React Native)** — capture mobile-first ASEAN market
4. **Content expansion** — 82 → 250+ cases (faster authoring pipeline)
5. **B2B motion** — pitch 3–5 medical schools for institutional licenses
6. **Key hire** — growth marketer / community manager

### 10.3 Milestones funded
| Milestone | Target |
|---|---|
| First 100 paying users | Month 3 |
| $5K MRR | Month 6 |
| 2,000 active users | Month 12 |
| Institutional pilot | Month 9 |

---

## 11. Valuation & Structure

| Item | Detail |
|---|---|
| **Pre-money valuation (pre-revenue)** | $500K–$1.5M |
| **Post-revenue valuation** (100+ paying users) | $3–5M (5–10x revenue) |
| **Equity offered** | 10–15% for seed |
| **Instrument preference** | Convertible note (20% discount) or priced round |
| **Existing cap table** | Founders 100% |

**Valuation rationale (pre-revenue):**
| Component | Value |
|---|---|
| Codebase (full-stack, AI, 500+ hrs dev) | ~$200K |
| Content IP (82 cases, assessment schema) | ~$100K |
| Legal entity (PT registered, NIB) | ~$50K |
| Market positioning (healthtech + edtech + AI) | ~$300K |
| Founding team (CEO + CTO) | ~$300K |
| **Total** | **~$950K** |

---

## 12. Team

### Founders
- **Arran — CEO.** Business strategy, operations, partnerships, fundraising. Driving company formation (PT Qora Cendekia Medika, NIB issued) and payment infrastructure (Midtrans/Xendit onboarding).
- **Ker — Co-founder, CTO.** Full-stack engineering, AI systems design, product architecture. Built the entire platform: AI patient engine, assessment system, multilingual support, billing infrastructure, i18n.

### Advisors / planned hires
- **Medical advisor** (planned) — content validation, clinical accuracy
- **Growth marketer** (planned, funded) — Meta Ads, SEO, community
- **Customer success** (planned) — onboarding, retention

---

## 13. Roadmap

### Phase 1 — Launch (Q3 2026)
- [ ] Midtrans live (Indonesia payments)
- [ ] Xendit live (international payments)
- [ ] Domain qora.ai + email (info@qora.ai)
- [ ] Meta Ads campaign
- [ ] First 100 paying users

### Phase 2 — Growth (Q4 2026)
- [ ] 500+ paying users
- [ ] 200+ cases (expand specialties)
- [ ] Mobile app (React Native)
- [ ] Leaderboard & social features
- [ ] B2B institutional licenses

### Phase 3 — Scale (2027)
- [ ] Series A ($500K–1M)
- [ ] 5,000+ paying users
- [ ] LatAm / Middle East expansion
- [ ] Advanced analytics dashboard
- [ ] Enterprise/B2B partnerships

---

## 14. Risks & Mitigation

| Risk | Mitigation |
|---|---|
| LLM API downtime | Multi-provider fallback (OpenRouter → direct OpenAI/Anthropic) |
| Low conversion from free→paid | A/B testing pricing, onboarding optimization, exam-season pushes |
| High churn | Gamification (streaks, badges, XP), monthly new cases, goal tracking |
| Content accuracy | Medical advisor validation, source_refs in every case, review workflow |
| Payment gateway issues | Dual gateway (Midtrans + Xendit), webhook monitoring |
| Competitor price war | PPP pricing moat, multilingual differentiation, institutional bundling |

---

## 15. KPIs We Report Monthly

- MRR & ARPU (by region)
- Active users (MAU/WAU)
- Free→paid conversion rate
- Churn rate & retention cohorts
- Sessions per user per month
- Average assessment score improvement over time
- CAC & LTV:CAC by channel
- NPS & app store ratings

---

## 16. Contact

- **Company:** PT Qora Cendekia Medika
- **Email:** info@qora.ai (pending activation)
- **WhatsApp:** +62 821-2493-3053
- **Platform:** vp-simulator.vercel.app (temporary; qora.ai pending)
- **Repository:** github.com/rafiarrantisi/vp-simulator (private)

---

*This memorandum contains forward-looking estimates. Figures marked as estimates are based on current market research and internal modelling, not audited financials. Qora is a study aid, not a medical device — it complements, never replaces, real clinical training.*

*Last updated: July 2026*
