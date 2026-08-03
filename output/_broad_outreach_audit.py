"""Broad Outreach Ready Reclassification — 2026-07-29 16:32 CST — Read-Only"""
import sqlite3, re
from collections import defaultdict

DB = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\data\bd_leads.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

def s(v): return str(v) if v is not None else 'NULL'

# ═══════════════════════════════════
# 1. Business category matching
# ═══════════════════════════════════
BUSINESS_CATEGORIES = {
    'toy_store', 'game_store', 'board_game_store', 'puzzle_store',
    'card_game_store', 'bookstore', 'gift_shop', 'museum_store',
    'visitor_center_store', 'educational_store', 'teacher_supply',
    'childrens_store', 'hobby_store', 'comic_store',
    'local_specialty_retailer', 'independent_retailer',
    'institution', 'original_product_brand', 'custom_product_opportunity',
}

# Map DB fields to categories
def match_business_category(lead):
    """Check if lead matches any relevant business category."""
    store_type = (lead.get('store_type') or '').lower()
    product_fit = (lead.get('product_fit') or '').lower()
    store_name = (lead.get('store_name') or '').lower()
    notes = (lead.get('notes') or '').lower()
    source_keyword = (lead.get('source_keyword') or '').lower()
    fit_reason = (lead.get('fit_reason') or '').lower()
    
    matched = []
    
    # Keyword-based matching
    keyword_map = {
        'toy_store': ['toy', 'toys'],
        'game_store': ['game store', 'game shop', 'gaming store'],
        'board_game_store': ['board game', 'boardgame'],
        'puzzle_store': ['puzzle'],
        'card_game_store': ['card game', 'trading card', 'tcg', 'ccg'],
        'bookstore': ['bookstore', 'book store', 'book shop', 'bookseller', 'bookshop'],
        'gift_shop': ['gift shop', 'gift store', 'gift boutique'],
        'museum_store': ['museum store', 'museum shop', 'museum gift'],
        'visitor_center_store': ['visitor center', 'visitor centre', 'national park store'],
        'educational_store': ['educational', 'teacher supply', 'learning store'],
        'teacher_supply': ['teacher supply', 'teaching supply'],
        'childrens_store': ['children', 'kids store', 'toy store'],
        'hobby_store': ['hobby', 'hobbies', 'model shop'],
        'comic_store': ['comic', 'comics'],
        'local_specialty_retailer': ['specialty', 'local store', 'local shop', 'general store', 'country store', 'mercantile'],
        'independent_retailer': ['independent', 'family owned', 'small business'],
    }
    
    # Also check product_fit field
    fit_category_map = {
        'puzzles': ['puzzles', 'puzzle'],
        'games': ['games', 'board game', 'card game', 'game'],
        'both': ['puzzles', 'games', 'board game', 'card game', 'game', 'puzzle'],
        'toys': ['toy', 'toys'],
        'gifts': ['gift'],
        'books': ['book'],
        'comics': ['comic'],
        'hobby': ['hobby'],
        'education': ['education', 'educational'],
    }
    
    # Check product_fit
    for cat, keywords in fit_category_map.items():
        if any(kw in product_fit for kw in keywords):
            matched.append(cat)
    
    # Check store_type
    for cat, keywords in keyword_map.items():
        if any(kw in store_type for kw in keywords):
            if cat not in matched:
                matched.append(cat)
    
    # Check broader text fields
    all_text = f"{store_name} {notes} {source_keyword} {fit_reason}"
    for cat, keywords in keyword_map.items():
        if any(kw in all_text for kw in keywords):
            if cat not in matched:
                matched.append(cat)
    
    # Fallback: if product_fit is 'both', that's games+toys by default
    if not matched and product_fit in ('both', 'puzzles_games'):
        matched.append('game_store')
        matched.append('puzzle_store')
    
    return matched

# Service opportunity matching
SERVICE_OPPORTUNITIES = {
    'ready_to_stock_wholesale', 'puzzles', 'family_card_games',
    'private_label', 'custom_cards', 'custom_puzzles',
    'printing', 'packaging', 'oem', 'production_support',
}

def match_service_opportunity(lead):
    """Check if rokt&razo has at least one service opportunity for this lead."""
    product_fit = (lead.get('product_fit') or '').lower()
    store_type = (lead.get('store_type') or '').lower()
    notes = (lead.get('notes') or '').lower()
    fit_reason = (lead.get('fit_reason') or '').lower()
    
    matched = []
    
    # Product fit gives direct service match
    if 'puzzle' in product_fit: matched.append('puzzles')
    if 'game' in product_fit: matched.append('family_card_games')
    if 'both' in product_fit:
        matched.extend(['puzzles', 'family_card_games'])
    
    # Store type implies wholesale opportunity
    retail_types = ['toy', 'game', 'book', 'gift', 'hobby', 'comic', 'puzzle', 'educational', 'museum']
    if any(t in store_type for t in retail_types):
        matched.append('ready_to_stock_wholesale')
    
    # Notes/fit_reason may mention custom/production
    if any(w in notes + fit_reason for w in ['custom', 'private label', 'oem', 'print']):
        if 'private_label' not in matched: matched.append('private_label')
        if 'custom_cards' not in matched: matched.append('custom_cards')
        if 'custom_puzzles' not in matched: matched.append('custom_puzzles')
    
    # Default: if product_fit is 'both' or 'puzzles_games', wholesale applies
    if not matched:
        matched.append('ready_to_stock_wholesale')
    
    return matched

# ═══════════════════════════════════
# 2. Hard block sets
# ═══════════════════════════════════
suppressed_emails = set(r[0] for r in conn.execute("SELECT DISTINCT email FROM suppression_list"))
sent_emails = set(r[0] for r in conn.execute("SELECT DISTINCT email FROM send_log WHERE status='sent'"))
sent_orgs = set()
for r in conn.execute("""
    SELECT DISTINCT COALESCE(NULLIF(l.organization_key,''), 'org_'||sl.lead_id)
    FROM send_log sl JOIN leads l ON sl.lead_id=l.id WHERE sl.status='sent'
"""):
    sent_orgs.add(r[0])
# Legacy sends with NULL message_type
for r in conn.execute("""
    SELECT DISTINCT COALESCE(NULLIF(l.organization_key,''), 'org_'||sl.lead_id)
    FROM send_log sl JOIN leads l ON sl.lead_id=l.id 
    WHERE sl.status='sent' AND (sl.message_type IS NULL OR sl.message_type='')
"""):
    sent_orgs.add(r[0])

replied_leads = set(r[0] for r in conn.execute("SELECT DISTINCT lead_id FROM reply_log"))
bounced_leads = set(r[0] for r in conn.execute("SELECT DISTINCT lead_id FROM bounce_log WHERE bounce_type='hard'"))
bounced_emails = set(r[0] for r in conn.execute("SELECT DISTINCT email FROM bounce_log WHERE bounce_type='hard'"))
test_patterns = ['test@', 'example@', 'noreply@', 'no-reply@']
sentry_pattern = re.compile(r'^[a-f0-9]{32,}@sentry\.io$', re.I)
# Image filename patterns in emails
image_email_pattern = re.compile(r'\.(png|jpg|jpeg|gif|webp|svg|bmp)', re.I)
hash_email_pattern = re.compile(r'^[a-f0-9]{20,}@', re.I)
placeholder_pattern = re.compile(r'^xxx@|@xxx\.|@example\.com|noreply@|no-reply@', re.I)
dimension_pattern = re.compile(r'\d+x\d+', re.I)  # image dimensions like 60x60 in email

# ═══════════════════════════════════
# 3. Organization key fallback
# ═══════════════════════════════════
def generate_org_key(lead):
    """Generate stable fallback organization_key."""
    # Priority: official domain → normalized name → name+city+state
    website = (lead.get('official_website') or '').strip()
    name = (lead.get('store_name') or '').strip()
    city = (lead.get('city') or '').strip()
    state = (lead.get('state') or '').strip()
    
    if website:
        # Extract domain
        import re as _re
        m = _re.search(r'https?://(?:www\.)?([^/]+)', website)
        if m:
            domain = m.group(1).lower().replace('.', '_').replace('-', '_')
            return domain
    
    if name:
        normalized = name.lower().replace(' ', '_').replace("'", '').replace('&', 'and')
        normalized = _re.sub(r'[^a-z0-9_]', '', normalized)
        if normalized:
            return normalized
    
    if city and state:
        raw = f"{name}_{city}_{state}".lower().replace(' ', '_')
        raw = _re.sub(r'[^a-z0-9_]', '', raw)
        return raw
    
    return f"org_{lead.get('id', 'unknown')}"

# ═══════════════════════════════════
# 4. Main classification loop
# ═══════════════════════════════════
leads = conn.execute("""
    SELECT * FROM leads WHERE status NOT IN ('sent', 'bounced', 'delivery_issue', 'failed', 'do_not_contact')
    ORDER BY id
""").fetchall()

print(f'Total active leads: {len(leads)}')

stats = {
    'strict_a0': [],
    'broad_ready': [],
    'exception_review': [],
    'contact_recovery': [],
    'contact_form_only': [],
    'permanently_blocked': [],
    'previously_sent': [],
}

broad_org_keys = set()
a0_org_keys = set()

for row in leads:
    lead = dict(row)
    lid = lead['id']
    email = (lead.get('email') or '').strip().lower()
    name = lead.get('store_name', '')
    status = lead.get('status', '')
    score = lead.get('confidence_score', '')
    auto = lead.get('auto_sendable')
    org_key = (lead.get('organization_key') or '').strip()
    website = (lead.get('official_website') or '').strip()
    ev_url = (lead.get('evidence_url') or '').strip()
    ev_snip = (lead.get('evidence_snippet') or '').strip()
    city = lead.get('city', '')
    state_ = lead.get('state', '')
    src = (lead.get('email_source_type') or '').strip()
    notes = lead.get('notes', '') or ''
    
    # === HARD BLOCKS ===
    hard_block = None
    
    if status == 'contact_form_pool' or src == 'contact_form' or src == 'contact_form_only':
        stats['contact_form_only'].append({'lid': lid, 'name': name, 'reason': 'contact_form_only'})
        continue
    
    if not email or '@' not in email:
        stats['contact_recovery'].append({'lid': lid, 'name': name, 'reason': 'no_email'})
        continue
    
    if image_email_pattern.search(email) or dimension_pattern.search(email):
        stats['permanently_blocked'].append({'lid': lid, 'name': name, 'reason': f'image_email:{email[:40]}'})
        continue
    
    if placeholder_pattern.search(email):
        stats['permanently_blocked'].append({'lid': lid, 'name': name, 'reason': f'placeholder_email:{email[:40]}'})
        continue
    
    if sentry_pattern.match(email):
        stats['permanently_blocked'].append({'lid': lid, 'name': name, 'reason': f'sentry_email:{email[:40]}'})
        continue
    
    if hash_email_pattern.match(email):
        stats['permanently_blocked'].append({'lid': lid, 'name': name, 'reason': f'hash_email:{email[:40]}'})
        continue
    
    if any(p in email for p in test_patterns):
        stats['permanently_blocked'].append({'lid': lid, 'name': name, 'reason': f'test_email:{email}'})
        continue
    
    if email in suppressed_emails:
        stats['permanently_blocked'].append({'lid': lid, 'name': name, 'reason': 'suppressed'})
        continue
    
    if email in sent_emails:
        stats['previously_sent'].append({'lid': lid, 'name': name, 'reason': 'email_previously_sent'})
        continue
    
    if lid in replied_leads:
        stats['permanently_blocked'].append({'lid': lid, 'name': name, 'reason': 'replied'})
        continue
    
    if lid in bounced_leads or email in bounced_emails:
        stats['permanently_blocked'].append({'lid': lid, 'name': name, 'reason': 'hard_bounced'})
        continue
    
    if status in ('rejected', 'deferred', 'recheck_pending'):
        stats['permanently_blocked'].append({'lid': lid, 'name': name, 'reason': f'status:{status}'})
        continue
    
    # === Check if Strict A0 ===
    is_a0 = (status == 'new' and score == 'A' and auto == 1 
             and org_key and website and ev_url and ev_snip
             and email and '@' in email)
    
    if is_a0:
        final_org = org_key
        a0_org_keys.add(final_org)
        stats['strict_a0'].append({
            'lid': lid, 'name': name, 'email': email, 'org_key': final_org,
            'city': city, 'state': state_, 'website': website,
            'broad_fit': match_business_category(lead),
            'broad_service': match_service_opportunity(lead),
            'src': src,
        })
        continue
    
    # === Check Broad Outreach Ready ===
    business_cats = match_business_category(lead)
    services = match_service_opportunity(lead)
    
    if not business_cats:
        stats['exception_review'].append({'lid': lid, 'name': name, 'reason': 'no_business_category_match', 'email': email})
        continue
    
    if not services:
        stats['exception_review'].append({'lid': lid, 'name': name, 'reason': 'no_service_opportunity', 'email': email})
        continue
    
    # Auto-generate org_key if missing
    final_org = org_key if org_key else generate_org_key(lead)
    
    # Check org-level history
    if final_org in sent_orgs:
        stats['previously_sent'].append({'lid': lid, 'name': name, 'reason': 'org_previously_sent', 'org': final_org})
        continue
    
    # Passed all gates!
    broad_org_keys.add(final_org)
    stats['broad_ready'].append({
        'lid': lid, 'name': name, 'email': email, 'org_key': final_org,
        'city': city, 'state': state_, 'website': website,
        'broad_fit': business_cats,
        'broad_service': services,
        'src': src,
        'auto_generated_org': not bool(org_key),
        'was_contact_role_uncertain': 'CONTACT_ROLE_UNCERTAIN' in notes.upper() or 'ROLE' in notes.upper(),
        'score': score, 'auto': auto,
    })

# ═══════════════════════════════════
# 5. Deduplicate by org for opportunities
# ═══════════════════════════════════
broad_opps = []
seen = set()
for entry in stats['broad_ready']:
    if entry['org_key'] not in seen:
        seen.add(entry['org_key'])
        broad_opps.append(entry)

# ═══════════════════════════════════
# 6. Output
# ═══════════════════════════════════
sep = '=' * 70
print(f'\n{sep}')
print('BROAD OUTREACH READY — FINAL REPORT')
print(sep)

print(f'\n  1. Strict A0 Organizations:                         {len(a0_org_keys)}')
print(f'  2. Broad Outreach Ready Organizations:              {len(broad_org_keys)}')
print(f'  3. Broad Organization Outreach Opportunities:       {len(broad_opps)}')

# Count CONTACT_ROLE_UNCERTAIN
cru_count = sum(1 for e in stats['broad_ready'] if e.get('was_contact_role_uncertain'))
print(f'  4. Previously blocked by CONTACT_ROLE_UNCERTAIN:    {cru_count}')

# Count auto-generated org_keys
auto_org = sum(1 for e in stats['broad_ready'] if e.get('auto_generated_org'))
print(f'  5. Auto-generated organization keys:                {auto_org}')

invalid_email_count = sum(1 for e in stats['contact_recovery'] if 'no_email' in e.get('reason',''))
image_email_count = sum(1 for e in stats['permanently_blocked'] if 'image_email' in e.get('reason','') or 'hash_email' in e.get('reason','') or 'placeholder' in e.get('reason',''))
print(f'  6. Invalid email excluded:                          {invalid_email_count + image_email_count}')

prev_sent = len(stats['previously_sent'])
print(f'  7. Previously Sent excluded:                        {prev_sent}')

perm_block = len(stats['permanently_blocked'])
print(f'  8. Permanent Block excluded:                        {perm_block}')

cfo = len(stats['contact_form_only'])
print(f'  9. Contact Form Only:                               {cfo}')

max_tonight = len(broad_opps) + len(stats['strict_a0'])
print(f' 10. Tonight max New Outreach:                        {max_tonight}')

meets_60 = 'YES' if max_tonight >= 60 else f'NO (gap: {60 - max_tonight})'
print(f' 11. Meets 60 target:                                 {meets_60}')

print(f' 12. send_log unchanged:                              ✅ (read-only audit)')
print(f' 13. Final Send Plan NOT created:                     ✅')
print(f' 14. SMTP NOT called:                                 ✅')

# Exception review breakdown
print(f'\n--- Exception Review: {len(stats["exception_review"])} ---')
er_reasons = defaultdict(int)
for e in stats['exception_review']:
    er_reasons[e['reason']] += 1
for reason, count in sorted(er_reasons.items(), key=lambda x: -x[1]):
    print(f'  {reason}: {count}')

# Broad opportunities list (first 50)
print(f'\n--- Broad Organization Outreach Opportunities ({len(broad_opps)}) ---')
print(f'{"#":>3} {"lead_id":>7} {"Store":30s} {"City":12s} {"ST":3s} {"Org Key":25s} {"Email":35s} {"Fit":15s}')
print('-' * 135)
for i, opp in enumerate(broad_opps[:50]):
    fit_str = ','.join(opp['broad_fit'][:2])[:15]
    print(f'{i+1:3d} {opp["lid"]:7d} {opp["name"][:30]:30s} {opp["city"][:12]:12s} {opp["state"]:3s} {opp["org_key"][:25]:25s} {opp["email"][:35]:35s} {fit_str}')
if len(broad_opps) > 50:
    print(f'  ... and {len(broad_opps) - 50} more')

# Strict A0 list
print(f'\n--- Strict A0 Organizations ({len(stats["strict_a0"])}) ---')
for opp in stats['strict_a0']:
    print(f'  id={opp["lid"]:3d} {opp["name"][:30]:30s} {opp["org_key"][:30]:30s} {opp["email"][:35]}')

conn.close()
print(f'\n{sep}')
print('AUDIT COMPLETE — Read-only, no DB changes')
print(sep)
