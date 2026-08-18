"""campaign_eligible_v2.py — Email Quality Gate V2（P1.4）。

V1 的 Campaign Eligible 规则全部保留（复用 review_campaign_eligible），
在 V1 基础上**追加** Email Quality Gate：

  ICP Qualified → Broad Ready → Official Ownership Evidence
                → MX Verification → Email Source Quality → Campaign Eligible V2

新增硬门禁：
  A. MX Verification（store-domain email 的域名 MX 状态）：
      允许进入下一层：MX_VALID / MAIL_ROUTE_VALID（Worker 返回 ok）
      BLOCK        ：nxdomain / null_mx / no_mail_route（MX Host Not Found 等）
      RETRY_PENDING：dns_error / 暂时无法确认 → 绝不当作 PASS，直接 BLOCK（可重试）
  B. Email Source Quality（按 Tier 评估）：
      E1 official_page_visible + email_verified_on_official_site=1  最高优先
      E2 web_search_official（搜索结果指向商户官方第一方页面）
      E3 公共免费邮箱（gmail/yahoo/hotmail/aol…）必须有商户官方第一方证据
      E4 guessed_email → 高风险，不再仅凭格式/域匹配直接通过；
         必须 MX PASS + 官网域匹配 + 官网可访问 + evidence fresh，否则 NEEDS_EMAIL_VERIFICATION
      BLOCK 仅第三方目录 + 猜测邮箱 + 无第一方证据
  C. Evidence Freshness：
      evidence_checked_at 距今 >90 天 → EVIDENCE_STALE（进入重新验证队列，不算 Eligible V2）

设计约束：
  - 只读验证，绝不写库（除 MX 查询写 system_config.mx_cache_<domain> 缓存外）。
  - 不改动历史真实结果（P1.2 15 条 bounce 保持 bounce_log/suppression/bounced）。
  - 本轮不启用 SMTP RCPT probing（MX Gate 先解决 domain_invalid 主因）。
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Optional

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from campaign_eligible import review_campaign_eligible, _is_official_evidence, _is_third_party_email
from broad_ready import FREE_MAILBOX_DOMAINS, _email_domain

# Asia/Shanghai
ASIA_SH = timezone(timedelta(hours=8))

# ── MX 状态常量 ─────────────────────────────────────────────
MX_OK = "ok"                # Worker 返回 mx_pass / implicit_mail_route
MX_NXDOMAIN = "nxdomain"
MX_NULL_MX = "null_mx"
MX_NO_ROUTE = "no_mail_route"
MX_DNS_ERROR = "dns_error"  # 暂时无法确认 → RETRY_PENDING，不 PASS

# Worker 状态 → V2 判定
_ALLOWED_MX = frozenset({MX_OK})                       # 允许进入下一层
_BLOCKED_MX = frozenset({MX_NXDOMAIN, MX_NULL_MX, MX_NO_ROUTE})
_RETRY_MX = frozenset({MX_DNS_ERROR})

# ── Email Source Tier ───────────────────────────────────────
TIER_E1 = "E1"
TIER_E2 = "E2"
TIER_E3 = "E3"
TIER_E4 = "E4"
TIER_BLOCK = "BLOCK"

# Evidence freshness：>90 天未重新确认 → stale
EVIDENCE_MAX_AGE_DAYS = 90


def _domain_of_email(email: str) -> str:
    if not email or "@" not in email:
        return ""
    return email.rsplit("@", 1)[1].strip().lower()


def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    v = str(value).strip()
    try:
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        dt = datetime.fromisoformat(v)
        return dt.astimezone(ASIA_SH) if dt.tzinfo else dt.replace(tzinfo=ASIA_SH)
    except ValueError:
        try:
            return datetime.strptime(v, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ASIA_SH)
        except ValueError:
            return None


def _get_mx_status(lead: Mapping[str, Any], ctx: Optional[Mapping[str, Any]]) -> dict:
    """查询 store-domain email 域名 MX 状态。

    优先使用 ctx 注入的 {domain: status} 缓存（批量场景复用）；否则走
    preflight_gate.query_mx（Worker 查询）。返回 {"status", "checked_at", "domain"}。
    """
    email = str(lead.get("email") or "")
    domain = _domain_of_email(email)
    if not domain:
        return {"status": MX_DNS_ERROR, "checked_at": None, "domain": ""}

    mx_lookup = (ctx or {}).get("mx_lookup") or {}
    if domain in mx_lookup:
        return {"status": mx_lookup[domain], "checked_at": None, "domain": domain}

    try:
        from preflight_gate import query_mx
        status, checked_at = query_mx(domain)
        # query_mx 返回的是映射后的状态：ok / nxdomain / null_mx / no_mail_route / dns_error
        return {"status": status, "checked_at": checked_at, "domain": domain}
    except Exception:
        return {"status": MX_DNS_ERROR, "checked_at": None, "domain": domain}


def _website_reachable(website: str, timeout: int = 10) -> bool:
    """官网 HTTP 是否可访问（辅助信号，非硬门禁）。只返回 True/False，失败不算 Evidence 失败。"""
    if not website:
        return False
    w = website.strip()
    if not w.startswith("http"):
        w = "https://" + w
    try:
        import urllib.request
        req = urllib.request.Request(w, method="HEAD", headers={"User-Agent": "quality-gate/2.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        return 200 <= resp.status < 400
    except Exception:
        return False


def email_source_tier(lead: Mapping[str, Any], website: str) -> tuple[str, str]:
    """按邮箱来源质量分级。返回 (tier, reason)。"""
    email = str(lead.get("email") or "")
    email_src = str(lead.get("email_source_type") or "").lower()
    verified = bool(lead.get("email_verified_on_official_site"))
    edom = _email_domain(email) if email and "@" in email else ""

    # E1: official_page_visible + 官网验证通过
    if email_src == "official_page_visible" and verified:
        return TIER_E1, "official_page_visible + verified_on_official_site"

    # E2: web_search_official（搜索结果指向官方第一方页面）
    if email_src == "web_search_official":
        # 搜索来源 + evidence 为官方/第一方（复用 V1 official evidence 判定）
        official_ev = _is_official_evidence(lead, email, website)
        if official_ev:
            return TIER_E2, "web_search_official + official evidence"
        return TIER_BLOCK, "web_search_official but no official first-party evidence"

    # E3: 公共免费邮箱 → 必须有商户官方第一方证据
    if edom and edom in FREE_MAILBOX_DOMAINS:
        official_ev = _is_official_evidence(lead, email, website)
        if official_ev:
            return TIER_E3, f"free mailbox {edom} + official evidence"
        return TIER_BLOCK, f"free mailbox {edom} without official evidence"

    # E4: guessed_email → 高风险
    if email_src == "guessed_email":
        # 默认不作为优先库存；需通过加强验证（MX/域匹配/官网/evidence fresh）
        return TIER_E4, "guessed_email high-risk"

    # 其他来源（official_mailto / wholesale_vendor_page 等，V1 official 证据通过）
    official_ev = _is_official_evidence(lead, email, website)
    if official_ev:
        return TIER_E1, f"official evidence ({email_src})"
    return TIER_BLOCK, f"source={email_src} without official evidence"


def review_campaign_eligible_v2(lead: Mapping[str, Any],
                                ctx: Optional[Mapping[str, Any]] = None) -> dict:
    """Campaign Eligible V2：V1 规则 + Email Quality Gate。

    ctx 可注入：
      conn           — sqlite3.Connection（V1 broad_ready 需要）
      mx_lookup      — {domain: mx_status} 预查缓存（批量复用）
      allow_timezone_unresolved — bool（透传 V1）
      force_recheck  — bool（True 时强制现场查 MX，忽略 mx_lookup）
    """
    ctx = dict(ctx or {})
    conn = ctx.get("conn")
    website = str(lead.get("official_website") or "")

    # ── 1. V1 规则（全部保留）──
    v1 = review_campaign_eligible(lead, ctx)

    checks: dict[str, dict] = {}
    for name, c in (v1.get("checks") or {}).items():
        checks[name] = dict(c)

    # ── 2. MX Verification（硬门禁）──
    mx = _get_mx_status(lead, ctx)
    mx_status = mx.get("status", MX_DNS_ERROR)
    email = str(lead.get("email") or "")
    edom = _domain_of_email(email)
    mx_blocker = None

    if not edom:
        mx_blocker = "mx:no_email_domain"
        checks["mx_verification"] = {"pass": False, "detail": "no email domain"}
    elif mx_status in _ALLOWED_MX:
        checks["mx_verification"] = {"pass": True, "detail": f"domain={edom} MX={mx_status}"}
    elif mx_status in _BLOCKED_MX:
        mx_blocker = f"mx:{mx_status}"
        checks["mx_verification"] = {"pass": False, "detail": f"domain={edom} MX_BLOCK={mx_status}"}
    else:  # dns_error / retry_pending
        mx_blocker = "mx:retry_pending_dns_error"
        checks["mx_verification"] = {"pass": False, "detail": f"domain={edom} MX_UNAVAILABLE={mx_status}"}

    # ── 3. Email Source Quality（Tier）──
    tier, tier_reason = email_source_tier(lead, website)
    checks["email_source_tier"] = {"pass": True, "detail": f"{tier}: {tier_reason}"}

    # guessed_email 加强验证（E4）
    email_src = str(lead.get("email_source_type") or "").lower()
    if tier == TIER_E4:
        checks["email_source_tier"]["pass"] = False
        checks["email_source_tier"]["detail"] = f"E4 guessed_email needs enhanced verification: {tier_reason}"

    # ── 4. Evidence Freshness ──
    # 优先 evidence_checked_at；缺失时回退 last_checked_at（同为验证时间戳）。
    evidence_stale = False
    checked_raw = lead.get("evidence_checked_at") or lead.get("last_checked_at")
    checked_at = _parse_ts(checked_raw)
    if checked_at:
        age_days = (datetime.now(ASIA_SH) - checked_at).total_seconds() / 86400
        evidence_stale = age_days > EVIDENCE_MAX_AGE_DAYS
        checks["evidence_freshness"] = {
            "pass": not evidence_stale,
            "detail": f"checked_at={checked_at.isoformat()} age={age_days:.1f}d "
                      f"({'STALE' if evidence_stale else 'fresh'})",
        }
    else:
        checks["evidence_freshness"] = {
            "pass": False,
            "detail": "evidence_checked_at/last_checked_at missing → cannot confirm freshness",
        }
        evidence_stale = True

    # ── 汇总 ──
    blockers: list[str] = []
    for b in (v1.get("blockers") or []):
        blockers.append(b)

    if mx_blocker:
        blockers.append(mx_blocker)
    if tier == TIER_E4:
        blockers.append("guessed_email_without_enhanced_verification")
    if evidence_stale:
        blockers.append("evidence_stale")

    eligible = len(blockers) == 0

    # 池分类：V1 已 BLOCK 则保持 BLOCK；否则按 V2 原因分池
    if eligible:
        pool = "CAMPAIGN_ELIGIBLE_V2"
    elif any(b.startswith(("broad_ready:", "hygiene:", "third_party", "mx:")) for b in blockers):
        pool = "BLOCKED"
    elif any(b == "evidence_stale" or b.startswith("guessed_email")
             or b.startswith("mx:retry_pending") for b in blockers):
        pool = "NEEDS_EMAIL_VERIFICATION"
    else:
        pool = "NEEDS_MANUAL_REVIEW"

    return {
        "lead_id": lead.get("id"),
        "store_name": lead.get("store_name"),
        "email": email,
        "eligible": eligible,
        "pool": pool,
        "tier": tier,
        "mx_status": mx_status,
        "evidence_stale": evidence_stale,
        "checks": checks,
        "blockers": blockers,
        "v1_pool": v1.get("pool"),
        "campaign_eligible_version": "campaign_eligible_v2",
    }


def scan_v2_inventory(lead_ids: list[int], conn) -> list[dict]:
    """批量重跑 V2。只读，不写库。mx_lookup 预查所有 store-domain 去重。"""
    if not lead_ids:
        return []
    conn.row_factory = __import__("sqlite3").Row
    ph = ",".join("?" for _ in lead_ids)
    rows = conn.execute(f"SELECT * FROM leads WHERE id IN ({ph})", lead_ids).fetchall()

    # 预查所有去重域名 MX（批量复用，单域一次查询）
    domains = set()
    for r in rows:
        d = _domain_of_email(str(r["email"] or ""))
        if d:
            domains.add(d)
    mx_lookup = {}
    from preflight_gate import query_mx
    for d in sorted(domains):
        try:
            status, _ts = query_mx(d)
        except Exception:
            status = "dns_error"
        mx_lookup[d] = status

    results = []
    for row in rows:
        lead = dict(row)
        r = review_campaign_eligible_v2(lead, {"conn": conn, "mx_lookup": mx_lookup})
        results.append(r)
    return results
