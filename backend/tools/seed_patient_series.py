"""Seed patient_series (PRD_QORA_MENTOR §14.1 adapted to the real catalog).

Idempotent upsert — safe to re-run. Two continuity series built from REAL
catalog cases + REAL red flags:

1. budi_uta_series:  im_uta_001 (DVT) → em_pulmonary_embolism_001 (PE)
   Trigger: missed red flag "chest pain" in im_uta_001 (PE screen).
2. joko_t2dm_series: im_new_t2dm_001 (T2DM) → em_diabetic_ketoacidosis_001 (DKA)
   Trigger: missed red flag "diabetic ketoacidosis" in im_new_t2dm_001.

Usage (from backend/):
    .venv/bin/python tools/seed_patient_series.py
"""
import sys
from datetime import datetime, timezone

sys.path.insert(0, ".")

from app.database import SessionLocal  # noqa: E402
from app.domains.mentor.models import PatientSeries  # noqa: E402

_SERIES = [
    {
        "id": "budi_uta_series",
        "name": "Pak Budi",
        "base_condition": "deep vein thrombosis",
        "age": 52,
        "gender": "male",
        "occupation": "Supir truk jarak jauh",
        "case_sequence": ["im_uta_001", "em_pulmonary_embolism_001"],
        "triggers": [
            {"type": "missed_red_flag", "value": "chest pain",
             "target_case": "em_pulmonary_embolism_001",
             "description": "User melewatkan skrining PE (nyeri dada/sesak) di im_uta_001"}
        ],
        "next_visit_context": {
            "days_later": 5,
            "reason": "Kaki membaik tapi tiba-tiba nyeri dada dan sesak napas",
            "new_symptoms": ["nyeri dada mendadak", "sesak napas", "batuk ringan"],
        },
    },
    {
        "id": "joko_t2dm_series",
        "name": "Pak Joko",
        "base_condition": "diabetes melitus tipe 2",
        "age": 58,
        "gender": "male",
        "occupation": "Pedagang pasar",
        "case_sequence": ["im_new_t2dm_001", "em_diabetic_ketoacidosis_001"],
        "triggers": [
            {"type": "missed_red_flag", "value": "diabetic ketoacidosis",
             "target_case": "em_diabetic_ketoacidosis_001",
             "description": "User melewatkan skrining DKA di im_new_t2dm_001"}
        ],
        "next_visit_context": {
            "days_later": 14,
            "reason": "Haus terus, mual muntah, napas cepat dan dalam",
            "new_symptoms": ["haus berlebihan", "mual muntah",
                             "napas cepat dan dalam", "mengantuk"],
        },
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        for s in _SERIES:
            row = db.get(PatientSeries, s["id"])
            if row:
                for k, v in s.items():
                    setattr(row, k, v)
                print(f"updated {s['id']}")
            else:
                db.add(PatientSeries(**s))
                print(f"inserted {s['id']}")
        db.commit()
        print(f"OK — {len(_SERIES)} series seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
