# Grant Ready Weekly: per-client onboarding

Duplicates the weekly routine built for Plain Truth Baptist Church. For every client who buys a subscription, give Claude a **client name + criteria** and it creates a new weekly email routine for that client. The routine runs until you say "stop <client>".

## How to onboard a client
Send Claude: `Client: <name>` plus the fields in `clients/_TEMPLATE.json`:
- Recipients (to / cc), greeting name, send day and time (default: Monday morning, America/New_York)
- Focus areas / grant criteria (cause areas, geography, org type, award size, federal vs. foundation)
- Start date

Claude then:
1. Copies `clients/_TEMPLATE.json` to `clients/<client-slug>.json` and fills it in.
2. Generates the routine prompt by filling `routine-prompt.md` from that config.
3. Creates a **new, separate** weekly scheduled routine for that client (one routine per client).
4. Confirms the schedule and recipients back to you.

To stop: "Stop <client>". Claude deletes only that client's routine and sets `"status": "stopped"` in the config.

## What each weekly email contains (matches the Plain Truth format)
1. **This Week's Matched Opportunities**: open grants from Granted / Kindora that fit the client's criteria. Every item includes name, funder, amount, deadline and a link.
2. **Resource of the Week**: one practical readiness tip, rotated and never repeated for the same client (see `resources_used` in the config).
3. Footer: questions go to Marcia Boyer, Delaware Mobile Signings, plus the disclaimer.

Rules carried over from the Plain Truth routine:
- Never list unverified opportunities. If there are no reliable matches, say so and hold off.
- Send From the notary account, To the notary account, and Cc the client contacts (as in the Plain Truth sends).
- Subject: `Grant Ready Weekly: <Mon D, YYYY>: <Client Name>`.

## Files
- `routine-prompt.md`: prompt template for each client's routine
- `email-template.html`: HTML layout (gold/navy, Georgia)
- `clients/_TEMPLATE.json`: per-client config
- `clients/plain-truth-baptist-church.json`: reference client

## Limits to know about
- Routines created in a Claude Code session via CronCreate are session-only and expire after 7 days. For subscriptions that must run indefinitely, create each routine as a durable scheduled routine in claude.ai (use the generated prompt), or the weekly send will lapse.
