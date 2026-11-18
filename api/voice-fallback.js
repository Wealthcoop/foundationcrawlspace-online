// Vercel Serverless Function: Unanswered Call Fallback for foundationcrawlspace.online

const TELNYX_API_KEY = process.env.TELNYX_API_KEY || "";
const TELNYX_PROFILE_ID = process.env.TELNYX_PROFILE_ID || "4001a183-adf9-4171-a62a-8528cd76a274";
const TELNYX_FROM = process.env.TELNYX_FROM || "+19168849689";
const ALERT_PHONE = process.env.ALERT_PHONE || "+15309010353";

function normalizePhone(phone) {
  const digits = String(phone || "").replace(/\D/g, "");
  if (digits.length === 10) return `+1${digits}`;
  if (digits.length === 11 && digits.startsWith("1")) return `+${digits}`;
  return String(phone || "").startsWith("+") ? `+${digits}` : "";
}

async function sendSms(toNumber, text) {
  const to = normalizePhone(toNumber);
  if (!to || !TELNYX_API_KEY) return;
  try {
    await fetch("https://api.telnyx.com/v2/messages", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${TELNYX_API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        from: TELNYX_FROM,
        to,
        text,
        messaging_profile_id: TELNYX_PROFILE_ID
      })
    });
  } catch (err) {
    console.error("Fallback SMS failed:", err.message);
  }
}

export default async function handler(req, res) {
  res.setHeader("Content-Type", "application/xml; charset=utf-8");
  res.setHeader("Cache-Control", "no-cache, no-store, must-revalidate");

  let body = req.body || {};
  if (typeof body === "string") {
    try {
      body = JSON.parse(body);
    } catch (e) {
      body = Object.fromEntries(new URLSearchParams(body).entries());
    }
  }

  const dialStatus = body.DialCallStatus || req.query.DialCallStatus || "";
  const callerPhone = body.From || req.query.From || body.Caller || req.query.Caller || "";

  if (dialStatus === "completed" || dialStatus === "answered") {
    return res.status(200).send(`<?xml version="1.0" encoding="UTF-8"?>\n<Response></Response>`);
  }

  if (callerPhone) {
    await Promise.allSettled([
      sendSms(
        ALERT_PHONE,
        `[foundationcrawlspace.online] MISSED CALL ALERT\nCaller: ${callerPhone}\nSent missed-call text-back automatically.`
      ),
      sendSms(
        callerPhone,
        "Thanks for calling Foundation & Crawlspace Directory (foundationcrawlspace.online). Sorry we missed your call. Reply here with your city and what you need checked (foundation cracks, crawlspace moisture, or yard drainage) and we will connect you right away."
      )
    ]);
  }

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="alice">Thanks for calling the Foundation and Crawlspace Directory. Please leave your name, city, and project details after the tone, or reply to the text message we just sent you.</Say>
  <Record maxLength="90" playBeep="true" />
</Response>`;

  return res.status(200).send(xml);
}
