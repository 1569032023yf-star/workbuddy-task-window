"""Read-only Review Center auto-classify for 2026-08-20 inventory stage.
Evaluates manual_review_needed leads WITH email against A0 hygiene gate.
NO writes to DB. NO SMTP. NO Final Send Plan.
"""
import sqlite3
from collections import Counter
from lead_hygiene_gate import evaluate_a0
from production_adapter import build_candidate_from_db_row, build_context

DB = 'data/bd_leads.db'
ALLOWED = ('TN','AR','KY','OH','IN','MN','NE','NC','OR','CO')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

rows = [dict(r) for r in conn.execute(
    "SELECT * FROM leads WHERE status='manual_review_needed' AND email IS NOT NULL AND email != ''"
).fetchall()]

ctx = build_context(conn)
verdicts = Counter()
reasons = Counter()
pass_ids = []
allowed_n = 0
for ld in rows:
    in_allowed = ld.get('state') in ALLOWED
    if in_allowed:
        allowed_n += 1
    try:
        cand = build_candidate_from_db_row(ld, ctx)
        dec = evaluate_a0(cand)
    except Exception as e:
        verdicts['EVAL_ERROR'] += 1
        reasons[f'ERROR:{type(e).__name__}'] += 1
        continue
    if dec.a0_eligible:
        verdicts['A0_PASS'] += 1
        pass_ids.append(ld['id'])
    else:
        verdicts['B2_manual_review'] += 1
    for r in dec.reasons:
        reasons[r] += 1

print('=== Review Center auto-classify (READ-ONLY) ===')
print(f'total manual_review_needed WITH email: {len(rows)}')
print(f'  in allowed states: {allowed_n}')
print(f'verdicts: {dict(verdicts)}')
print(f'A0 pass lead_ids: {pass_ids}')
print()
print('Top reasons:')
for k, v in reasons.most_common(25):
    print(f'  {v:4d}  {k}')
conn.close()
