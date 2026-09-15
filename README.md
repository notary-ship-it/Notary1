# Notary1

Working repository for Delaware Mobile Signings LLC tooling.

## Grant Desk

`grant-desk/grant-desk.html` — a grant analyzer built as a sibling to the DMS Bid Desk. It reads a
funding notice (federal NOFO, state RFA, or foundation RFP), scores a client organization against
the funder's own published rubric, models the federal registration chain against the deadline, and
checks budgets and narratives before they go into the package.

Published as **DMS Grant Desk**: https://claude.ai/artifact/Ptb7uEy4tdJXXkyFMgsiif

Eight tabs: Intake · Notice · Eligibility & runway · Rubric · What's needed · Document check ·
Packet · Client.

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

### Editing it

The HTML file is the source of truth. Republish with the Artifact tool using the same file path to
keep the same URL. The page declares three runtime capabilities: `sample` (the analysis passes),
`db` (client records at `grantdesk/clients`), and `downloads` (the readiness memo export).
