# Grant Ready Weekly — Per-Client Playbook

Reproduces the weekly email currently sent to Plain Truth Baptist Church, Inc., so it can be
stamped out for every client who buys a subscription. Delaware Mobile Signings LLC.

## Trigger
Whenever the owner gives a **client name + criteria**, do the setup below. The email then goes
out **every Monday** for that client **until the owner says stop**.

## Inputs (collect; ask only for what is missing — never invent)
| Field | Example (Plain Truth) |
|---|---|
| Client legal name | Plain Truth Baptist Church, Inc. |
| Greeting name | Plain Truth Baptist Church team |
| To / Cc recipients | To: notary@delawaremobilesignings.com, Cc: client contacts |
| Criteria (mission focus, populations, geography, budget size, grant types, excluded topics) | community/social-service outreach, historic building preservation, faith-based, Delaware |
| Send day/time | Monday morning ET |

Save the answers as `clients/<client-slug>.md` (copy `clients/_TEMPLATE.md`).

## Weekly run (per client)
1. **Find opportunities** — Granted (`search_grants`, `search_funders`) and Kindora
   (`search_open_grants`, `search_funders`); run several targeted searches from the criteria.
   Use `state` for US location. Open `get_grant` for details.
2. **Verify** — keep only opportunities that are open, with a confirmed deadline (or "Rolling"),
   a real application URL, and a plausible fit. Drop expired items and anything already sent in a
   prior week (search Gmail `subject:"Grant Ready Weekly" "<client>"`).
3. **Compose** from `template.html`: 3–7 opportunity cards (title, funder, deadline, 1–2 sentence
   fit note that is honest about eligibility caveats, direct link), plus one "Resource of the
   Week" (rotate topics; don't repeat the last 8 weeks).
4. **If nothing verified:** use the "holding off" card (as in the Oct 12 send) — never share
   unconfirmed items.
5. **Send** via Gmail from notary@delawaremobilesignings.com.
   Subject: `Grant Ready Weekly — <Mon D, YYYY> — <Client Name>`. Include the plain-text version.
6. Do not send twice for the same client and week.

## Fixed branding / copy (identical for every client)
- Navy `#1b2a4a`, gold `#c9a24b`, Georgia serif, 600px layout.
- Header: GRANT READY WEEKLY / "Delaware Mobile Signings — Grant Readiness & SAM Registration Services".
- Footer: "Questions about any of these? Reply to this email or reach out to Marcia Boyer, Delaware
  Mobile Signings." + disclaimer "This is a curated selection from public grant databases, not a
  guarantee of funding eligibility or award."

## Scheduling a new client
Create one scheduled routine per client (weekly, Monday morning), prompt = "Run the Grant Ready
Weekly playbook for `clients/<slug>.md`". To stop a client: delete/disable that routine and set
`status: stopped` in the client file. Routines created from inside a session (CronCreate) are
session-only and expire after 7 days — create them as saved routines instead.
