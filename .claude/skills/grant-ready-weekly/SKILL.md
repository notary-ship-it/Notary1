---
name: grant-ready-weekly
description: Set up (or run) the weekly "Grant Ready Weekly" email for a Delaware Mobile Signings subscription client. Use when given a client name plus matching criteria, or when a scheduled weekly run for a client fires.
---

# Grant Ready Weekly

Duplicates the weekly routine originally built for Plain Truth Baptist Church. One client = one client spec file + one recurring weekly job. Repeat for every new subscriber; stop a client only when the owner says so.

## A. Onboarding a new client (owner gives client name + criteria)

1. Copy `clients/_template.md` to `clients/<client-slug>.md` and fill it in from what the owner said. Ask only for what is missing: greeting name, CC recipients, focus areas/criteria, state/geography, send day/time.
2. Commit the spec file.
3. Create the recurring job with `CronCreate` (recurring) using the prompt in section B, filled with the client slug. Default: Mondays ~8:00 local, off-minute (e.g. `7 8 * * 1`). NOTE: CronCreate jobs are session-only and auto-expire after 7 days; for a durable schedule create it as a scheduled routine instead and tell the owner which was used.
4. Report the client, schedule and next run time. Do not send a test to the client; if a preview is wanted, create a Gmail draft addressed only to the owner.

## B. Weekly run prompt (per client)

"Run the grant-ready-weekly skill, section C, for clients/<client-slug>.md."

## C. Weekly run procedure

1. Read `clients/<slug>.md`. If `status: stopped`, do nothing.
2. Find opportunities matching the client's criteria. Sources: Granted (`search_grants`), Kindora (`search_open_grants`, `search_funders`), Grants.gov-type federal listings via web search. Use the client's state and focus areas; run several targeted queries.
3. Keep 3–7 opportunities. Each needs: name, funder, deadline (or "Rolling / no fixed deadline"), amount if known, one–two sentences on why it fits THIS client, and a direct application/info URL. Exclude expired deadlines, ineligible applicant types, and duplicates of items sent in the last 4 weeks (check the client's previous sent emails via Gmail search on the subject).
4. Never include anything unverified. If nothing verified is found, use the "no matches" block in the template (as in the Oct 12, 2026 Plain Truth issue) rather than padding.
5. Pick a "Resource of the Week" (short grant-readiness tip, 60–110 words; do not repeat one used in the last 8 weeks).
6. Build the HTML from `template.html` (replace `{{...}}` placeholders; repeat the opportunity card per match; use plain direct URLs, not tracking links).
7. Send with Gmail `send_message`:
   - To: notary@delawaremobilesignings.com
   - CC: the client's recipients from the spec
   - Subject: `Grant Ready Weekly — <Mon D, YYYY> — <Client Name>`
   - Include both HTML and plain-text bodies.
8. Do not alert the owner on a normal send. Notify only on failure (no tools, send error, bounce such as an invalid CC address) or if something needs their decision.
