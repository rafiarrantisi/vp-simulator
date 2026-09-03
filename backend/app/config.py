"""Settings — pydantic-settings, .env driven (backend-plan §6.1)."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    product_name: str = "Qora"  # rebrand single source (§3); override via PRODUCT_NAME
    app_name: str = "Qora Backend"
    env: str = "dev"  # dev | staging | prod

    # DB: sqlite untuk dev (runnable tanpa Docker); Postgres via env utk prod.
    # Kontrak §7: prod = PostgreSQL. Ini hanya kenyamanan dev.
    database_url: str = "sqlite:///./ophtha_dev.db"

    # Auth (custom JWT, kontrak §6 / backend-plan §8.1)
    jwt_secret: str = "dev-only-change-me"  # WAJIB di-override via env di prod
    jwt_alg: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Google Sign-In (pivot-v4 §7.1). Empty -> Google auth disabled (the UI
    # keeps the button hidden/off). Set to the Google OAuth Web Client ID.
    google_client_id: str = ""

    # Multi-tenant (kontrak §9 K3 — institution_id sejak hari 1)
    default_institution_id: str = "default"

    # RAG infra (Fase 3 — opsional saat skeleton Fase 2)
    qdrant_url: str = "http://localhost:6333"
    embed_model: str = "intfloat/multilingual-e5-large"

    # LLM provider (kontrak §9 K2). Default OpenRouter (OpenAI-compatible,
    # banyak model via 'vendor/model'). Kosongkan key → StubLlmClient.
    llm_provider: str = "openrouter"  # openrouter | openai | anthropic | ""
    llm_api_key: str = ""
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "anthropic/claude-3.5-sonnet"  # persona (kuat) — sesuaikan
    llm_judge_model: str = "openai/gpt-4o-mini"      # judge (murah, rag-plan §9.1)
    llm_author_model: str = ""  # case authoring (pivot-v4 §5.3); empty -> falls back to llm_model. Set a stronger reasoning model when the account supports it.
    # OpenRouter opsional (atribusi; aman dikosongkan)
    llm_site_url: str = ""
    llm_app_title: str = "Qora"
    # Tier A v0.13.0: cap balasan utk persona (cegah essay panjang →
    # kurangi tail latency). 220 ≈ 3-4 kalimat ID, cukup utk balasan
    # pasien answer-restrained. Judge butuh lebih utk JSON struktural.
    # NOTE: deepseek-v4-flash emits ~90-250 reasoning tokens before content
    # (measured Aug 2026: 94 reasoning tokens for a trivial task). 220
    # truncates patient replies (reasoning eats the budget -> empty/"...."
    # responses). 1024 keeps reasoning + full content safe.
    llm_persona_max_tokens: int = 1024
    # Judge JSON is large (per_item × all dimensions + feedback). Reasoning is
    # DISABLED for OpenRouter (llm.py) so this budget is pure content — 8000
    # covers the biggest OSCE cases without truncation.
    llm_judge_max_tokens: int = 8000

    # ── Voice (Fase 4) ──
    # STT: OpenAI-compatible /audio/transcriptions. Default reuse OpenRouter
    # base+key (kosong → fallback ke llm_*). CAVEAT: OpenRouter mungkin tak
    # dukung audio → set STT_BASE_URL ke endpoint Whisper lain (mis. Groq).
    stt_base_url: str = ""   # kosong → pakai llm_base_url
    stt_api_key: str = ""    # kosong → pakai llm_api_key
    stt_model: str = "openai/whisper-large-v3-turbo"
    stt_language: str = "id"
    # TTS: ElevenLabs (env-driven; nonaktif sampai TTS_API_KEY diisi)
    tts_provider: str = "elevenlabs"
    tts_api_key: str = ""
    tts_base_url: str = "https://api.elevenlabs.io"
    tts_voice_id: str = "EXAVITQu4vr4xnSDxMaL"  # ElevenLabs "Sarah" (multibahasa)
    tts_model: str = "eleven_multilingual_v2"

    # ── Rate limiting (in-memory; Redis-backed = scale, ditunda) ──
    rate_limit_enabled: bool = True

    # ── Case content engine (Phase B feature flag, §K) ──
    # v2 (default) keeps the legacy 92-case catalogue & engine.
    # v3_compat makes /api/v2/cases return V3 family cards and dispatches
    # v3 families into the V3 runtime — while QoraV2Screen stays untouched.
    case_content_engine: str = "v2"  # v2 | v3_compat
    # Emails (comma-separated) that see v3_compat even when the global flag is v2
    # (handy for canary/testing without a full rollout).
    v3_compat_test_emails: str = ""
    rate_limit_auth: int = 20      # /api/auth/* per IP per menit
    rate_limit_ai: int = 30        # /api/ai|scoring per user per menit
    rate_limit_window_sec: int = 60

    # ── Developer Dashboard (v0.15.0) ──
    # Akun admin = 1 super-admin hardcoded di .env (keputusan kontrak v0.15.0
    # K9). Saat startup, lifespan() seed user ini dgn role='admin' bila belum
    # ada. Idempoten — kalau user ada tapi role!=admin, JANGAN auto-promote
    # (safety: cegah privilege escalation tak sengaja).
    # Hash bcrypt: generate via `python -m scripts.hash_admin_password`.
    admin_email: str = ""
    admin_password_hash: str = ""
    # Upload dir utk eye photos (& kelak konten admin lain). Prod default
    # `/opt/ophtha/uploads`; dev override ke `./uploads` lewat .env.
    upload_dir: str = "./uploads"

    # ── Billing / entitlements (Midtrans primary + Xendit fallback) ──
    # Enforcement is OFF by default so the live product is unchanged until cutover.
    billing_enforced: bool = False
    free_session_limit: int = 5     # sessions per rolling 30 days for free users
    free_case_limit: int = 3        # distinct cases a free user may open
    price_monthly_usd: float = 9.99
    price_annual_usd: float = 59.0
    price_exam_pass_usd: float = 14.99
    # Cost guardrail (margin protection, §7.3): blended est. $/1k tokens + alert ratio.
    cost_per_1k_tokens_usd: float = 0.001
    cost_alert_ratio: float = 0.8   # warn if a user's 30-day spend > ratio * plan price
    # Midtrans is the Indonesia-primary gateway; Xendit is the fallback for
    # hosted invoices/international regions. Billing remains beta-open until
    # billing_enforced is intentionally enabled.

    # ── Xendit payment gateway (instruksi §8) — env-driven; empty key -> disabled.
    # Xendit hosts the checkout (an invoice URL) so we never touch card data.
    xendit_api_key: str = ""          # secret key (server-side only)
    xendit_webhook_token: str = ""    # x-callback-token verification value
    xendit_currency: str = "USD"      # invoice currency (e.g. USD or IDR)
    xendit_success_url: str = ""      # redirect after a successful payment
    xendit_failure_url: str = ""      # redirect after a failed/expired payment

    # ── Midtrans payment gateway (Indonesia primary) — Snap API.
    # Snap hosts the payment page (QRIS/VA/e-wallet/card) via a popup token.
    # Entitlement granted ONLY from the verified webhook (SHA512 signature).
    midtrans_server_key: str = ""     # server key (server-side only)
    midtrans_client_key: str = ""     # client key (safe for frontend Snap.js)
    midtrans_is_production: bool = False  # False -> sandbox endpoint
    midtrans_success_url: str = ""    # optional redirect after payment
    midtrans_failure_url: str = ""    # optional redirect after failure

    # ── Region-aware pricing (Phase 1 — international rollout) ──
    # Indonesia — IDR
    price_monthly_idr: float = 119000
    price_annual_idr: float = 999000
    # ASEAN (MY, TH, VN, PH, SG) — USD
    price_monthly_asean: float = 9.99
    price_annual_asean: float = 84.0
    # Rest of World — USD
    price_monthly_row: float = 14.99
    price_annual_row: float = 119.0
    # Exam pass (one region for now)
    price_exam_pass_usd: float = 14.99

    # ── Email (transactional; pivot-v4 §7.1). Empty SMTP_HOST -> console mode:
    # the message (e.g. a verification/reset link) is logged to the server
    # console so flows work locally. Plug a provider (SMTP/Resend/SES) later. ──
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "no-reply@qora.app"

    def stt_base(self) -> str:
        return self.stt_base_url or self.llm_base_url

    def stt_key(self) -> str:
        return self.stt_api_key or self.llm_api_key

    def is_prod(self) -> bool:
        return self.env.lower() in ("prod", "production", "staging")

    def production_issues(self) -> list[str]:
        """Konfigurasi tak-aman utk lingkungan prod/staging."""
        issues: list[str] = []
        weak = {"", "dev-only-change-me", "change-me", "secret"}
        if self.jwt_secret in weak or len(self.jwt_secret) < 32:
            issues.append("JWT_SECRET lemah/default (wajib acak >=32 byte)")
        if self.database_url.startswith("sqlite"):
            issues.append("DATABASE_URL sqlite (wajib PostgreSQL di prod)")
        if "*" in self.cors_origins:
            issues.append("CORS_ORIGINS wildcard '*' (wajib origin spesifik)")
        if not self.llm_api_key:
            issues.append("LLM_API_KEY kosong")
        return issues

    def assert_production_safe(self) -> None:
        """Fail-fast: prod/staging tolak start bila tak aman; dev → warn."""
        issues = self.production_issues()
        if not issues:
            return
        msg = "Konfigurasi tak aman: " + "; ".join(issues)
        if self.is_prod():
            raise RuntimeError(f"[PROD GUARD] {msg}")
        import warnings
        warnings.warn(f"[DEV] {msg} — wajib diperbaiki sebelum prod.", stacklevel=2)

    # Korpus kasus markdown (sumber kebenaran kanonik, kontrak §5.6)
    cases_dir: str = str(_REPO_ROOT / "data-kasus")
    # Schema-v2 cases (pivot-v4 §5.1) — English, multi-specialty
    content_cases_dir: str = str(_REPO_ROOT / "content" / "cases")
    # Schema-v3 canonical case system (STEP 2) — families + variants
    content_v3_dir: str = str(_REPO_ROOT / "content" / "v3")


@lru_cache
def get_settings() -> Settings:
    return Settings()
