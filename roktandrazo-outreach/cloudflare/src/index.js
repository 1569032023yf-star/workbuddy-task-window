/**
 * Roktandrazo Email Tracking Worker
 * Endpoints:
 *   GET /o/<token>.gif — open tracking pixel
 *   GET /healthz        — health check
 * Privacy: No cookies, no client data, IP hashed with salt before storage.
 */

const PIXEL_GIF = new Uint8Array([
  0x47,0x49,0x46,0x38,0x39,0x61,0x01,0x00,0x01,0x00,0x80,0x00,0x00,
  0xff,0xff,0xff,0x00,0x00,0x00,0x21,0xf9,0x04,0x01,0x00,0x00,0x00,
  0x00,0x2c,0x00,0x00,0x00,0x00,0x01,0x00,0x01,0x00,0x00,0x02,0x02,
  0x44,0x01,0x00,0x3b
]);

const PIXEL_HEADERS = {
  "Content-Type": "image/gif",
  "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
  "X-Content-Type-Options": "nosniff",
  "Access-Control-Allow-Origin": "*",
};

async function hashToken(token, env) {
  const encoder = new TextEncoder();
  const pepper = (env && env.TRACKING_PEPPER) ? env.TRACKING_PEPPER : "tracking-pilot-20260728";
  const key = await crypto.subtle.importKey(
    "raw", encoder.encode(pepper),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, encoder.encode(token));
  return Array.from(new Uint8Array(sig)).map(b => b.toString(16).padStart(2,"0")).join("");
}

async function hashIP(ip, env) {
  const salt = (env && env.TRACKING_IP_SALT) ? env.TRACKING_IP_SALT : "roktandrazo-tracking-salt";
  const encoder = new TextEncoder();
  const data = encoder.encode(salt + (ip || ""));
  const hash = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2,"0")).join("").slice(0, 24);
}

function classifySource(userAgent) {
  const ua = (userAgent || "").toLowerCase();
  // WeChat Work / WeCom mail client — common on Windows in China
  if (/wxwork|wecom|mailplugin/.test(ua)) return "wechat_work_mail_client";
  // Apple Mail Privacy Protection: only match actual Apple Mail user agents
  if (/(?:apple.*mail|mail.*apple|mac.*mail|iphone.*mail|ipad.*mail|cfnetwork.*darwin)/.test(ua)) return "likely_apple_mpp";
  if (/googleimageproxy|google-proxy/.test(ua)) return "likely_google_proxy";
  if (/security|scanner|curl|wget|python-requests|go-http-client|axios|node-fetch|java|bot|spider|crawler/.test(ua)) return "likely_security_scanner";
  return "direct_or_unknown";
}

async function servePixel() {
  return new Response(PIXEL_GIF, { status: 200, headers: PIXEL_HEADERS });
}

async function handleOpen(request, env, ctx, token) {
  const tokenHash = await hashToken(token, env);
  const userAgent = request.headers.get("User-Agent") || "";
  const ip = request.headers.get("CF-Connecting-IP") || request.headers.get("X-Forwarded-For") || "";
  const ipHash = await hashIP(ip, env);
  const classification = classifySource(userAgent);
  const now = new Date().toISOString();
  const dedupeKey = `open:${tokenHash}:${classification}:${userAgent.slice(0, 40)}`;

  try {
    // Look up tracking message
    const msg = await env.DB.prepare(
      "SELECT id, status FROM tracking_messages WHERE token_hash = ? AND status = 'active' LIMIT 1"
    ).bind(tokenHash).first();

    if (msg) {
      // Write event with dedup
      await env.DB.prepare(
        `INSERT OR IGNORE INTO tracking_events (tracking_message_id, event_type, event_at, source_classification, user_agent_family, ip_hash, dedupe_key)
         VALUES (?, 'open_signal', ?, ?, ?, ?, ?)`
      ).bind(msg.id, now, classification, userAgent.slice(0, 200), ipHash, dedupeKey).run();

      // Update message stats
      await env.DB.prepare(
        "UPDATE tracking_messages SET first_open_signal_at = COALESCE(first_open_signal_at, ?), last_open_signal_at = ?, open_signal_count = open_signal_count + 1 WHERE id = ?"
      ).bind(now, now, msg.id).run();
    }
  } catch (e) {
    // DB errors must not prevent pixel delivery
  }

  return servePixel();
}

async function handleHealthz() {
  return new Response(JSON.stringify({ status: "ok", service: "roktandrazo-email-tracker" }), {
    status: 200,
    headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
  });
}

function checkAuth(request, env) {
  const auth = request.headers.get("Authorization") || "";
  const token = auth.replace(/^Bearer\s+/i, "").trim();
  const expected = env.DASHBOARD_API_KEY;
  if (!expected) {
    return false; // Secret not configured — deny all
  }
  return token === expected;
}

async function handleMXCheck(request, env) {
  if (!checkAuth(request, env)) {
    return new Response(JSON.stringify({ error: "unauthorized" }), { status: 401,
      headers: { "Content-Type": "application/json" } });
  }
  try {
    const body = await request.json();
    const domain = (body.domain || "").toLowerCase().trim().replace(/\/+$/, "");
    if (!domain || !/^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$/.test(domain)) {
      return new Response(JSON.stringify({ error: "invalid_domain", domain }), { status: 400,
        headers: { "Content-Type": "application/json" } });
    }

    const results = { domain, checked_at: new Date().toISOString(), resolver: "cloudflare-doh" };

    // MX query via Cloudflare DNS-over-HTTPS
    const mxResp = await fetch(`https://cloudflare-dns.com/dns-query?name=${encodeURIComponent(domain)}&type=MX`, {
      headers: { "Accept": "application/dns-json" }
    });
    const mxData = await mxResp.json();

    if (mxData.Status === 0 && mxData.Answer && mxData.Answer.length > 0) {
      const exchanges = mxData.Answer.filter(a => a.type === 15).map(a => ({
        exchange: a.data.split(" ").slice(1).join(" "),
        preference: parseInt(a.data.split(" ")[0]),
      }));
      results.mx_status = "mx_pass";
      results.mx_records = exchanges;
    } else if (mxData.Status === 3) {
      results.mx_status = "nxdomain";
    } else {
      results.mx_status = "no_mx_found";
      // Check A/AAAA fallback
      const aResp = await fetch(`https://cloudflare-dns.com/dns-query?name=${encodeURIComponent(domain)}&type=A`, {
        headers: { "Accept": "application/dns-json" }
      });
      const aData = await aResp.json();
      if (aData.Status === 0 && aData.Answer && aData.Answer.length > 0) {
        results.mx_status = "implicit_mail_route";
        results.a_records = aData.Answer.filter(a => a.type === 1).map(a => a.data);
      } else {
        results.mx_status = "no_mail_route";
      }
    }

    results.raw_status = mxData.Status;
    return new Response(JSON.stringify(results), { status: 200,
      headers: { "Content-Type": "application/json" } });
  } catch (e) {
    return new Response(JSON.stringify({ error: "mx_check_failed", detail: e.message }), { status: 500,
      headers: { "Content-Type": "application/json" } });
  }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "");

    try {
      // GET /o/<token>.gif
      const openMatch = path.match(/^\/o\/(.+)\.gif$/);
      if (openMatch) {
        return handleOpen(request, env, ctx, openMatch[1]);
      }

      // GET /healthz
      if (path === "/healthz") {
        return handleHealthz();
      }

      // POST /internal/mx-check (Bearer auth, domain DNS check)
      if (path === "/internal/mx-check" && request.method === "POST") {
        return handleMXCheck(request, env);
      }

      // GET /internal/dashboard-summary (Bearer auth)
      if (path === "/internal/dashboard-summary") {
        return handleInternalDashboardSummary(request, env);
      }

      // Unknown path — serve pixel silently
      return servePixel();
    } catch (e) {
      return servePixel();
    }
  }
};
