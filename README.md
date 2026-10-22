# Notary1

Working repository for Delaware Mobile Signings LLC tooling.

## Grant Desk

`grant-desk/grant-desk.html` — a grant analyzer built as a sibling to the DMS Bid Desk. It reads a
funding notice (federal NOFO, state RFA, or foundation RFP), scores a client organization against
the funder's own published rubric, models the federal registration chain against the deadline, and
checks budgets and narratives before they go into the package.

Published as **DMS Grant Desk**: https://claude.ai/artifact/Ptb7uEy4tdJXXkyFMgsiif

Nine tabs: Intake · Notice · Eligibility & runway · Rubric · Corrections · What's needed ·
Document check · Packet · Client.

The assessment can be argued with. Corrections holds a chat that explains and cites but cannot move
a number, and a ledger that can: each correction is typed, and the type governs what scoring may do
with it — a fact true today can raise the score, a thing you intend to add cannot. Every re-score
returns a change log naming which correction moved what.

An opportunity held in a slot saves itself — corrections, the conversation and an append-only
revision history, about a second after each change, with the slot's score index refreshed in the
same write. One not yet in a slot says so rather than losing the work quietly. See the spec's §4d.

Intake takes a notice four ways: a dropped PDF (text extracted in the page), a live search of the
Kindora grant database, a pasted URL whose site and opportunity number are parsed out, or pasted
text. A published page cannot download a website — the browser sandbox blocks it silently — so
there is no fetch-from-URL button by design; see the spec's §4b.

Three grants can be kept in flight per client, each slot holding its notice, scores and gap list so
work can be picked back up later. Clients come in live from HoneyBook, or from any CRM export as
CSV (FluentCRM has no connector — see §4c).

Two things it does that the Bid Desk does not:

- **Adopts the funder's rubric as data** rather than scoring on fixed weights, and reports points
  evidenced versus points left on the table, criterion by criterion.
- **Splits arithmetic from judgment.** Budget footing, indirect-rate caps, cost-share percentages
  and page limits are computed in the page and are either right or wrong; Claude's reading of the
  same document is shown separately and labelled as judgment.

Every gap it finds is filed against one of the six tabs of the Grant Ready Binder, so its output
doubles as the build sheet for that deliverable.

Design notes, data model, known limits and the productization path (client packaging, the
WordPress client view, the skill port) are in **[docs/grant-desk-spec.md](docs/grant-desk-spec.md)**.

## Grant Desk Intake skill

`.claude/skills/grant-desk-intake/` — the same work outside the browser, for when it starts from
files on disk. Reads a notice PDF, extracts the record, and runs the deterministic budget and
narrative checks as a Python port of the page's arithmetic layer.

```bash
python3 .claude/skills/grant-desk-intake/scripts/grant_checks.py budget BUDGET.csv \
    --cap 10 --match 25 --ceiling 500000 --floor 150000
python3 .claude/skills/grant-desk-intake/scripts/test_grant_checks.py   # 13 tests
```

Exit status is 1 when any finding is a blocker, so it drops into a pre-submission check. The tests
run the example budget's three planted defects; if they fail, the script and the page have drifted
apart and will disagree about the same spreadsheet.

### Editing it

The HTML file is the source of truth. Republish with the Artifact tool using the same file path to
keep the same URL. The page declares four runtime capabilities: `sample` (the analysis passes), `db` (client records
at `grantdesk/clients`, saved sites at `grantdesk/sources`), `downloads` (the readiness memo
export), and `mcp` (the Kindora grant search). Declaring `mcp` bars public sharing of the
artifact — intentional, since the client-facing surface is WordPress rather than this page.
