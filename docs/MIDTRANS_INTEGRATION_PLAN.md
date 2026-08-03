# Qora — Integrasi Payment Gateway: Midtrans (Plan)

> **Status:** Plan — menunggu approval & execution
> **Konteks:** Qora akan mulai dari **Midtrans** sebagai payment gateway utama (pasar Indonesia), dengan Xendit sebagai opsi lanjutan untuk pasar internasional.
> **Channel:** #bisnispasien

---

## 1. Kenapa Midtrans Dulu?

| Alasan | Detail |
|---|---|
| **Metode pembayaran lokal terlengkap** | QRIS, GoPay, OVO, DANA, Virtual Account (BCA/Mandiri/BRI/BNI), Alfamart/Indomaret, Credit Card |
| **Proses onboarding cepat** | NIB udah ada → registrasi Midtrans bisa langsung |
| **Snap UI siap pakai** | Popup pembayaran yang gak perlu bikin UI sendiri |
| **Recurring support** | Langganan bulanan/tahunan bisa otomatis |
| **Xendit untuk internasional** | ASEAN/ROW tetap USD via Xendit nanti — dual gateway |

---

## 2. Arsitektur

```
┌────────────────────────────────────────────────────┐
│  Frontend (Vercel / qora.ai)                        │
│  - Pricing page → klik "Upgrade"                    │
│  - Panggil POST /api/billing/midtrans/checkout      │
│  - Dapet snap_token → buka Snap Popup (Midtrans.js) │
└──────────────────────┬─────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────┐
│  Backend (VPS FastAPI)                              │
│  - POST /checkout → buat Snap Transaction (Midtrans)│
│  - Simpan order reference (user_id, plan, amount)   │
│  - POST /notifications ← webhook Midtrans           │
│  - Verifikasi signature → grant entitlement         │
└──────────────────────┬─────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────┐
│  Midtrans (snap.midtrans.com)                       │
│  - Hosted payment page (QRIS, VA, e-wallet, card)   │
│  - Kirim webhook notification status                │
└────────────────────────────────────────────────────┘
```

---

## 3. Alur Pembayaran (Flow)

1. **User klik Upgrade** di pricing/billing page
2. Frontend panggil `POST /api/billing/midtrans/checkout/{plan}`
3. Backend buat **Snap Transaction** via Midtrans API (dengan `customer_details`, `item_details`, `custom_field1=user_id`)
4. Backend balikin `snap_token` + `redirect_url`
5. Frontend buka Snap Popup (`window.snap.pay(token)`)
6. User bayar (QRIS / VA / e-wallet / card)
7. Midtrans kirim **webhook notification** ke `POST /api/billing/midtrans/notifications`
8. Backend verifikasi signature + status `settlement`/`capture`
9. Backend update `entitlements` → user dapet akses unlimited
10. Frontend redirect ke `/billing/success` (atau `/billing/failed`)

---

## 4. Endpoint Backend

### 4.1 `POST /api/billing/midtrans/checkout/{plan}`
**Auth:** Bearer token (user login)

**Request params:**
- `plan`: `monthly` | `annual` | `exam_pass`

**Logic:**
```python
# 1. Ambil harga sesuai region user (IDR untuk indo)
amount = region_price(s, region, plan)   # Rp119.000 / Rp999.000 / dst
# 2. Buat unique order_id: qora-{user_id}-{plan}-{uuid[:8]}
order_id = f"qora-{user.id}-{plan}-{uuid4().hex[:8]}"
# 3. Panggil Midtrans Snap API (POST /v1/charge atau /snap/v1/transactions)
payload = {
    "transaction_details": {
        "order_id": order_id,
        "gross_amount": amount,
    },
    "item_details": [{
        "id": plan,
        "price": amount,
        "quantity": 1,
        "name": f"Qora {plan} plan",
    }],
    "customer_details": {
        "first_name": user.full_name or "Qora",
        "email": user.email,
    },
    "custom_field1": user.id,   # untuk reconciliation webhook
    "custom_field2": plan,
    "expiry": {"unit": "hours", "duration": 24},
}
# 4. Return { snap_token, redirect_url }
```

**Response:**
```json
{
  "success": true,
  "data": {
    "snap_token": "SNAP-TOKEN-...",
    "redirect_url": "https://app.midtrans.com/snap/v2/vtweb/...",
    "order_id": "qora-xxx-xxx-xxxxxxxx"
  }
}
```

### 4.2 `POST /api/billing/midtrans/notifications`
**No auth** (webhook — verifikasi signature sendiri)

**Verifikasi:**
1. Ambil `signature_key` dari body: `SHA512(order_id + status_code + gross_amount + server_key)`
2. Bandingkan dengan header/body `signature_key` dari Midtrans
3. Valid → proses; invalid → 401

**Status mapping:**
| Midtrans status | Aksi |
|---|---|
| `settlement` / `capture` | Grant entitlement (aktifkan plan) |
| `pending` | Simpan sebagai pending (tidak grant) |
| `deny` / `cancel` / `expire` | Tidak grant |
| `refund` | Revoke entitlement |

**Logic grant entitlement:**
```python
# 1. Parse order_id → user_id + plan
# 2. Cek signature valid
# 3. Cek status == settlement/capture
# 4. Update entitlements: plan, status=active, current_period_end = now + 30/365 hari
```

---

## 5. Env Vars (`.env` backend)

```bash
# Midtrans
MIDTRANS_SERVER_KEY=SB-Mid-server-xxx        # sandbox → production nanti
MIDTRANS_CLIENT_KEY=SB-Mid-client-xxx
MIDTRANS_IS_PRODUCTION=false                 # false = sandbox
MIDTRANS_MERCHANT_ID=xxx                      # opsional
```

**Frontend env (Vite):**
```bash
VITE_MIDTRANS_CLIENT_KEY=SB-Mid-client-xxx
```

---

## 6. Frontend Changes

### 6.1 Load Midtrans Snap
```html
<!-- index.html -->
<script src="https://app.sandbox.midtrans.com/snap/snap.js" data-client-key="SB-Mid-client-xxx"></script>
<!-- production: https://app.midtrans.com/snap/snap.js -->
```

### 6.2 Pricing page — upgrade button
```js
async function upgrade(planId) {
  const r = await fetch('/api/billing/midtrans/checkout/' + planId, {
    method: 'POST', headers: { Authorization: 'Bearer ' + token }
  });
  const data = r.data;
  if (window.snap) {
    window.snap.pay(data.snap_token, {
      onSuccess: (result) => { window.location = '/billing/success'; },
      onPending: (result) => { /* show pending message */ },
      onError: (result) => { window.location = '/billing/failed'; },
      onClose: () => { /* user closed popup */ }
    });
  } else {
    window.location = data.redirect_url;  // fallback
  }
}
```

### 6.3 Redirect pages
- `/billing/success` — "Pembayaran berhasil! Plan kamu udah aktif."
- `/billing/failed` — "Pembayaran belum selesai. Coba lagi."

*(Kedua halaman ini udah dibuat di frontend sebagai `QoraBillingResult`)*

---

## 7. Reconciliation & Testing

### Sandbox test (sebelum production)
1. Set `MIDTRANS_IS_PRODUCTION=false`
2. Pakai **Midtrans sandbox dashboard** (demo merchant: `G992637357` / password bebas)
3. Test metode: QRIS, VA BCA, GoPay, Credit Card
   - Card test: `4811 1111 1111 1114`, CVV `123`, exp bulan depan
4. Verifikasi webhook settlement → entitlement aktif di DB

### Production checklist
- [ ] Ganti server key ke production (`MIDTRANS_IS_PRODUCTION=true`)
- [ ] Webhook URL: `https://qora.ai/api/billing/midtrans/notifications`
- [ ] Set `BILLING_ENFORCED=true`
- [ ] Test transaksi kecil (Rp10.000) → verifikasi entitlement
- [ ] Monitoring: log semua webhook + entitlement changes

---

## 8. Dual Gateway (Midtrans + Xendit)

| Region | Gateway | Currency |
|---|---|---|
| Indonesia | **Midtrans** | IDR |
| ASEAN | **Xendit** (nanti) | USD |
| ROW | **Xendit** (nanti) | USD |

**Provider abstraction:**
```python
# billing/providers.py
def create_checkout(s, user, plan):
    region = user.profile.region
    if region == "indo":
        return midtrans.create_snap_checkout(s, user, plan)   # IDR
    return xendit.create_invoice(s, plan, amount_usd, user)   # USD

def resolve_webhook(request) -> Entitlement:
    # route by URL path: /midtrans/notifications vs /xendit/webhooks
    ...
```

---

## 9. Kebutuhan dari Arran (untuk mulai)

1. ✅ **NIB** — udah jadi
2. ⏳ **Daftar Midtrans** (https://dashboard.midtrans.com/register)
   - Pilih paket: **Basic/Startup** (0% biaya setup, per-transaksi fee)
   - Butuh: NIB, KTP direktur, rekening bank, NPWP
3. ⏳ **Dapet Server Key + Client Key** (sandbox dulu)
4. ⏳ Kasih ke Ker → set env vars + test sandbox end-to-end

---

## 10. Estimasi Biaya Midtrans

| Metode | Fee |
|---|---|
| QRIS | ~0.7% |
| GoPay / OVO / DANA | ~2-3% |
| Virtual Account | ~Rp4.000 flat (BCA/BNI/Mandiri) atau ~1-2% |
| Alfamart/Indomaret | ~Rp3.000-5.000 flat |
| Credit Card | ~2.9% |

**Contoh per transaksi bulanan (Rp119.000):**
- QRIS: ~Rp833
- GoPay: ~Rp2.380-3.570
- VA BCA: ~Rp4.000
- **Margin Qora tetap >90%** (LLM cost ~Rp1.500/sesi)

---

## 11. Timeline

| Step | Durasi |
|---|---|
| Registrasi Midtrans + verifikasi | 1-3 hari kerja |
| Setup sandbox + env vars | 0.5 hari |
| Implementasi backend endpoint | 1 hari |
| Frontend Snap integration | 0.5 hari |
| Test sandbox end-to-end | 1 hari |
| Switch production + test kecil | 0.5 hari |
| **Total** | **~4-7 hari kerja** |
