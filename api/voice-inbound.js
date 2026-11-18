// Vercel Serverless Function: Inbound Call Router for (916) 884-9689 (foundationcrawlspace.online)
// Fires an instant SMS alert to (530) 901-0353 tagged [foundationcrawlspace.online] so Justin knows
// which site the caller dialed from before answering, then forwards to (530) 901-0353.

const TELNYX_API_KEY = process.env.TELNYX_API_KEY || "";
const TELNYX_PROFILE_ID = process.env.TELNYX_PROFILE_ID || "4001a183-adf9-4171-a62a-8528cd76a274";
const TELNYX_FROM = process.env.TELNYX_FROM || "+19168849689";
const ALERT_PHONE = process.env.ALERT_PHONE || "+15309010353";

async function alertIncomingCall(callerPhone) {
  if (!TELNYX_API_KEY || !callerPhone) return;
  try {
    await fetch("https://api.telnyx.com/v2/messages", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${TELNYX_API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        from: TELNYX_FROM,
        to: ALERT_PHONE,
        text: `Foundation Directory Call: ${callerPhone} just dialed (916) 884-9689.`,
        messaging_profile_id: TELNYX_PROFILE_ID
      })
    });
  } catch (err) {
    console.error("Call alert SMS failed:", err.message);
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

  const callerPhone = body.From || req.query.From || body.Caller || req.query.Caller || "";
  await alertIncomingCall(callerPhone);

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial timeout="18" action="https://foundationcrawlspace.online/api/voice-fallback">
    <Number>${ALERT_PHONE}</Number>
  </Dial>
</Response>`;

  return res.status(200).send(xml);
}
