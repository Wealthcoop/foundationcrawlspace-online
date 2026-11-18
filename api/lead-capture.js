// Vercel Serverless Function: foundationcrawlspace.online Lead & Claim Alert Router
// Sends SMS from Telnyx (916) 884-9689 to Justin at (530) 901-0353 + email to goldstandardaiagency@gmail.com
// Includes anti-bot honeypot, fill-timing, IP rate limiting, and mixed-case gibberish blocking.

const TELNYX_API_KEY = process.env.TELNYX_API_KEY || "";
const TELNYX_PROFILE_ID = process.env.TELNYX_PROFILE_ID || "4001a183-adf9-4171-a62a-8528cd76a274";
const TELNYX_FROM = process.env.TELNYX_FROM || "+19168849689";
const ALERT_PHONE = process.env.ALERT_PHONE || "+15309010353";
const RESEND_API_KEY = process.env.RESEND_API_KEY || "";
const ALERT_EMAIL = process.env.ALERT_EMAIL || "goldstandardaiagency@gmail.com";
const SITE_LABEL = "foundationcrawlspace.online";

const RATE_WINDOW_MS = 15 * 60 * 1000;
const RATE_MAX_HITS = 3;
const recentIpHits = new Map();

function isRateLimited(req) {
  const fwd = String((req.headers && req.headers["x-forwarded-for"]) || "");
  const ip = (fwd.split(",")[0] || (req.socket && req.socket.remoteAddress) || "").trim();
  if (!ip) return false;
  const now = Date.now();
  const hits = (recentIpHits.get(ip) || []).filter((ts) => now - ts < RATE_WINDOW_MS);
  if (hits.length >= RATE_MAX_HITS) {
    recentIpHits.set(ip, hits);
    return true;
  }
  hits.push(now);
  recentIpHits.set(ip, hits);
  return false;
}

function normalizePhone(phone) {
  if (!phone) return "";
  const digits = String(phone).replace(/\D/g, "");
  if (digits.length === 10) return `+1${digits}`;
  if (digits.length === 11 && digits.startsWith("1")) return `+${digits}`;
  if (String(phone).startsWith("+") && digits.length >= 10) return `+${digits}`;
  return "";
}

function isValidNanpPhone(phone) {
  if (!phone) return false;
  const digits = String(phone).replace(/\D/g, "");
  const national = (digits.length === 11 && digits.startsWith("1")) ? digits.slice(1) : digits;
  if (national.length !== 10) return false;
  const areaCode = national.slice(0, 3);
  const centralOffice = national.slice(3, 6);
  if (areaCode[0] === "0" || areaCode[0] === "1") return false;
  if (areaCode[1] === "1" && areaCode[2] === "1") return false;
  if (centralOffice[0] === "0" || centralOffice[0] === "1") return false;
  if (/^(\d)\1{9}$/.test(national)) return false;
  if (national === "1234567890" || national === "9876543210") return false;
  return true;
}

function isValidEmail(email) {
  if (!email || typeof email !== "string") return false;
  return /^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$/.test(email.trim());
}

const RARE_BIGRAMS_RE = /(?:bx|cj|cx|dx|fq|fx|gq|gx|hx|jc|jf|jg|jq|jv|jx|jz|kq|kv|kx|kz|lq|lx|mx|px|pz|qb|qc|qd|qf|qg|qh|qj|qk|ql|qm|qn|qp|qq|qr|qs|qt|qv|qw|qx|qy|qz|sx|tq|tx|vb|vf|vg|vh|vj|vk|vm|vp|vq|vt|vx|vz|wq|wx|wz|xb|xj|xk|xq|xz|yq|yy|zb|zd|zf|zg|zj|zk|zp|zq|zr|zv|zx|zz)/gi;
const CONSONANT_RUN_5_RE = /[bcdfghjklmnpqrstvwxz]{5,}/i;
const CONSONANT_RUN_4_RE = /[bcdfghjklmnpqrstvwxz]{4,}/i;
const SAFE_SHORT_WORDS = new Set([
  "llc", "inc", "corp", "co", "dba", "hvac", "plumbing", "foundation",
  "crawlspace", "drainage", "french", "drain", "sump", "vapor", "barrier",
  "ca", "sac", "usa", "dr", "st", "ste", "mr", "ms", "jr", "sr", "and", "the"
]);

function wordSpamScore(word) {
  const clean = word.replace(/[^a-zA-Z]/g, "");
  if (!clean || clean.length < 4) return 0;
  const lower = clean.toLowerCase();
  if (SAFE_SHORT_WORDS.has(lower)) return 0;

  let score = 0;
  const lowerToUpper = (clean.match(/[a-z][A-Z]/g) || []).length;
  const upperToLower = (clean.slice(1).match(/[A-Z][a-z]/g) || []).length;
  if (lowerToUpper >= 3 || (lowerToUpper >= 2 && upperToLower >= 3)) return 5;
  if (/^([bcdfghjkmnpqrstvwxz])\1/i.test(lower)) score += 3;

  const rareHits = (lower.match(RARE_BIGRAMS_RE) || []).length;
  if (rareHits >= 2) score += 4;
  else if (rareHits === 1 && clean.length >= 5) score += 2;

  const norm = lower.replace(/sch|tch/g, "sh");
  const vowelCount = (lower.match(/[aeiouy]/g) || []).length;
  if (clean.length >= 5 && vowelCount === 0) return 5;
  if (CONSONANT_RUN_5_RE.test(norm) && vowelCount <= 2) score += 3;
  else if (CONSONANT_RUN_4_RE.test(norm) && clean.length <= 10 && vowelCount <= 1) score += 2;
  if (clean.length >= 10 && vowelCount / clean.length < 0.18) score += 3;
  return score;
}

function isGibberishText(value) {
  const text = String(value || "").trim();
  if (!text) return false;
  const tokens = text.split(/[\s\-_/|,]+/).filter(Boolean);
  let total = 0;
  for (const tok of tokens) {
    const s = wordSpamScore(tok);
    if (s >= 4) return true;
    total += s;
  }
  return total >= 4;
}

async function sendTelnyxSms(toNumber, text) {
  const cleanTo = normalizePhone(toNumber);
  if (!cleanTo || !TELNYX_API_KEY) return { ok: false, skipped: true };
  try {
    const res = await fetch("https://api.telnyx.com/v2/messages", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${TELNYX_API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        from: TELNYX_FROM,
        to: cleanTo,
        text: text,
        messaging_profile_id: TELNYX_PROFILE_ID
      })
    });
    const data = await res.json();
    return { ok: res.ok, data };
  } catch (err) {
    return { ok: false, error: err.message };
  }
}

async function sendResendEmail(payload) {
  if (!RESEND_API_KEY) return { ok: false, skipped: true };
  const leadTypeLabel = payload.leadType === "claim"
    ? "CONTRACTOR CLAIM"
    : payload.leadType === "featured"
      ? "FEATURED SLOT INQUIRY"
      : "HOMEOWNER QUOTE LEAD";

  const subject = `[${SITE_LABEL}] ${leadTypeLabel}: ${payload.name || payload.company || "New Inquiry"} (${payload.city || "Greater Sacramento"})`;

  const html = `
    <div style="font-family: Arial, sans-serif; max-width: 620px; color: #0f172a; line-height: 1.55;">
      <div style="background: #0b2545; color: #ffffff; padding: 14px 18px; border-radius: 8px 8px 0 0;">
        <strong>Source Site:</strong> ${SITE_LABEL} (${leadTypeLabel})
      </div>
      <div style="border: 1px solid #cbd5e1; border-top: 0; padding: 18px; border-radius: 0 0 8px 8px;">
        <p><strong>Name:</strong> ${escapeHtml(payload.name || "Not provided")}</p>
        ${payload.company ? `<p><strong>Company:</strong> ${escapeHtml(payload.company)}</p>` : ""}
        <p><strong>Phone:</strong> <a href="tel:${escapeHtml(payload.phone)}">${escapeHtml(payload.phone || "Not provided")}</a></p>
        <p><strong>Email:</strong> ${escapeHtml(payload.email || "Not provided")}</p>
        <p><strong>City / ZIP:</strong> ${escapeHtml(payload.city || "Not provided")}</p>
        <p><strong>Service / Issue:</strong> ${escapeHtml(payload.service || "General Inquiry")}</p>
        ${payload.license ? `<p><strong>CSLB License #:</strong> ${escapeHtml(payload.license)}</p>` : ""}
        ${payload.targetCompany ? `<p><strong>Listed Profile Page:</strong> ${escapeHtml(payload.targetCompany)}</p>` : ""}
        ${payload.notes ? `<p><strong>Details:</strong> ${escapeHtml(payload.notes)}</p>` : ""}
        <p style="font-size: 12px; color: #64748b; margin-top: 16px;">Page URL: ${escapeHtml(payload.pageUrl || "/")}</p>
      </div>
    </div>
  `;

  try {
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${RESEND_API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        from: `Directory Alerts <jd@goldstandard.monster>`,
        reply_to: payload.email && isValidEmail(payload.email) ? payload.email : ALERT_EMAIL,
        to: [ALERT_EMAIL],
        subject,
        html
      })
    });
    const data = await res.json();
    return { ok: res.ok, data };
  } catch (err) {
    return { ok: false, error: err.message };
  }
}

function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") return res.status(200).end();
  if (req.method === "GET") {
    return res.status(200).json({ status: "active", site: SITE_LABEL });
  }
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    let body = req.body;
    if (typeof body === "string") {
      try { body = JSON.parse(body); } catch (e) { body = {}; }
    }
    body = body || {};

    // Honeypot
    if (body.website_url || body.confirm_email || body.hp_token) {
      return res.status(200).json({ status: "success", message: "Processed" });
    }

    // Timing guard
    if (body.loadedAt) {
      const elapsed = Date.now() - Number(body.loadedAt);
      if (Number.isFinite(elapsed) && elapsed >= 0 && elapsed < 1800) {
        return res.status(200).json({ status: "success", message: "Processed" });
      }
    }

    if (isRateLimited(req)) {
      return res.status(200).json({ status: "success", message: "Processed" });
    }

    const leadType = String(body.leadType || "quote").trim().toLowerCase();
    const name = String(body.name || "").trim();
    const company = String(body.company || "").trim();
    const phone = String(body.phone || "").trim();
    const email = String(body.email || "").trim().toLowerCase();
    const city = String(body.city || "").trim();
    const service = String(body.service || "").trim();
    const license = String(body.license || "").trim();
    const notes = String(body.notes || "").trim();
    const targetCompany = String(body.targetCompany || "").trim();
    const pageUrl = String(body.pageUrl || "").trim();

    if (!phone && !email) {
      return res.status(400).json({ error: "Phone or email is required" });
    }
    if (phone && !isValidNanpPhone(phone)) {
      return res.status(200).json({ status: "success", message: "Processed" });
    }
    if (email && !isValidEmail(email)) {
      return res.status(200).json({ status: "success", message: "Processed" });
    }
    if (isGibberishText(name) || isGibberishText(company) || isGibberishText(city) || isGibberishText(notes)) {
      return res.status(200).json({ status: "success", message: "Processed" });
    }

    const typeHeader = leadType === "claim"
      ? "Foundation Directory Claim:"
      : leadType === "featured"
        ? "Foundation Directory Featured:"
        : "Foundation Directory Lead:";

    const smsLines = [
      typeHeader,
      name ? `Name: ${name}` : null,
      company ? `Co: ${company}` : null,
      city ? `City: ${city}` : null,
      service ? `Need: ${service}` : null,
      phone ? `Phone: ${phone}` : null,
      email ? `Email: ${email}` : null,
      license ? `CSLB: ${license}` : null,
      targetCompany ? `Profile: ${targetCompany}` : null,
      notes ? `Note: ${notes.slice(0, 120)}` : null
    ].filter(Boolean).join("\n");

    const payload = {
      leadType, name, company, phone, email, city, service, license, notes, targetCompany, pageUrl
    };

    const [smsRes, emailRes] = await Promise.allSettled([
      sendTelnyxSms(ALERT_PHONE, smsLines),
      sendResendEmail(payload)
    ]);

    return res.status(200).json({
      status: "success",
      message: "Lead captured",
      sms: smsRes.status === "fulfilled" ? smsRes.value.ok : false,
      email: emailRes.status === "fulfilled" ? emailRes.value.ok : false
    });
  } catch (err) {
    return res.status(500).json({ error: "Server error", message: err.message });
  }
}
