"""
Roktandrazo BD Outreach - Email Template V4
Premium Puzzles & Card Games — Active Template (2026-06-30)
"""

SIGNATURE_TEXT = """
Ian
Business Development Specialist

Play, Learn, Laugh!
website: roktandrazo.com


If this isn't relevant, just reply "unsubscribe" and I won't follow up.
"""

SIGNATURE_HTML = """<p><strong>Ian</strong><br>
Business Development Specialist</p>
<p><em>Play, Learn, Laugh!</em><br>
website: <a href="https://roktandrazo.com">roktandrazo.com</a></p>
<hr>
<p><small>If this isn't relevant, just reply "unsubscribe" and I won't follow up.</small></p>
"""

def _subject_for(store_name: str) -> str:
    return f'Premium puzzles & card games for {store_name} (Low MOQ / DDP)'

BODY_TEXT = """Hi {greeting},

I'm Ian from rokt&razo. We are a manufacturer (with our own brand) with 10+ years of experience specializing in premium jigsaw puzzles and family card games.

We are expanding our U.S. retail network and offer:

* Low MOQs & DDP / door-to-door quotes available
* Unique 24-in-1 puzzle collections with strong online demand
* Custom & private-label options

If interested, we can set up a quick Zoom call to discuss:

1. Test-selling with sample options
2. How to cut costs and improve quality for your existing products

Just let us know — we aim to be the long-term partner for your business success.

{signature}
"""

BODY_HTML = """<p>Hi {greeting},</p>

<p>I'm Ian from <strong>rokt&amp;razo</strong>. We are a manufacturer (with our own brand) with 10+ years of experience specializing in premium jigsaw puzzles and family card games.</p>

<p>We are expanding our U.S. retail network and offer:</p>

<ul>
<li><strong>Low MOQs &amp; DDP / door-to-door quotes</strong> available</li>
<li><strong>Unique 24-in-1 puzzle collections</strong> with strong online demand</li>
<li><strong>Custom &amp; private-label</strong> options</li>
</ul>

<p>If interested, we can set up a quick Zoom call to discuss:</p>

<ol>
<li>Test-selling with sample options</li>
<li>How to cut costs and improve quality for your existing products</li>
</ol>

<p>Just let us know — we aim to be the long-term partner for your business success.</p>

{signature}
"""


def _safety_check(text: str) -> list:
    issues = []
    if "{{" in text or "}}" in text:
        issues.append("Unreplaced template braces {{}}")
    if "undefined" in text.lower():
        issues.append("Contains 'undefined'")
    if "None" in text:
        issues.append("Contains Python 'None'")
    if "null" in text.lower():
        issues.append("Contains 'null'")
    if "&ndash;" in text:
        issues.append("Raw HTML entity &ndash;")
    if "&amp;" in text and "<" not in text:
        issues.append("Raw HTML entity &amp; outside HTML context")
    if "stationary" in text.lower():
        issues.append("stationary typo (should be stationery)")
    return issues


def get_email_for_lead(lead: dict, template_key: str = None) -> dict:
    """Generate email content for a lead using V4 template."""
    store_name = (lead.get("store_name") or "").strip()
    if not store_name or store_name.lower() in ("null", "none", "undefined"):
        greeting = "there"
        subject = 'Premium puzzles & card games for your store (Low MOQ / DDP)'
    else:
        greeting = f"{store_name} team"
        subject = f'Premium puzzles & card games for {store_name} (Low MOQ / DDP)'

    body_text = BODY_TEXT.format(greeting=greeting, signature=SIGNATURE_TEXT)
    body_html = BODY_HTML.format(greeting=greeting, signature=SIGNATURE_HTML)

    for label, content in [("text", body_text), ("html", body_html)]:
        issues = _safety_check(content)
        if issues:
            print(f"  WARNING [{label}]: {'; '.join(issues)}")

    return {
        "template_key": "premium_puzzles_card_games_v4",
        "subject": subject,
        "body_text": body_text.strip(),
        "body_html": body_html.strip(),
    }


def apply_email_to_lead(lead: dict, template_key: str = None) -> dict:
    email_data = get_email_for_lead(lead)
    lead["email_template"] = email_data["template_key"]
    lead["email_subject"] = email_data["subject"]
    lead["email_body"] = email_data["body_text"]
    lead["email_body_html"] = email_data["body_html"]
    return lead
