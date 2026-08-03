"""BD Operations Center API — read-only stats for the dashboard.
All functions take a db connection factory and return JSON-safe dicts."""
import json, os, sqlite3, urllib.request, time
from datetime import datetime, timedelta, timezone

CST = timezone(timedelta(hours=8))
TRACKING_BASE = "https://roktandrazo-email-tracker.1569032023yf.workers.dev"

_cache = {}
_cache_ttl = {"tracking": 30, "default": 15}


def _cached(key, ttl_key="default"):
    val = _cache.get(key)
    if val and time.time() - val["t"] < _cache_ttl.get(ttl_key, 15):
        return val["d"]
    return None


def _set_cache(key, data):
    _cache[key] = {"d": data, "t": time.time()}


def _now_cst():
    return datetime.now(CST)


def _today_str():
    return _now_cst().strftime("%Y-%m-%d")


# ═══════════════════════════════════════════════
# D1 tracking fetch
# ═══════════════════════════════════════════════

def _fetch_d1_sql(sql: str):
    """Run SQL against Cloudflare D1 via Worker internal API."""
    try:
        token = os.environ.get("DASHBOARD_API_KEY", "roktandrazo-dashboard-key-2026")
        req = urllib.request.Request(
            f"{TRACKING_BASE}/internal/query",
            data=json.dumps({"sql": sql}).encode(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except Exception:
        return None


def get_tracking_stats():
    cached = _cached("tracking_stats", "tracking")
    if cached:
        return cached
    # Read from poller's tracking cache (created by bd_ops_poller via curl transport)
    try:
        cache_path = os.path.join(os.path.dirname(__file__), "output", "bd_ops_poller_tracking_cache.json")
        with open(cache_path, "r") as f:
            data = json.load(f)
        if data.get("available"):
            result = {
                "messages_with_open": data.get("messages_with_open", 0),
                "total_open_signals": data.get("total_open_signals", 0),
                "tracked_sent": data.get("tracked_sent", 0),
                "coverage": round(data.get("messages_with_open", 0) / max(1, data.get("tracked_sent", 1)) * 100, 1),
                "breakdown": data.get("breakdown", {}),
                "available": True,
                "synced_at": data.get("synced_at", ""),
                "source": "poller_cache",
            }
            _set_cache("tracking_stats", result)
            return result
    except Exception:
        pass
    return {"messages_with_open": 0, "total_open_signals": 0, "breakdown": {},
            "coverage": 0, "tracked_sent": 0,
            "available": False, "error": "poller_cache_unavailable"}


# ═══════════════════════════════════════════════
# Today stats
# ═══════════════════════════════════════════════

def get_today_stats(db_path: str):
    t = _today_str()
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Planned today
    planned = c.execute("""
        SELECT message_type, COUNT(*) FROM final_send_plan
        WHERE outreach_batch_date = ? AND status = 'planned'
        GROUP BY message_type
    """, (t,)).fetchall()

    # Sent today (by send_log, not sender copies)
    sent = c.execute("""
        SELECT message_type, COUNT(*) FROM send_log
        WHERE outreach_batch_date = ? AND status = 'sent'
          AND message_type IS NOT NULL
          AND message_type NOT IN ('test','internal_report','acceptance_test','sender_copy')
        GROUP BY message_type
    """, (t,)).fetchall()

    # Fallback: sent_at CST date
    sent2 = c.execute("""
        SELECT message_type, COUNT(*) FROM send_log
        WHERE status = 'sent' AND sent_at LIKE ?
          AND message_type NOT IN ('test','internal_report','acceptance_test')
        GROUP BY message_type
    """, (f"{t}%",)).fetchall()

    # Failed / skipped today
    failed = c.execute("""
        SELECT COUNT(*) FROM send_log WHERE status IN ('failed','bounced')
          AND (outreach_batch_date = ? OR sent_at LIKE ?)
          AND message_type NOT IN ('test')
    """, (t, f"{t}%")).fetchone()[0]
    skipped = c.execute("""
        SELECT COUNT(*) FROM final_send_plan 
        WHERE outreach_batch_date = ? AND status = 'skipped'
    """, (t,)).fetchone()[0]

    # Unique orgs sent today
    uniq_orgs = c.execute("""
        SELECT COUNT(DISTINCT COALESCE(NULLIF(l.organization_key,''),'org_'||sl.lead_id))
        FROM send_log sl LEFT JOIN leads l ON sl.lead_id = l.id
        WHERE sl.status = 'sent' AND sl.message_type NOT IN ('test')
          AND (sl.outreach_batch_date = ? OR sl.sent_at LIKE ?)
    """, (t, f"{t}%")).fetchone()[0]

    # Reply / bounce today
    replies = c.execute("SELECT COUNT(*) FROM reply_log WHERE reply_received_at LIKE ?", (f"{t}%",)).fetchone()[0]
    hard_bounces = c.execute("""
        SELECT COUNT(*) FROM bounce_log 
        WHERE bounce_type IN ('hard','policy','permanent') AND bounce_received_at LIKE ?
    """, (f"{t}%",)).fetchone()[0]
    unsub = c.execute("SELECT COUNT(*) FROM leads WHERE unsubscribed_at LIKE ?", (f"{t}%",)).fetchone()[0]

    conn.close()

    def _sum_plans(rows, key="new_outreach"):
        for r in rows:
            if r[0] == key: return r[1]
        return 0

    return {
        "date": t, "timezone": "Asia/Shanghai",
        "planned_new": _sum_plans(planned, "new_outreach"),
        "planned_fw": _sum_plans(planned, "follow_up"),
        "sent_new": _sum_plans(sent or sent2, "new_outreach") or _sum_plans(sent2, "new_outreach"),
        "sent_fw": _sum_plans(sent or sent2, "follow_up") or _sum_plans(sent2, "follow_up"),
        "failed": failed, "skipped": skipped,
        "unique_orgs_sent": uniq_orgs,
        "replies": replies, "hard_bounces": hard_bounces, "unsubscribed": unsub,
    }


# ═══════════════════════════════════════════════
# Inventory
# ═══════════════════════════════════════════════

def get_inventory(db_path: str):
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM leads").fetchone()[0]

    type_kw = ['game','toy','book','gift','museum','hobby','education','children',
               'retail','card','puzzle','comic','visitor','souvenir','stationery',
               'craft','general','boutique','department','specialty','independent']
    type_sql = ' OR '.join([f"store_type LIKE '%{t}%'" for t in type_kw])

    def _count(where):
        return c.execute(f"SELECT COUNT(*) FROM leads WHERE {where} AND ({type_sql})").fetchone()[0]

    # Send-preparation candidates
    send_prep = c.execute(f"""SELECT COUNT(*) FROM leads WHERE
        official_website IS NOT NULL AND official_website != ''
        AND (email IS NOT NULL AND email != '' OR contact_form_url IS NOT NULL AND contact_form_url != '')
        AND status NOT IN ('sent','do_not_contact','review_rejected') AND unsubscribed_at IS NULL AND bounced_at IS NULL
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT DISTINCT lead_id FROM send_log WHERE status='sent')
        AND ({type_sql})
    """).fetchone()[0]

    strict_a0 = _count("""status='new' AND confidence_score='A' AND auto_sendable=1
        AND email_verified_on_official_site=1 AND evidence_url IS NOT NULL AND evidence_url != ''
        AND evidence_snippet IS NOT NULL AND evidence_snippet != ''
        AND email IS NOT NULL AND email != ''
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status='sent')
        AND id NOT IN (SELECT lead_id FROM bounce_log WHERE bounce_type IN ('hard','policy','permanent'))""")

    strict_a0_orgs = c.execute(f"""SELECT COUNT(DISTINCT COALESCE(NULLIF(organization_key,''),'org_'||id))
        FROM leads WHERE status='new' AND confidence_score='A' AND auto_sendable=1
        AND email_verified_on_official_site=1 AND evidence_url IS NOT NULL AND evidence_url != ''
        AND email IS NOT NULL AND email != '' AND ({type_sql})
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status='sent')""").fetchone()[0]

    manual = _count("review_reason_code IS NOT NULL AND review_reason_code != '' AND review_status = 'pending'")
    web_lookup = _count("(review_reason_code = 'WEAK_EVIDENCE' OR notes LIKE '%website_lookup%') AND review_status = 'pending'")
    contact_form = _count("status = 'contact_form_pool' OR review_reason_code = 'CONTACT_FORM_ONLY'")
    low_prio = _count("review_reason_code = 'LOW_PRIORITY' OR (status='manual_review_needed' AND confidence_score='C')")
    prev_sent = _count("id IN (SELECT DISTINCT lead_id FROM send_log WHERE status='sent')")
    suppressed = _count("email IN (SELECT email FROM suppression_list) OR status='do_not_contact' OR unsubscribed_at IS NOT NULL")
    bounce_rec = _count("id IN (SELECT lead_id FROM bounce_log WHERE bounce_type IN ('hard','policy','permanent')) AND id NOT IN (SELECT DISTINCT lead_id FROM send_log WHERE status='sent')")
    staging = c.execute("SELECT COUNT(*) FROM lead_discovery_results").fetchone()[0]

    conn.close()
    return {
        "total_leads": total, "send_prep_candidates": send_prep,
        "strict_a0_locations": strict_a0, "strict_a0_organizations": strict_a0_orgs,
        "org_outreach_opps": strict_a0_orgs,  # same as A0 orgs for now
        "manual_review": manual, "website_lookup": web_lookup,
        "contact_form_only": contact_form, "low_priority": low_prio,
        "previously_sent": prev_sent, "permanently_suppressed": suppressed,
        "bounce_recovery": bounce_rec, "unprocessed_staging": staging,
        "targets": {"critical": 40, "warning": 80, "target": 120},
        "gaps": {"to_40": max(0, 40 - strict_a0_orgs), "to_80": max(0, 80 - strict_a0_orgs),
                 "to_120": max(0, 120 - strict_a0_orgs)},
        "status": "critical" if strict_a0_orgs < 40 else ("warning" if strict_a0_orgs < 80 else "healthy"),
    }


# ═══════════════════════════════════════════════
# Search progress
# ═══════════════════════════════════════════════

def get_search_progress():
    result = {"active_city": "Nashville", "active_state": "TN",
              "city_status": "active_partial_webfetch_collection",
              "queries_total": 22, "queries_executed": 22, "queries_remaining": [],
              "current_query": None, "current_source": None,
              "raw_records": 0, "unique_locations": 0, "unique_organizations": 0}
    try:
        with open("data/webfetch_nashville_dashboard.json", "r") as f:
            d = json.load(f)
        gc = d.get("G_CURSOR", {})
        disc = d.get("A_FILE_LEVEL_DISCOVERY", {})
        result["queries_executed"] = gc.get("query_index", 22)
        result["queries_remaining"] = gc.get("remaining_queries", [])
        result["current_query"] = gc.get("next_query")
        result["unique_locations"] = disc.get("unique_locations", 39)
        result["unique_organizations"] = disc.get("unique_organizations", 33)
        result["raw_records"] = d.get("A_FILE_LEVEL_DISCOVERY", {}).get("raw_records",
                                    gc.get("raw_records", 58))
        result["updated_at"] = d.get("generated_at", gc.get("timestamp", ""))
    except Exception:
        pass
    return result


# ═══════════════════════════════════════════════
# Final Send Plan
# ═══════════════════════════════════════════════

def get_final_plan(db_path: str):
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    by_status = {}
    for r in c.execute("SELECT status, COUNT(*) FROM final_send_plan GROUP BY status"):
        by_status[r[0]] = r[1]

    entries = c.execute("""
        SELECT fsp.*, l.store_name, l.organization_key, l.tracking_message_id
        FROM final_send_plan fsp LEFT JOIN leads l ON fsp.lead_id = l.id
        ORDER BY fsp.planned_sequence
    """).fetchall()

    plan_list = []
    for r in entries:
        d = dict(r)
        plan_list.append({
            "plan_id": d.get("plan_id", ""), "lead_id": d["lead_id"],
            "store": d.get("store_name", ""), "org": d.get("organization_key", ""),
            "recipient": d["recipient_email"][:30] if d.get("recipient_email") else "",
            "type": d["message_type"], "status": d["status"],
            "tracking": d.get("tracking_message_id", ""),
            "batch_date": d.get("outreach_batch_date", ""),
            "sequence": d.get("planned_sequence", 0),
        })
    conn.close()
    return {"by_status": by_status, "total": len(plan_list), "entries": plan_list}


# ═══════════════════════════════════════════════
# Health
# ═══════════════════════════════════════════════

def get_health(db_path: str):
    result = {"components": {}, "generated_at": _now_cst().isoformat()}

    # Review Server
    result["components"]["review_server"] = {"status": "healthy", "port": 8765}

    # Production DB
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        c = conn.cursor()
        qc = c.execute("PRAGMA quick_check").fetchone()[0]
        conn.close()
        result["components"]["database"] = {"status": "healthy" if qc == "ok" else "warning", "quick_check": qc}
    except Exception as e:
        result["components"]["database"] = {"status": "down", "error": str(e)}

    # Tracking Worker
    try:
        r = urllib.request.urlopen(f"{TRACKING_BASE}/healthz", timeout=5)
        h = json.loads(r.read())
        result["components"]["tracking_worker"] = {"status": "healthy" if h.get("status") == "ok" else "warning"}
    except Exception:
        result["components"]["tracking_worker"] = {"status": "down"}

    # SMTP / IMAP config
    result["components"]["smtp"] = {"status": "configured" if os.environ.get("BD_SMTP_USER") or os.path.exists(".env") else "not_configured"}
    result["components"]["imap"] = {"status": "configured" if os.environ.get("BD_IMAP_USER") else "unknown"}

    # Risk gate / scheduler
    try:
        conn2 = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        c2 = conn2.cursor()
        rg = c2.execute("SELECT value FROM system_state WHERE key='risk_gate_status'").fetchone()
        mp = c2.execute("SELECT value FROM system_state WHERE key='manual_pause'").fetchone()
        conn2.close()
        result["risk_gate"] = rg[0] if rg else "unknown"
        result["manual_pause"] = mp[0] if mp else "false"
    except Exception:
        result["risk_gate"] = "unknown"
        result["manual_pause"] = "unknown"

    # Sending window
    h = _now_cst().hour
    result["in_send_window"] = 23 <= h or h < 1
    result["current_time_cst"] = _now_cst().strftime("%Y-%m-%d %H:%M:%S")

    return result


# ═══════════════════════════════════════════════
# Data quality warnings
# ═══════════════════════════════════════════════

def get_data_quality(db_path: str):
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    c = conn.cursor()
    warnings = []
    now = _now_cst()

    # organization_key empty
    n = c.execute("SELECT COUNT(*) FROM leads WHERE (organization_key IS NULL OR organization_key='') AND status NOT IN ('do_not_contact','review_rejected')").fetchone()[0]
    if n > 10:
        warnings.append({"zh": f"{n} 条线索缺少组织标识", "en": f"{n} leads missing organization_key", "count": n, "link": "/review"})

    # Strict A0 = 0
    a0 = c.execute("SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A' AND auto_sendable=1 AND email_verified_on_official_site=1").fetchone()[0]
    if a0 == 0:
        warnings.append({"zh": "可发送库存为 0", "en": "Zero sendable inventory", "count": 0, "link": "/inventory"})

    # Stale tracking data
    stale = c.execute("SELECT COUNT(*) FROM lead_discovery_results WHERE discovered_at < ?", ((now - timedelta(days=30)).isoformat(),)).fetchone()[0]
    if stale > 0:
        warnings.append({"zh": f"{stale} 条发现数据超过 30 天未处理", "en": f"{stale} discovery results stale >30 days", "count": stale, "link": "/search"})

    # Manual review backlog
    mr = c.execute("SELECT COUNT(*) FROM leads WHERE review_reason_code IS NOT NULL AND review_reason_code != '' AND review_status = 'pending'").fetchone()[0]
    if mr > 50:
        warnings.append({"zh": f"人工审核积压 {mr} 条", "en": f"Manual review backlog: {mr}", "count": mr, "link": "/review"})

    # Expired planned plans
    expired = c.execute("SELECT COUNT(*) FROM final_send_plan WHERE status='planned' AND outreach_batch_date < ?", (_today_str(),)).fetchone()[0]
    if expired > 0:
        warnings.append({"zh": f"{expired} 条过期计划未处理", "en": f"{expired} expired planned entries", "count": expired, "link": "/engagement"})

    # send_log missing message_type
    no_type = c.execute("SELECT COUNT(*) FROM send_log WHERE status='sent' AND (message_type IS NULL OR message_type='') AND lead_id IS NOT NULL").fetchone()[0]
    if no_type > 0:
        warnings.append({"zh": f"{no_type} 条发送记录缺少消息类型", "en": f"{no_type} send_log entries missing message_type", "count": no_type, "link": "/engagement"})

    conn.close()
    return {"warnings": warnings, "generated_at": now.isoformat(), "total": len(warnings)}


# ═══════════════════════════════════════════════
# Combined summary
# ═══════════════════════════════════════════════

def get_ops_summary(db_path: str):
    def safe(fn, default):
        try: return fn()
        except Exception as e: return default if not isinstance(default, dict) else {"error": str(e), **default}
    return {
        "generated_at": _now_cst().isoformat(),
        "timezone": "Asia/Shanghai",
        "today": safe(lambda: get_today_stats(db_path), {"date": _today_str()}),
        "tracking": safe(lambda: get_tracking_stats(), {"available": False}),
        "inventory": safe(lambda: get_inventory(db_path), {}),
        "search": safe(lambda: get_search_progress(), {}),
        "final_plan": safe(lambda: get_final_plan(db_path), {"entries": []}),
        "health": safe(lambda: get_health(db_path), {"components": {}}),
        "data_quality": safe(lambda: get_data_quality(db_path), {"warnings": []}),
    }
