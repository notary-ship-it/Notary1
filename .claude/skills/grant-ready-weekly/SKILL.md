---
name: grant-ready-weekly
description: Use when checking FluentCRM or FluentCart for new purchasers of the Grant Ready Weekly subscription (daily onboarding check), or when drafting/sending a client's weekly grant-readiness email (the routine already running for Plain Truth Baptist Church). Triggers on "check for new grant ready subscribers", "onboard a new grant client", "run the daily FluentCRM/FluentCart check", "send this week's grant email for <client>", or a scheduled daily/weekly firing of this routine.
---

# Grant Ready Weekly — client onboarding + send

Delaware Mobile Signings sells a recurring "Grant Ready Weekly" service: a
weekly curated-grants email per client, in the format already running for
Plain Truth Baptist Church (see `reference/email-template.md`). This skill
has two jobs that run on different cadences:

1. **Daily** — check FluentCRM / FluentCart for new purchasers of the Grant
   Ready Weekly product and onboard them into the roster.
2. **Weekly, per active client** — search for matching grant opportunities
   and send that client's email.

The roster of clients (who's active, their contacts, their search criteria)
lives in `clients.json` next to this file. Never onboard or send silently —
every new client and every send should be traceable in that file.

## 0. Configuration this skill needs (check before Step 1)

FluentCRM/FluentCart have no dedicated connector in this environment, so
this skill talks to their REST APIs directly. Before running the daily
check, confirm these are set (env vars or supplied by the user):

- `FLUENTCRM_SITE_URL` — e.g. `https://delawaremobilesignings.com`
- `FLUENTCRM_API_USERNAME` / `FLUENTCRM_API_KEY` — WordPress Application
  Password or FluentCRM API key, used as HTTP Basic Auth
- `FLUENTCART_API_USERNAME` / `FLUENTCART_API_KEY` — if FluentCart's API
  uses separate credentials from FluentCRM; otherwise reuse the above
- `GRANT_READY_WEEKLY_PRODUCT` — the exact FluentCart product name/ID, or
  the FluentCRM tag applied on purchase, that identifies a Grant Ready
  Weekly subscriber

**None of these are configured yet.** If you reach Step 1 and they're still
missing, stop and tell the user exactly which ones are needed — don't guess
API paths or fabricate a "no new clients found" result. Once the user gives
the site URL and credentials, verify the actual REST namespaces before
assuming endpoint paths:

```
curl -s -u "$FLUENTCRM_API_USERNAME:$FLUENTCRM_API_KEY" \
  "$FLUENTCRM_SITE_URL/wp-json/" | jq '.namespaces'
```

Look for something like `fluent-crm/v2` and `fluent-cart/v2` in the
response and confirm against the site's own API docs (FluentCRM: Settings →
API Keys in-plugin; FluentCart: Settings → REST API) before building
queries — don't assume undocumented paths are correct.

## 1. Daily check — new Grant Ready Weekly purchasers

1. Query FluentCart for orders/subscriptions on `GRANT_READY_WEEKLY_PRODUCT`
   (or FluentCRM for contacts carrying the corresponding tag).
2. Dedupe against `clients.json` by email — skip anyone already present
   (any status, including `stopped`; a stopped client doesn't get
   re-onboarded automatically).
3. For each genuinely new purchaser, pull the criteria fields listed in
   Step 2 from their CRM contact custom fields / order notes.

## 2. Criteria required to onboard a client

A client can't be marked `active` until all of these are known. This is
the "what criteria you need" the CRM record should supply:

| Field | Description |
|---|---|
| `org_name` | Client's organization name, as it should appear in "Hi {org} team," |
| `contacts` | Primary contact name(s) + email(s) to Cc on the weekly send |
| `criteria.keywords` | Topics/cause areas to search (e.g. "historic preservation", "youth education") |
| `criteria.geography` | State/region the org is based in and eligible for |
| `criteria.org_type` | e.g. "501(c)(3) church", "small nonprofit" |
| `criteria.funding_types` | federal / state / foundation / community foundation, etc. |
| `cadence.preferred_day` | Which day of the week the client expects the email |

If the CRM record is missing any of these, do not guess or invent values.
List exactly what's missing and ask the user (or flag it for follow-up with
the client) rather than onboarding with incomplete criteria.

## 3. Add to roster

Append a new entry to `clients.json` (schema below, mirroring the seeded
Plain Truth Baptist Church entry), `status: "active"`, and record the
FluentCRM contact ID / FluentCart order ID / product so re-runs can dedupe
correctly.

## 4. Weekly send, per active client

For each client with `status: "active"`:

1. Search for matching opportunities using the Granted / Kindora funder
   tools, filtered by that client's `criteria` (keywords, geography,
   org_type, funding_types).
2. Draft the email following `reference/email-template.md` exactly —
   subject line `Grant Ready Weekly — {Mon DD, YYYY} — {org_name}`,
   greeting `Hi {org_name} team,`, the same section structure (matched
   opportunities, a funding-gap note when relevant, one "Resource of the
   Week" tip), and the same sign-off ("reach out to Marcia Boyer, Delaware
   Mobile Signings") and disclaimer line.
3. Send via Gmail: `To: notary@delawaremobilesignings.com`,
   `Cc: {client's contacts}` — this mirrors how every prior Plain Truth
   Baptist Church send was addressed.
4. Record the send date and thread ID in the client's `history` in
   `clients.json`.

Never fabricate a grant listing — every "View Opportunity" link must come
from an actual search result, not be invented to fill out the list. A
shorter, honest list (like the Sep 28 Plain Truth email) is correct
behavior, not a failure.

## 5. Stopping a client

When the user says to stop a client, set that client's `status` to
`"stopped"` in `clients.json` — never delete their record — and confirm
back which client was stopped.

## Known limitation

This skill defines what to *do* on each check; it does not create the
recurring trigger that runs it. There's no tool available here to
provision a persistent daily/weekly schedule on the account — the same way
the Plain Truth Baptist Church routine's schedule had to be set up once
through the account's own scheduled-tasks feature, each new cadence (the
daily FluentCRM/FluentCart check, and the weekly per-client send) needs
that same one-time setup. Flag this to the user rather than assuming it's
already wired up.
