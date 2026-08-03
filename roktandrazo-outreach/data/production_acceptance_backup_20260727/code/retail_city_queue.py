"""SQLite-backed single-city retail discovery state; no network or project imports."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from outreach_control import DEFAULT_RETAIL_CITIES, RETAIL_QUERY_FAMILIES, RETAIL_SOURCES, all_city_completion_conditions_met


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def seed_default_queue(conn: sqlite3.Connection) -> None:
    conn.executemany("""INSERT OR IGNORE INTO retail_city_queue (city, state, priority, timezone, status)
        VALUES (?, ?, ?, ?, 'pending')""", DEFAULT_RETAIL_CITIES)


def active_city(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute("""SELECT * FROM retail_city_queue
        WHERE status IN ('active','validating','paused_by_runtime_limit','places_matrix_completed_web_pending')
        ORDER BY CASE status WHEN 'active' THEN 0 WHEN 'paused_by_runtime_limit' THEN 1 ELSE 2 END, priority, id
        LIMIT 1""").fetchone()
    return dict(row) if row else None


def activate_next_city(conn: sqlite3.Connection) -> dict:
    current = active_city(conn)
    if current:
        if current['status'] in ('paused_by_runtime_limit', 'places_matrix_completed_web_pending'):
            conn.execute("UPDATE retail_city_queue SET status='active' WHERE id=?", (current['id'],))
            return dict(conn.execute("SELECT * FROM retail_city_queue WHERE id=?", (current['id'],)).fetchone())
        return current
    paused = conn.execute("SELECT * FROM retail_city_queue WHERE status='paused_by_runtime_limit' ORDER BY priority, id LIMIT 1").fetchone()
    if paused:
        conn.execute("UPDATE retail_city_queue SET status='active' WHERE id=?", (paused['id'],))
        return dict(conn.execute("SELECT * FROM retail_city_queue WHERE id=?", (paused['id'],)).fetchone())
    row = conn.execute("SELECT * FROM retail_city_queue WHERE status='pending' ORDER BY priority, id LIMIT 1").fetchone()
    if not row:
        raise RuntimeError('no pending retail city')
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("UPDATE retail_city_queue SET status='active', started_at=COALESCE(started_at, ?) WHERE id=?", (now, row['id']))
    return dict(conn.execute("SELECT * FROM retail_city_queue WHERE id=?", (row['id'],)).fetchone())


def search_queries(city_row: dict) -> list[str]:
    return [f"{family} {city_row['city']} {city_row['state']}" for family in RETAIL_QUERY_FAMILIES]


def checkpoint(conn: sqlite3.Connection, city_id: int, query_family: str, source: str, page_cursor: str,
               counters: dict[str, int] | None = None, paused: bool = False) -> None:
    if query_family not in RETAIL_QUERY_FAMILIES or source not in RETAIL_SOURCES:
        raise ValueError('unknown query family or source')
    counters = counters or {}
    allowed = {'discovered_count', 'unique_domain_count', 'official_site_count', 'public_email_count',
               'strict_a0_count', 'manual_review_count', 'contact_form_count', 'duplicate_count', 'rejected_count',
               'pages_processed', 'results_seen', 'new_unique_places', 'duplicate_places', 'provider_errors',
               'consecutive_pages_without_new_place'}
    table_cols = _columns(conn, 'retail_city_queue')
    updates = ['active_query_family=?', 'active_source=?', 'page_cursor=?', 'status=?']
    values: list[object] = [query_family, source, page_cursor, 'paused_by_runtime_limit' if paused else 'active']
    if 'active_provider' in table_cols:
        updates.insert(2, 'active_provider=?')
        values.insert(2, source)
    for name, value in counters.items():
        if name not in allowed:
            raise ValueError(f'unsupported counter: {name}')
        if name not in table_cols:
            continue
        updates.append(f'{name}=?')
        values.append(value)
    values.append(city_id)
    conn.execute(f"UPDATE retail_city_queue SET {', '.join(updates)} WHERE id=?", values)


def complete_if_exhausted(conn: sqlite3.Connection, city_id: int, checks: dict[str, bool]) -> bool:
    if not all_city_completion_conditions_met(checks):
        return False
    conn.execute("""UPDATE retail_city_queue SET status='search_matrix_exhausted', completed_at=?,
        completion_reason='search_matrix_exhausted' WHERE id=? AND status IN ('active','validating','paused_by_runtime_limit')""",
        (datetime.now(timezone.utc).isoformat(), city_id))
    return conn.total_changes > 0
