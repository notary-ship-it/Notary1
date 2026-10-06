/**
 * POST /api/lead — receives an intake submission and fans it out to every
 * configured destination. Nothing here is required for the page to work: with
 * no environment variables set, leads still land in the Vercel runtime logs
 * as `DMS_LEAD` lines, so a booth shift is never lost waiting on config.
 *
 * Destinations, all optional, all additive:
 *   FLUENTCRM_WEBHOOK_URL  FluentCRM incoming-webhook URL
 *   HUBSPOT_PORTAL_ID + HUBSPOT_FORM_ID   HubSpot Forms (no API key needed)
 *   LEAD_WEBHOOK_URL       generic catch-all (Zapier, Make, n8n, Sheets)
 */

const TIMEOUT_MS = 6000;

function clean(value, max = 200) {
  return typeof value === 'string' ? value.trim().slice(0, max) : '';
}

function normalizePhone(raw) {
  const d = clean(raw, 40).replace(/\D/g, '');
  if (d.length === 10) return `+1${d}`;
  if (d.length === 11 && d[0] === '1') return `+${d}`;
  return d ? `+${d}` : '';
}

function isEmail(v) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v);
}

async function postJson(url, body, label) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`${res.status} ${text.slice(0, 200)}`);
    }
    return { sink: label, ok: true };
  } catch (err) {
    console.error(`DMS_SINK_FAIL ${label}: ${err.message}`);
    return { sink: label, ok: false, error: err.message };
  } finally {
    clearTimeout(timer);
  }
}

function buildTags(lead) {
  const tags = ['QR Intake', lead.eventName, lead.entityType === 'business' ? 'Business' : 'Individual'];
  if (lead.veteran) tags.push('Veteran / Military');
  return tags.concat(lead.services).filter(Boolean);
}

function toFluentCrm(lead) {
  return {
    first_name: lead.firstName,
    last_name: lead.lastName,
    email: lead.email,
    phone: lead.phone,
    company_name: lead.company || undefined,
    designation: lead.jobTitle || undefined,
    status: 'subscribed',
    source: lead.source,
    tags: buildTags(lead),
    contact_type: lead.entityType === 'business' ? 'lead' : 'lead',
  };
}

function toHubspot(lead, req) {
  const fields = [
    { name: 'firstname', value: lead.firstName },
    { name: 'lastname', value: lead.lastName },
    { name: 'email', value: lead.email },
    { name: 'phone', value: lead.phone },
  ];
  if (lead.company) fields.push({ name: 'company', value: lead.company });
  if (lead.jobTitle) fields.push({ name: 'jobtitle', value: lead.jobTitle });
  if (lead.services.length) {
    fields.push({ name: 'message', value: `Interested in: ${lead.services.join(', ')}` });
  }
  return {
    fields,
    context: {
      pageUri: `https://${req.headers.host || 'dms'}/`,
      pageName: `DMS Intake — ${lead.eventName}`,
    },
    legalConsentOptions: {
      consent: {
        consentToProcess: true,
        text: 'I agree to allow Delaware Mobile Signings LLC to contact me about my request.',
        communications: [
          {
            value: Boolean(lead.smsOptIn),
            subscriptionTypeId: 999,
            text: 'I agree to receive text messages from Delaware Mobile Signings LLC.',
          },
        ],
      },
    },
  };
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ ok: false, error: 'Method not allowed' });
  }

  const body = typeof req.body === 'string' ? safeParse(req.body) : req.body || {};

  // Honeypot — bots fill hidden fields. Accept, discard, tell them nothing.
  if (clean(body.website)) {
    return res.status(200).json({ ok: true, delivered: [] });
  }

  const lead = {
    firstName: clean(body.firstName, 80),
    lastName: clean(body.lastName, 80),
    email: clean(body.email, 160).toLowerCase(),
    phone: normalizePhone(body.phone),
    company: clean(body.company, 160),
    jobTitle: clean(body.jobTitle, 120),
    entityType: body.entityType === 'business' ? 'business' : 'individual',
    services: Array.isArray(body.services) ? body.services.slice(0, 12).map((s) => clean(s, 60)).filter(Boolean) : [],
    veteran: Boolean(body.veteran),
    smsOptIn: Boolean(body.smsOptIn),
    source: clean(body.source, 60) || 'qr-intake',
    eventName: clean(body.eventName, 80) || 'QR Intake',
    capturedAt: clean(body.capturedAt, 40) || new Date().toISOString(),
    receivedAt: new Date().toISOString(),
  };

  if (!lead.firstName || !lead.lastName || !isEmail(lead.email) || lead.phone.replace(/\D/g, '').length < 10) {
    return res.status(400).json({ ok: false, error: 'first name, last name, a valid email and a 10-digit phone are required' });
  }

  // Durable-enough record of record: searchable in Vercel runtime logs even
  // when every downstream CRM is unconfigured or down.
  console.log(`DMS_LEAD ${JSON.stringify(lead)}`);

  const jobs = [];
  if (process.env.FLUENTCRM_WEBHOOK_URL) {
    jobs.push(postJson(process.env.FLUENTCRM_WEBHOOK_URL, toFluentCrm(lead), 'fluentcrm'));
  }
  if (process.env.HUBSPOT_PORTAL_ID && process.env.HUBSPOT_FORM_ID) {
    const url = `https://api.hsforms.com/submissions/v3/integration/submit/${process.env.HUBSPOT_PORTAL_ID}/${process.env.HUBSPOT_FORM_ID}`;
    jobs.push(postJson(url, toHubspot(lead, req), 'hubspot'));
  }
  if (process.env.LEAD_WEBHOOK_URL) {
    jobs.push(postJson(process.env.LEAD_WEBHOOK_URL, lead, 'webhook'));
  }

  const results = await Promise.all(jobs);

  // Always 200 when the lead is captured — the visitor is standing at a booth
  // and must not see an error because a downstream CRM is having a bad day.
  return res.status(200).json({
    ok: true,
    delivered: results.filter((r) => r.ok).map((r) => r.sink),
    failed: results.filter((r) => !r.ok).map((r) => r.sink),
    sinksConfigured: jobs.length,
  });
}

function safeParse(text) {
  try { return JSON.parse(text); } catch { return {}; }
}
