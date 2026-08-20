# NayiSaans Backend

FastAPI backend for the NayiSaans (RecoveryTwin) cigarette-recovery app. Matches the frontend's `api.js` request/response shapes exactly.

## Run locally

```bash
python3 -m venv venv
        
Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Runs on SQLite by default (`nayisaans.db`, created automatically) — no setup needed for local dev/demo. To use Postgres, copy `.env.example` to `.env`, set `DATABASE_URL`, and load it (e.g. `python-dotenv` or export manually) before starting.

## Wiring to the frontend

In `api.js`, set:
```js
const API_BASE_URL = "http://localhost:8000";
const DEMO_MODE = false;
```

## Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | /signup | — | Create account, returns token |
| POST | /login | — | Returns token |
| GET | /me | ✓ | Current user |
| POST | /onboarding | ✓ | Save smoking profile, initialize twin |
| POST | /checkin | ✓ | Log "smoked"/"resisted" + stress/moods, recomputes twin |
| GET | /checkins/today | ✓ | Today's check-in list |
| POST | /physiology | ✓ | Log client-computed {bpm, quality}, recomputes twin |
| GET | /dashboard | ✓ | Full dashboard payload |
| GET | /twin/state | ✓ | Raw twin state |
| GET | /timeline | ✓ | Chronological recovery events |
| DELETE | /account | ✓ | Delete account + all data |

All `✓` routes need `Authorization: Bearer <token>`.

## Notes

- Nicotine model: exponential decay, `app/ml/nicotine_model.py`
- Craving-risk model: logistic regression trained on a synthetic dataset at first use + SHAP, `app/ml/craving_model.py` — **not clinically validated**, matches the doc's labeling requirements
- Twin recompute: `app/ml/twin_engine.py`, called after every checkin/physiology/onboarding event
- rPPG stays client-side (`rppg.js`) — backend only logs the derived `{bpm, quality}`, never raw video, per the privacy-by-design approach
