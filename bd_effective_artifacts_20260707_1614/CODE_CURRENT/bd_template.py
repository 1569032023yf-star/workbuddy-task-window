"""
Roktandrazo BD Outreach - Email Template V5
Premium Puzzles & Card Games — Active Template (2026-07-06)
"""

SIGNATURE_TEXT = """
Ian
Business Development Specialist
website: roktandrazo.com


If this isn't relevant, just reply "unsubscribe" and I won't follow up.
"""

SIGNATURE_HTML = """<p><strong>Ian</strong><br>
Business Development Specialist</p>
<p>website: <a href="https://roktandrazo.com">roktandrazo.com</a></p>
<hr>
<p><small>If this isn't relevant, just reply "unsubscribe" and I won't follow up.</small></p>
"""

def _subject_for(store_name: str) -> str:
    return f'Premium puzzles & card games for {store_name} (Low MOQ / DDP)'

BODY_TEXT = """Hi {greeting},

I'm Ian from rokt&razo. We are a puzzle and family card game brand with 10+ years of experience in product development, manufacturing, and custom production. In addition to our own branded products, we also support many U.S. brands and independent artists with custom production.

We are currently expanding our U.S. retail and distributor network, and I wanted to see if there may be an opportunity to work together. We offer:

- Low MOQs and DDP pricing for rokt&razo branded products
- Premium jigsaw puzzles and family card games
- Custom and private-label production options
- Supply chain support to help improve cost, quality, and production efficiency

If you're interested, I'd be happy to send over our latest catalogue, including very unique 24-in-1 puzzle series, which has received very positive customer feedback.

If you also have your own branded products, we'd be happy to discuss custom production opportunities as well.

{signature}
"""

BODY_HTML = """<p>Hi {greeting},</p>

<p>I'm Ian from <strong>rokt&amp;razo</strong>. We are a puzzle and family card game brand with 10+ years of experience in product development, manufacturing, and custom production. In addition to our own branded products, we also support many U.S. brands and independent artists with custom production.</p>

<p>We are currently expanding our U.S. retail and distributor network, and I wanted to see if there may be an opportunity to work together. We offer:</p>

<ul>
<li>Low MOQs and DDP pricing for rokt&amp;razo branded products</li>
<li>Premium jigsaw puzzles and family card games</li>
<li>Custom and private-label production options</li>
<li>Supply chain support to help improve cost, quality, and production efficiency</li>
</ul>

<p>If you're interested, I'd be happy to send over our latest catalogue, including very unique 24-in-1 puzzle series, which has received very positive customer feedback.</p>

<p>If you also have your own branded products, we'd be happy to discuss custom production opportunities as well.</p>

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
    """Generate email content for a lead using V5 template."""
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
        "template_key": "premium_puzzles_card_games_v5",
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
