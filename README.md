# DMS QR Client Intake

QR-driven intake for **Delaware Mobile Signings LLC**. A client or business scans
the code, gives first name, last name, email and phone, and immediately gets a
full screen of DMS services, pricing, booking links, locations and contact info.

## How it works

| Path | What it is |
|---|---|
| `public/index.html` | The whole visitor experience — intake form, then the services screen. No build step, no framework. |
| `api/lead.js` | Serverless endpoint that fans each lead out to every configured destination. |
| `tools/make-qr.mjs` | Generates the printable QR codes in `qr/`. |

### Two screens, one page

1. **Intake** — individual/business toggle, the four required fields, optional
   service-interest chips, optional veteran and SMS-consent checkboxes.
2. **Services** — appears the moment the form is submitted. Mobile notary,
   estate execution, loan signings, apostille tiers, fingerprinting,
   translation, and Delaware corporate filings, plus booking links, both
   office addresses, phone, email and credentials.

Business submissions additionally see a partner-terms card (Net 3, overflow
signings, EIN/UEI) that individuals don't.

### Collecting at a booth

- **"Add another person"** resets the form at the bottom of the services screen,
  so one tablet can be handed down a line.
- **Bad venue wifi is handled.** If the POST fails, the lead is queued in the
  visitor's `localStorage` and retried automatically on the next page load or
  when the device comes back online. The visitor still sees the services screen
  either way — a downstream outage is never shown to a client.

### Source tagging

The QR link carries its own campaign tags, so one codebase serves every event:

```
https://<your-domain>/?src=qr-standdown&event=Delaware%20VA%20Stand%20Down
```

`event` is shown as the badge in the header and attached to the CRM record;
`src` is stored as the lead source. Change them per event — no redeploy needed.

## Wiring up the CRM

Every destination is optional and additive. With none configured, leads are
still written to the Vercel runtime logs as `DMS_LEAD {...}` JSON lines, so a
booth shift is never lost waiting on configuration.

| Env var | Destination |
|---|---|
| `FLUENTCRM_WEBHOOK_URL` | FluentCRM incoming webhook. FluentCRM → Settings → Incoming Webhooks → create one, paste the URL. |
| `HUBSPOT_PORTAL_ID` + `HUBSPOT_FORM_ID` | HubSpot Forms. No API key needed. |
| `LEAD_WEBHOOK_URL` | Anything else — Zapier, Make, n8n, Google Sheets. |

Each lead is tagged `QR Intake`, the event name, `Individual` or `Business`,
`Veteran / Military` where ticked, plus every service chip selected.

## Regenerating the QR codes

```bash
npm install
node tools/make-qr.mjs https://your-domain.com
```

Writes SVG (print) and PNG (screen/slides) at error-correction level H into
`qr/`, so the code still scans with a logo over the middle or a crease through
it. Print the SVG at 1.5 inches or larger.

## Compliance notes

- The submit button carries a plain-language contact notice; SMS marketing
  consent is a separate, unchecked opt-in (TCPA express written consent).
- A hidden honeypot field drops bots without showing a visitor a CAPTCHA.
- The services screen states DMS is not a law firm and does not give legal
  advice, and repeats the 4-hour cancellation policy.
