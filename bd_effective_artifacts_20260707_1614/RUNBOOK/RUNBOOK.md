# RUNBOOK.md

> **Codex Handoff — Execution Runbook**
> 本次任务: 修复 Message-ID header 缺失

---

## 1. Pre-Flight Checklist

- [ ] 确认只读审计生产目录，不修改任何文件
- [ ] 确认不复制 `.env`、`data/bd_leads.db`、cookies、profile
- [ ] 确认不跑 live send、不跑采集、不改数据库
- [ ] 确认不注册 automation 任务

---

## 2. Step-by-Step Fix Plan

### Step 1: Read and Understand `_build_email()`

**File**: `roktandrazo-outreach/bd_sender.py` lines 31-44

```python
def _build_email(to_email: str, subject: str, body_text: str, body_html: str = None) -> MIMEMultipart:
    sender = get_sender_info()
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((sender["name"], sender["email"]))
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Reply-To"] = sender["email"]
    # ← NO Message-ID set here
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    if body_html:
        msg.attach(MIMEText(body_html, "html", "utf-8"))
    return msg
```

**Issue**: Python `MIMEMultipart` does NOT auto-generate `Message-ID`.
Without it, some receiving servers (especially Microsoft 365) reject the message.

### Step 2: Add Message-ID

Add import at top of `bd_sender.py`:

```python
from email.utils import make_msgid
```

Add one line in `_build_email()` after `msg["Reply-To"]`:

```python
msg["Message-ID"] = make_msgid(domain="roktandrazo.com")
```

The `domain="roktandrazo.com"` parameter ensures the Message-ID uses our sending domain,
not localhost or a random hostname.

### Step 3: Fix Bounce Classification

**File**: `roktandrazo-outreach/agent_bounce_auditor.py`

Current `classify_bounce()` function (lines 25-50):

```python
def classify_bounce(status_code, diagnostic_code, body):
    # ...
    if any(x in sc for x in ['5.4.1', '5.7.1']) or \
       any(x in dc or x in bt for x in ['access denied', 'relaying denied',
                                          'rejected by policy', 'blocked', ...]):
        return 'policy', 'Receiving server policy rejection'
    # ...
```

**Problem**: Message-ID missing bounces get classified as `policy`.
But they should NOT trigger suppression.

**Fix**: Add a new subtype check BEFORE the generic `policy` check:

```python
# NEW: Message-ID missing bounce — NOT a hard bounce, NOT to be suppressed
if any(x in dc or x in bt for x in ['message-id', 'missing message-id',
                                      'malformed message-id',
                                      'missing required headers']):
    return 'message_id_missing', 'Message-ID header missing — fix sender, do NOT suppress'
```

This must come BEFORE the generic `policy` check so it gets classified first.

### Step 4: Fix Suppression Logic in `daily_session.py`

**File**: `roktandrazo-outreach/daily_session.py` lines 233-242

Current logic in `scan_bounce_and_reply()`:

```python
if b.get('type') == 'hard':
    result['hard_bounces'].append(b)
    email = b.get('email', '')
    if email:
        add_to_suppression(email, 'hard_bounce')  # ← auto-suppress
elif b.get('type') == 'policy':
    result['policy_bounces'].append(b)
```

**Current behavior**:
- `hard` → auto-suppress ✅
- `policy` → counted but NOT auto-suppressed ✅

**But**: If Message-ID bounce is misclassified as `hard` (e.g. 550 status code),
it WILL be auto-suppressed. This is the real risk.

**Fix**: After adding the `message_id_missing` subtype in Step 3,
add explicit handling:

```python
if b.get('type') == 'message_id_missing':
    # Do NOT suppress — this is a sender-side technical issue
    result['policy_bounces'].append(b)
    print(f"    [MESSAGE-ID] {b.get('email')}: bounce due to missing Message-ID — NOT suppressed")
elif b.get('type') == 'hard':
    ...
```

### Step 5: Verify Fix with Dry-Run

```bash
# From roktandrazo-outreach/ directory
python daily_session.py --dry-run
```

Verify:
- `_build_email()` generates Message-ID
- No real emails sent
- Template safety checks pass

### Step 6: Add Unit Test (Optional but Recommended)

Create test to verify Message-ID exists in constructed emails:

```python
def test_build_email_has_message_id():
    from bd_sender import _build_email
    msg = _build_email("test@example.com", "Test Subject", "Test body")
    assert msg["Message-ID"], "Message-ID header must be present"
    assert "@roktandrazo.com" in msg["Message-ID"], "Message-ID must use roktandrazo.com domain"
```

---

## 3. Files to Modify (Summary)

| File | Change | Risk |
|------|--------|------|
| `bd_sender.py` | Add `make_msgid` import + one line in `_build_email()` | LOW |
| `agent_bounce_auditor.py` | Add `message_id_missing` subtype before `policy` check | LOW |
| `daily_session.py` | Add explicit handling for `message_id_missing` type | LOW |

Total: **3 files, ~10 lines of code**.

---

## 4. Rollback Plan

All changes are additive. If something breaks:

1. `git diff` to see changes (if git initialized)
2. Or manually revert the 3 edits
3. No database schema changes needed
4. No config changes needed

---

## 5. Post-Fix Verification

After fix, send 1 test email to yourself:

```bash
# Set BD_TEST_MODE=true in .env, BD_TEST_EMAIL=your@email.com
python daily_session.py --live --force --target-count 1
```

Check the received email headers for:
```
Message-ID: <unique-id@roktandrazo.com>
```

---

## 6. Known Edge Cases

1. **腾讯企业邮箱可能自动补 Message-ID**: Some SMTP servers add Message-ID if missing.
   The fix is still necessary because:
   - Not all servers do this
   - The auto-added one may use wrong domain
   - Best practice is to set it on the client side

2. **`_save_to_sent()` saves the msg object**: The Message-ID will be present in the
   IMAP-stored copy because it's set before `as_bytes()` is called.

3. **BCC-to-self**: `server.sendmail(sender_email, [actual_to, sender_email], msg.as_string())`
   The BCC copy will also have the correct Message-ID.
