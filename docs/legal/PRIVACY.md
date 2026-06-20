# Privacy Policy — Qora (DRAFT)

> Drafting starting point for `BUILD_PLAN_pivot_v4.md` §11/§13. Not legal advice —
> have it reviewed and fill the `{{...}}` placeholders before publishing.
> Last updated: {{DATE}} · Contact: {{SUPPORT_EMAIL}}

Qora is an educational study aid. We practise **data minimisation** —
we collect only what is needed to run the service.

## What we collect
- **Account:** email address, password (stored only as a salted hash), and optional
  profile fields you choose to add (display name, school, year).
- **Usage:** practice sessions you run — including the **transcripts** of your
  simulated interviews — plus scores, XP/streak/gamification, and aggregate usage
  counters used for plan limits.
- **Cost/operational:** per-session token-usage estimates (for service health and
  margin monitoring); standard request logs and error reports.

We do **not** ask for, and you must **not** enter, real patients' identifiable
health information. All AI patients are fictional.

## What we do NOT collect
- **Payment card details.** Checkout and billing are handled by our
  **Merchant of Record, Lemon Squeezy**, which is the seller of record and
  processes payments. We receive only subscription status and a customer/order id —
  never your card number.

## How we use it
- To provide the service (run sessions, score them, show your model-answer reveal).
- To enforce plan limits and protect against abuse/runaway cost.
- To improve case quality and the product (in aggregate; case reports you submit).
- We do **not** sell your personal data.

## Sub-processors
- **LLM provider** (e.g. via OpenRouter): your interview text is sent to the model
  to generate the patient's replies and scoring. Do not include real personal data.
- **Lemon Squeezy** (payments/MoR). **Email** provider for verification/receipts.
- Hosting/infrastructure provider.

## Retention & your rights
- You can request access to, export of, or deletion of your account and associated
  data by contacting {{SUPPORT_EMAIL}}. Deleting your account removes your profile
  and session history (subject to limited legal/operational retention).
- We keep data only as long as needed for the service or as required by law.

## Security
Passwords are hashed (bcrypt); transport is HTTPS; access tokens are short-lived.
No method is perfectly secure, but we apply reasonable safeguards.

## International users & changes
The service is offered globally; by using it you consent to processing as described.
We will post material changes here and update the date above.
