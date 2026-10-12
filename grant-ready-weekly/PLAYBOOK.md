# Grant Ready Weekly — per-client playbook

Reverse-engineered from the Plain Truth Baptist Church, Inc. routine (Aug 3 – Sep 28, 2026 sends).
Use this each time a new client buys a subscription.

## Inputs (given per client)
- Client display name (e.g. "Plain Truth Baptist Church")
- Criteria: org type, state/region, mission areas, project types (e.g. historic preservation, outreach), exclusions
- Client recipient emails (go in CC)
- Start date; runs weekly (Mondays, ~9:30 AM ET) until the user says stop

## Weekly run
1. Search live opportunities with the criteria:
   - Granted `search_grants` (use `get_grant` for details)
   - Kindora `search_open_grants` (set `state` for US clients; quoted phrases and `-term` exclusions work)
   - Run several narrow searches per mission area rather than one broad one.
2. Filter: keep only grants the client is eligible for (right state, org type, 501(c)(3) / faith-based as applicable). Drop expired deadlines and grants tied to other cities, counties, or states.
3. Pick roughly 3–7 matches. Each gets: title, funder, deadline (or "Rolling / no fixed deadline"), amount if known, and one sentence on why it fits and any caveat.
4. If a mission area has nothing eligible, say so in a short "note" box and suggest where to check directly. Don't pad the list.
5. Add a "Resource of the Week" (a short grant-writing or readiness tip). Don't repeat a topic from the last 8 weeks.
6. Build the email from `template.html`.
7. Send from the notary@delawaremobilesignings.com Gmail account:
   - Subject: `Grant Ready Weekly — {Mon D, YYYY} — {Client Name}`
   - To: notary@delawaremobilesignings.com
   - CC: client recipients
   - Always include a plain-text body alongside the HTML.
8. Before sending, open each "View Opportunity" URL and confirm it points to the funder and program named in that card.
9. A quiet week still sends, with a shorter list and the note box.

## Known issues from past sends (avoid)
- Sep 14: the "Urban Awareness USA" card linked to thelawrencefoundation.org, a different funder.
- Sep 28: two cards shared one URL, and the "Community Foundation" card linked to an NPS page.
- Don't recommend generic categories as opportunities without a specific, working link.

## Stopping
Per-client schedule continues until the user says stop. Then delete that client's schedule and leave other clients untouched.
