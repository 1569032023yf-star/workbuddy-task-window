# DB Schema / 数据库结构

Generated: 2026-07-07 16:14 Asia/Shanghai

CREATE TABLE leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        -- 基本信息
        store_name TEXT NOT NULL,
        store_type TEXT,
        city TEXT,
        state TEXT,
        official_website TEXT,
        contact_page TEXT,
        wholesale_or_vendor_page TEXT,
        email TEXT,
        email_type TEXT,
        contact_form_url TEXT,
        evidence_url TEXT,
        source_keyword TEXT,
        fit_reason TEXT,
        product_fit TEXT,
        confidence_score TEXT,
        -- 状态
        status TEXT DEFAULT 'new',
        -- 邮件内容
        email_subject TEXT,
        email_body TEXT,
        -- 时间戳
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_checked_at TIMESTAMP,
        sent_at TIMESTAMP,
        replied_at TIMESTAMP,
        bounced_at TIMESTAMP,
        unsubscribed_at TIMESTAMP,
        last_followup_at TIMESTAMP,
        followup_count INTEGER DEFAULT 0,
        -- 备注
        notes TEXT,
        -- 错误信息
        error_message TEXT,
        -- 去重
        domain_hash TEXT, email_source_type TEXT DEFAULT 'unknown', email_verified_on_official_site INTEGER DEFAULT 0, mx_provider TEXT DEFAULT '', campaign TEXT DEFAULT '', template_id TEXT DEFAULT '', priority TEXT DEFAULT 'normal', manual_found_email TEXT, manual_email_source_url TEXT, manual_email_source_type TEXT, manual_decision TEXT, manual_note TEXT, manual_verified_by TEXT DEFAULT 'user', manual_verified_at TIMESTAMP, evidence_snippet TEXT, evidence_checked_at TEXT, evidence_method TEXT,
        UNIQUE(domain_hash)
    );

CREATE TABLE sqlite_sequence(name,seq);

CREATE TABLE suppression_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        reason TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

CREATE TABLE send_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        email TEXT,
        subject TEXT,
        status TEXT,
        error_message TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lead_id) REFERENCES leads(id)
    );

CREATE TABLE bounce_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER,
    email TEXT,
    domain TEXT,
    campaign TEXT,
    bounce_received_at TEXT,
    status_code TEXT,
    diagnostic_code TEXT,
    bounce_type TEXT,
    raw_message_subject TEXT,
    recommended_action TEXT,
    processed_at TEXT
);

CREATE TABLE reply_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER,
    email TEXT,
    reply_received_at TEXT,
    reply_type TEXT,
    summary TEXT,
    suggested_action TEXT,
    raw_subject TEXT,
    processed_at TEXT
);

CREATE TABLE system_config (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT
);

