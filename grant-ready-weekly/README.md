# Grant Ready Weekly

A recurring email service Delaware Mobile Signings runs for grant-readiness
clients: once a week, each subscribed client gets a personalized roundup of
open grant/funder opportunities matched to their stated focus areas, plus a
short grant-writing tip.

This folder generalizes the process that was previously run by hand for a
single client (Plain Truth Baptist Church) so it can be repeated for every
client who subscribes, without rebuilding it from scratch each time.

## How it works

1. **Roster.** `clients.json` lists every subscribed client: their name,
   funding-focus criteria (keywords describing what kind of grants they
   want matched), who the email goes to/cc's, and `status`
   (`active` or `paused`).
2. **Weekly run.** On a weekly cadence, for every client with
   `status: "active"` in `clients.json`:
   - Search current grant/funder listings (the `Granted` and
     `Kindora-Funder-Discovery` tools — `search_grants`, `search_open_grants`,
     `search_funders`) using that client's `criteria` keywords.
   - Pick the opportunities that are genuinely relevant (open/rolling
     deadline, plausible eligibility fit) — usually 3-8 per week. If the
     search tools are unavailable or return nothing useful, say so plainly
     in the email rather than omitting the section (see fallback copy
     below) — don't fabricate matches.
   - Draft the email using the template below, filling in that client's
     name and matched opportunities.
   - Send it via Gmail (`mcp__Gmail__send_message`), addressed the way
     `recipients` specifies for that client.
3. **Onboarding a new client.** When given a client name and their funding
   criteria, add a new entry to `clients.json` with `status: "active"`.
   That client starts receiving the weekly email on the next scheduled run
   — no other setup needed.
4. **Offboarding.** When told to stop for a client, set their `status` to
   `"paused"` (or delete the entry). They're skipped on the next and all
   future runs.

## Email template

```
Subject: Grant Ready Weekly — <Month DD, YYYY> — <Client Name>

GRANT READY WEEKLY
Delaware Mobile Signings — Grant Readiness & SAM Registration Services

Hi <Client Name> team,

<One or two sentences: what we looked for this week, referencing their
specific criteria in plain language.>

This Week's Matched Opportunities

<For each matched opportunity:>
<Grant/Program Name>
Funder: <Funder> | Deadline: <Deadline, or "Rolling / no fixed deadline">
<1-2 sentence explanation of why it fits this client's stated criteria,
including any caveats worth flagging (e.g. "worth confirming eligibility
before applying").>
View Opportunity → <link>

Resource of the Week

<Short (~100-150 word) grant-writing or nonprofit-readiness tip. Rotate
topics week to week — don't repeat the same tip for the same client twice
in a row.>

Questions about any of these? Reply to this email or reach out to Marcia
Boyer, Delaware Mobile Signings.

This is a curated selection from public grant databases, not a guarantee of
funding eligibility or award.
```

### Fallback copy (search unavailable / no matches)

Replace the "This Week's Matched Opportunities" section with:

```
Our live grant search service was temporarily unable to connect this week
due to a technical issue on our end — so we don't have a fresh
matched-opportunities list to share in this edition. This is a connectivity
hiccup, not a sign that funding has dried up.

We'll run the search again for next week's edition. In the meantime, if
you'd like to browse directly, grants.gov/search-grants lets you filter by
keyword (try terms related to your programs) and by eligibility.
```

## Notes

- Keep each client's email self-contained — never mention one client's
  criteria, opportunities, or business details in another client's email.
- The "Resource of the Week" tip should vary week to week per client; track
  what's been sent if repetition becomes a risk.
- This is a content/data playbook, not a script — the matching and drafting
  is done by an LLM following these instructions, since "is this grant a
  good fit" isn't a rule a deterministic script can evaluate.
