---
name: grant-ready-weekly
description: Create a new weekly "Grant Ready Weekly" email routine for a Delaware Mobile Signings subscription client. Use whenever the user gives a client name plus grant criteria, or says to start/stop a client's weekly grant email.
---

# Grant Ready Weekly — per-client routine

Duplicates the "Plain Truth Baptist Church" weekly routine for any subscribing client.
Reference output: Gmail subjects `Grant Ready Weekly — <Mon DD, YYYY> — Plain Truth Baptist Church`.

## When the user gives a client name + criteria
1. Create `clients/<client-slug>.md` from `clients/_template.md` (name, greeting, contact emails to CC, location/state, org type, criteria, exclusions, send day/time).
2. Create ONE new scheduled routine for that client (weekly, same weekday/time each week) whose prompt is: "Run the grant-ready-weekly skill for clients/<client-slug>.md". One routine per client; never merge clients into one routine.
3. Confirm back: client, criteria, schedule, recipients. Do not send an email until the routine fires (or the user asks for a test).
4. When the user says stop for a client: delete that client's routine and set `status: stopped` in its file. Never delete other clients' routines.

## Each weekly run
1. Read the client file. If `status: stopped`, do nothing.
2. Search for open opportunities matching the criteria: Granted (`search_grants`, `search_funders`), Kindora (`search_open_grants`), plus federal/state sources. Respect the client's state and exclusions; drop grants tied to other states/cities, expired deadlines, or ineligible org types.
3. Pick the best matches (typically 3–7). For each: title, funder, deadline (or "Rolling / no fixed deadline"), amount if known, a 1–2 sentence plain-English fit explanation, and a link.
4. VERIFY every link: it must be the actual page for that listing, not another funder's page and not reused across different listings. If no direct URL is confirmed, say so rather than guessing.
5. If a criteria area has nothing strong, include a short "note" box saying so plus a concrete next step, instead of padding with weak matches. Say "shorter list than usual" honestly when applicable.
6. Add a "Resource of the Week" (grant-readiness tip; do not repeat a topic used in the client's last 4 emails — check Sent mail).
7. Skip anything already sent in recent weeks unless its deadline is now within 14 days.
8. Send via Gmail: To = notary@delawaremobilesignings.com, CC = client contacts, subject `Grant Ready Weekly — <date> — <Client Name>`, HTML + plain-text body. If any content is uncertain, create a draft instead of sending and flag it.

## Email layout (HTML, 600px, inline styles)
- Header band `#1b2a4a`: "GRANT READY WEEKLY" in `#c9a24b` 26px bold, letter-spacing 2px; subline white 13px: "Delaware Mobile Signings — Grant Readiness & SAM Registration Services".
- Greeting "Hi <Client Name> team," + 1–2 sentence intro (vary weekly).
- Section heading "This Week's Matched Opportunities" (`#1b2a4a` 17px bold, 2px `#c9a24b` bottom border).
- Opportunity cards: `#f9f7f1` background, 4px `#c9a24b` left border; title 15px bold navy; "Funder: … | Deadline: …" 13px gray; description 14px; "View Opportunity →" link navy bold.
- Optional note card: `#f4f1e8`, 4px navy left border.
- "Resource of the Week" heading + title in `#c9a24b` + paragraph.
- Footer band navy: "Questions about any of these? Reply to this email or reach out to Marcia Boyer, Delaware Mobile Signings." and disclaimer in `#c9a24b` 11px: "This is a curated selection from public grant databases, not a guarantee of funding eligibility or award."
- Fonts: Georgia outer, Arial content.
