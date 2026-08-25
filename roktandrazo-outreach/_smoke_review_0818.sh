#!/bin/bash
PY="C:/Users/15690/.workbuddy/binaries/python/versions/3.13.12/python.exe"
PORT=8787
"$PY" bd_review_server.py --port $PORT > output/_smoke_review_server.log 2>&1 &
PID=$!
sleep 5
echo "=== server log (head) ==="
head -8 output/_smoke_review_server.log
echo "=== HTTP checks ==="
curl -s -o /dev/null -w "root  /            HTTP %{http_code}\n" http://127.0.0.1:$PORT/
curl -s -o /dev/null -w "review /review     HTTP %{http_code}\n" http://127.0.0.1:$PORT/review
curl -s -o /dev/null -w "summary /api/summary HTTP %{http_code}\n" http://127.0.0.1:$PORT/api/summary
echo "=== /api/summary body (first 500) ==="
curl -s "http://127.0.0.1:$PORT/api/summary" | head -c 500
echo
echo "=== /api/leads pending (first 300) ==="
curl -s "http://127.0.0.1:$PORT/api/leads?status=pending&per_page=3" | head -c 300
echo
echo "=== DB counts (direct) ==="
"$PY" -c "
import sqlite3
c = sqlite3.connect('data/bd_leads.db')
for st in ['manual_review_needed','contact_form_pool']:
    n = c.execute('SELECT COUNT(*) FROM leads WHERE status=?',(st,)).fetchone()[0]
    print(f'  status={st}: {n}')
n = c.execute(\"SELECT COUNT(*) FROM leads WHERE review_reason_code IS NOT NULL AND review_reason_code!='' AND COALESCE(review_status,'pending')='pending'\").fetchone()[0]
print(f'  review queue pending (review_reason_code set + review_status pending): {n}')
c.close()
"
kill $PID 2>/dev/null
echo "=== server stopped (pid $PID) ==="
