# Grant Desk — design notes and productization path

Delaware Mobile Signings LLC · Grant & Government Contract Services
Companion document to `grant-desk/grant-desk.html` (published as **DMS Grant Desk**).

---

## 1. Why this is not just the Bid Desk with the words swapped

The Bid Desk answers one question: *should we bid on this?* It scores **DMS** against a
solicitation on six fixed dimensions we control, and the answer is go / no-go.

The Grant Desk answers three questions, about **someone else's organization**, and only the
first of them resembles a bid/no-bid:

| Question | Who it is about | What answers it |
| --- | --- | --- |
| Can this client legally and physically submit? | the client | eligibility gates + the registration runway |
| Would it score well enough to be funded? | the client's file | the funder's own rubric, self-scored |
| Is each document actually correct? | the package | deterministic checks + a reading pass |

Four structural differences fall out of that, and they drive the whole build.

**1. The rubric belongs to the funder, not to us.** A solicitation gets scored on criteria we
chose once. A grant gets scored on criteria the notice publishes — usually with explicit point
values, often with a sentence saying what will *not* score well. So the analyzer cannot carry a
fixed weighting model. It has to **adopt the funder's rubric as data** and score against it. This
is the single biggest design difference, and it is why the Rubric tab is the centrepiece rather
than a summary panel.

**2. There are two different scores, and conflating them would be a bug.**

- **Projected reviewer score** (0 → whatever the notice totals): what a reviewer would give
  *today*, reading only what the client can currently evidence. Measures competitiveness.
- **Readiness index** (0–100, five fixed dimensions): whether a *complete* package can be filed
  on time at all. Measures deliverability — and it is the thing DMS actually sells.

An application can be readiness-90 and score-55 (well-organized client, thin program design), or
readiness-40 and score-85 (brilliant program, no AOR delegated, no 990 on file). Those two
situations need opposite advice. One number cannot carry both.

**3. Eligibility has a clock on it.** A procurement either lets you bid or it doesn't. A federal
grant makes you clear a *chain* of registrations first — EIN → SAM.gov → UEI → Grants.gov →
AOR delegation by the E-Biz POC → workspace → validation window — and the chain runs in
sequence, on other people's schedules. A new SAM.gov registration is commonly 2–4 weeks. AOR
delegation waits on a human at the client. This is why applications die: not because the
narrative was weak, but because 31 days of chain did not fit into 22 days of calendar.

So the desk models the chain as lead times in days and draws it against the deadline. If the
chain does not fit, the recommendation is NO-GO regardless of how good the program is — and the
useful advice becomes "clear the chain now, apply next cycle."

**4. The client's own documents are the input.** The Bid Desk needs one thing pasted in. The
Grant Desk needs a spreadsheet to add up, a narrative to be inside a page limit, a match to be
documented rather than asserted. That is the "semi-AI check your uploads" requirement, and it
needed its own architecture — see §4.

---

## 2. Pass architecture

Three model passes plus a deterministic layer that never calls a model.

```
Notice text ──► Pass A: extract (chunked, 40k chars/pass, merged) ──► the notice record
                                                                          │
Client record + document registry ────────────────────────────────────────┤
                                                                          ▼
                                            Pass B: assess ──► gates, readiness, rubric self-score, gap list

One uploaded document ──► Layer 0: arithmetic (in the page) ──► Pass C: read it ──► findings
```

**Pass A — extract.** Same shape as the Bid Desk: chunk on paragraph boundaries, extract each
part, merge pairwise, stop merging when the accumulated record passes ~45 KB so the merge input
stays under the 64 KiB cap. `reviewCriteria` is called out in the prompt as the most important
field, because everything downstream hangs off it.

**Pass B — assess.** Takes the notice record, the client record and the document registry, and
returns gates, the five readiness dimensions, one rubric row per criterion, and a gap list
keyed to the binder tabs. Hard rule in the prompt: **a field whose value is `PENDING` is never
evidence of compliance.** It scores as unknown and says so. This is the same discipline as the
Bid Desk's `VERIFY` handling, and it is the reason the tool is worth anything — a self-score that
flatters the file tells you nothing a reviewer will agree with.

**Pass C — document check.** See §4.

All three pass `modelTier: "complex"` and a 24-hour cache; "Re-read and re-score" sets
`refresh: true` so the button genuinely asks again rather than replaying.

---

## 3. The rubric engine

For each criterion the notice publishes, the desk carries:

| Field | Meaning |
| --- | --- |
| `maxPoints` | copied from the notice, never invented |
| `supportedPoints` | what a reviewer would award **today**, on current evidence |
| `evidenceOnFile` | what in the client record supports that |
| `whatIsMissing` | what a reviewer would look for and not find |
| `liftPoints` | additional points realistically reachable before the deadline |
| `howToGainPoints` | the specific artifact to produce — *"name the curriculum and its dose (sessions/week × weeks)"*, never *"strengthen the approach"* |

Rendered as a two-segment bar per criterion on one shared scale: points evidenced (navy) and
**points left on the table** (pale). The gap is the product. A client looking at a 30-point
criterion scoring 12 understands the situation without reading a word of prose.

Two comparisons make the score mean something, and both come from the notice itself rather than
from us: a stated **minimum score** (below it, rank is irrelevant — you are not considered) and
a **historical funded score** where the notice discloses one. The example notice states both
(70 minimum, 88 lowest funded last round), which is realistic: an application at 74 clears the
floor and still loses.

---

## 4. The document checker — what "semi-AI" actually means

This is the part worth being precise about, because the split is the design.

**Layer 0 — arithmetic, computed in the browser.** Either right or wrong. No model involved.

*Budget spreadsheets:*
- every row cross-footed (parts vs. its own total column)
- every column footed block by block against its stated subtotals and grand total
- a labelled rate re-derived against its base (`"Fringe benefits at 22%"`, `"Indirect at 12%"`)
- indirect cost as a percentage of direct, against the notice's cap (10% de minimis when no NICRA)
- cost share as a percentage of total project cost, against the required match — including the
  dollar figure the match would have to reach, and the alternative federal request that matches
  the cash on hand
- federal request against award ceiling and floor
- hygiene: duplicate line labels, blank amounts, negative figures
- differences under $1 are reported as rounding, not as errors

*Narratives:*
- word and character count, estimated page count at the notice's stated line spacing
- page count against the stated limit, with the word count to cut
- placeholder text still in the draft (`TBD`, `XXX`, `[insert…]`, `FIXME`)
- a keyword scan against the criterion's sub-elements — which proves the *absence* of a word,
  never the presence of an argument, and is labelled as such

Verified against the seeded example budget, which carries three planted defects: a $1,000
cross-foot error, indirect at 12% against a 10% cap, and a 15% match against a 25% requirement.
All three are caught, plus the column-footing error the first one cascades into.

**Layer 1 — judgment, from Claude.** Gets the document *and Layer 0's findings as established
fact*, so it does not recompute arithmetic or repeat it back. It judges what arithmetic cannot:
is each line allocable to a stated activity, is the basis of each figure given, is the match
documented or merely asserted, does the narrative answer every sub-element in the criterion's own
order with specifics rather than intentions.

**They are rendered in separate panels, labelled "Computed in this page — not an opinion" and
"Judgment — verify before acting on it."** A client paying for this deserves to know which
findings are arithmetic and which are a reading. Blurring them would be the easiest way to make
the tool untrustworthy.

*Current input handling:* `.xlsx`/`.xls` via SheetJS (first sheet only, stated in the UI),
`.csv`/`.tsv` parsed natively with quote handling, `.txt`/`.md` as text. **PDFs must be pasted as
text** — the honest limitation, surfaced in the UI rather than hidden.

---

## 4b. Getting a notice in — and why there is no "load from URL" button

The obvious intake affordance is: paste the URL of the grant page, press a button, the notice
loads. **It cannot be built in the page.** A published artifact's browser sandbox blocks every
request to a host outside a short allowlist (cdnjs, Google Fonts), and it blocks them *silently* —
no error the page can catch and explain. A "fetch this URL" button would be a button that does
nothing, which is worse than no button.

So the requirement gets served three other ways, in descending order of how much typing they save:

**1. Search the live grant database instead of reading the site.** The `mcp` capability lets the
page call the viewer's own claude.ai connectors. **Kindora Funder Discovery**'s
`search_open_grants` is queried by topic, state, source type, deadline window and minimum award,
and each result loads into intake with one click — funder, deadline, award range, focus areas,
application link, and the notice box seeded with the record. This inverts the original request:
rather than reading a grant-only site and copying from it, query the database those sites
aggregate.

*Granted* was the other candidate and is **deliberately not used** — `search_grants` timed out at
60 s on two separate attempts during the build, so there is no observed response shape to build
against. Worth retrying later; it should not be declared until a real call succeeds.

**What a database record is not.** Kindora returns a *discovery* record: identity, deadline, award
range, focus, link. It carries **no scoring rubric, no required attachments, no page limits and no
cost-share rules** — because those exist only in the funder's own notice. So the seeded text is
explicitly headed `[DATABASE RECORD — not the funder's full notice]` and ends with a line telling
you to paste the real notice beneath it. Letting a rubric score run off a discovery record would
be the worst failure mode this tool has: a confident number derived from nothing.

**2. Read what the URL itself can tell you.** Pasting a notice URL parses out the site (Grants.gov,
GrantWatch, Foundant, HHS, Candid…), the Grants.gov numeric listing id, and the opportunity number
where the URL carries one — `https://www.acf.hhs.gov/grants/open/foa/view/ACF-EX-2027-0042` yields
`ACF-EX-2027-0042`. The record is identified even before the text is in, the link opens in a new
tab, and the site can be saved to the sites list in one click.

**3. A saved sites list.** The grant-only sites the firm actually works from, stored in
`grantdesk/sources` — name, URL, kind, and what each is good for. One click back to the site,
because the last step is always a human copy-paste.

**PDF is now handled in the page** (§4c). True URL-to-*text* still is not, and still belongs in the
skill version (§7), where a script can fetch a URL with no sandbox in the way.

### Connector trade-off, now settled

Declaring `mcp` means **this artifact can no longer be shared publicly** — a connector grant is
viewer-consented and bars public sharing. This was a trade-off; it is now simply the right call.
The desk is explicitly an in-house back office: DMS runs the applications and hands finished
packets to clients, and a client-facing surface comes later, on WordPress, once the tool has been
tweaked into shape. Nothing about the page needs to be shareable for that.

Every failure mode gets its own copy and its own fix, per the capability's failure doctrine —
connector not added, needs reconnecting, duplicate connectors unchosen, blocked by org policy,
declined for this page, upstream timeout. A single "something went wrong" banner is the named
anti-pattern, because it hides the one action that would repair the page.

## 4c. PDF, the pipeline, and the CRM

Three additions that turn the desk from an analyzer into the back office DMS runs grants from.

### PDF reading, in the page

Notices arrive as PDFs. `pdf.js` runs client-side, so unlike fetching a URL this one *is* possible
inside the sandbox: drop a PDF on intake or on the document checker and its text is extracted here,
with line breaks rebuilt from glyph positions so numbered clauses (`5.3`, `IV.7(k)`) survive —
run together, a rubric is unreadable and extraction is worthless.

A scanned PDF yields nothing, and the page says so rather than handing the analysis an empty
string: under 20 words across the document is reported as "very likely a scanned PDF", with OCR as
the fix. Both `pdf.js` and SheetJS are feature-detected, because neither CDN load is guaranteed.

### The three-grant pipeline

Three slots per client — a shortlist that stays a shortlist. Storage is split deliberately:

- the **index** rides on the client record (`title`, `funder`, `deadline`, `status`, both scores),
  so the panel renders three slots without loading three full analyses;
- each slot's **payload** is its own document, `opportunities/<clientId>__<slot>`, holding the
  intake metadata, the notice record and the assessment. Saving one slot never rewrites another,
  and opening one is a single small read.

Status runs considering → writing → submitted → awarded / declined / passed on it. Opening a slot
restores intake, notice and assessment and jumps to the furthest tab that has data.

### CRM import

**HoneyBook works live.** `listClientOrganizations` is the right source because a grant client is
an *organization*, not a contact, and it returns name, type, website, phone, address and private
notes. It runs through `take_action_read_only` on the viewer's own connector.

**FluentCRM has no path from the page, and will not get one.** It is not a claude.ai connector and
it is not in Zapier's catalog at all (searched: zero results). Its REST API lives on the WordPress
site, which the sandbox cannot reach for the same reason it cannot fetch a notice URL. So:

- **now** — FluentCRM contacts come in as a CSV export. The importer resolves company /
  organization / name / first+last columns by header, in that precedence, and falls back to
  substring matching *only after* the exactly-matched columns are excluded (without that, `name`
  matches `first_name` and the import silently drops every surname — caught by a test).
- **properly, later** — FluentCRM *is* WordPress. The client-view page in §7 runs on the same
  install, so the join needs no HTTP at all: a WP endpoint reads FluentCRM's tables directly.
  That is the real integration, and it lands with the WordPress work rather than before it.

Either way, an import brings what a CRM knows — who the client is — and nothing it never held. EIN,
UEI, SAM status and the document registry all arrive `PENDING`, which is precisely the list to go
and ask the client for.

## 5. Data model

One record per client, stored as `grantdesk/clients` in the artifact's own store:

- **identity** — legal name (must match IRS records exactly), DBA, EIN, org type, tax-exempt
  status, NTEE, year established, state of incorporation, addresses, service area
- **federal chain** — UEI, CAGE, SAM status and expiry, Grants.gov status, AOR, E-Biz POC,
  Login.gov holder
- **governance and money** — authorized official, board count, annual budget, FY end, audit
  status, indirect rate, staff
- **narrative raw material** — programs, prior awards and outcomes, partners and what is on file
  for each, data and outcome measurement
- **document registry** — every document, filed against one of the Grant Ready Binder's six tabs,
  with status (`on file` / `pending` / `missing` / `expired` / `n/a`) and a note
- **`regDone`** — the registration chain, seeded from the profile once, then owned by the
  checkboxes because a person looked

Firm-wide rather than per-client, in `grantdesk/sources`: the saved list of grant sites the firm
works from (§4b).

The binder mapping is deliberate: **the gap list is simultaneously the application to-do list and
the build sheet for the Grant Ready Binder we already sell.** The analyzer's output is a work
order for the existing product.

---

## 6. Known limits — read before selling this

1. **Not multi-tenant, by current intent.** All client records live in one document under the
   artifact owner's account. That is correct for the in-house back office this now is. It remains
   **unsafe** for any client-facing version where two clients must not see each other's records —
   so per-client isolation is a precondition of external access, not a later polish. See §7.
2. **The model passes are not deterministic.** Two runs on the same notice can differ at the
   margins. The deterministic layer is the stable part; the rubric self-score is an assessment,
   not a measurement. Caching makes a single session consistent, not two sessions identical.
3. **It does not predict award decisions.** It measures what the file evidences against the
   published rubric. Reviewers, panels and program priorities are not modelled and should never
   be claimed to be.
4. **Extraction quality tracks input quality.** A clean NOFO extracts well. A scanned PDF pasted
   as broken text extracts badly, and the desk will not know it did.
5. **First sheet only** on a workbook in the page. The skill reads every sheet — use it when the
   match detail hides on sheet two.
6. **Scanned PDFs need OCR.** Text PDFs extract in the page; image-only ones are detected and
   refused rather than analyzed as an empty string.
7. **No URL fetching**, ever, in the page — see §4b.
8. **Nothing is filed anywhere.** The desk assesses; a human submits.

---

## 7. Selling it: the packaging and platform path

### What the asset actually is

Not the page. The asset is three things, in order of durability:

1. **the deterministic checkers** — the arithmetic nobody else is doing, portable to any runtime
2. **the prompt set** — extract / assess / check, with the conservative-scoring discipline baked in
3. **the binder mapping** — which ties every finding back to a product DMS already delivers

The UI is the most replaceable part. Build on that assumption.

### Packaging inside the grant package

Three natural tiers, structured by *who operates the tool* rather than by feature count. Prices
are DMS's to set; this document deliberately does not invent them.

| Tier | What the client gets | Who drives the desk |
| --- | --- | --- |
| **Assessment** | one opportunity read, scored, with the gap list and a readiness memo | DMS |
| **Package** | the above plus document checks on the budget and narrative as they are drafted, and the Grant Ready Binder built from the gap list | DMS |
| **Subscription** | rolling opportunity assessments against a maintained client record, with SAM renewal tracking | DMS, client reads the dashboard |

The memo export exists for exactly this: the Markdown readiness memo drops straight into a client
email or into **binder tab 6 (Funding Strategy & Opportunities)**, which is the tab that currently
has the least substance in it. The analyzer fills the weakest page of the existing product.

### Front-facing web page

Do **not** invent a new stack. The *Grant Match Dashboard Spec* already commits to WordPress +
Elementor Pro + ACF Pro, Restrict Content Pro for gating, and a Vercel webhook backend for
PayAnywhere activation. A client-facing Grant Desk should ride that:

- a `grant_assessment` custom post type authored to the client's WP user, exactly as
  `grant_match` already is — the same author-based query filter, the same gating
- the desk's output posted to `/wp-json/wp/v2/grant-assessments` by whoever ran it
- the client's view is **read-only**: score, gap list, what we need from them. Running an
  analysis stays inside DMS, because that is the billable judgment
- **per-client isolation happens here, at the WordPress author boundary** — which is the cheapest
  correct answer to limit §6.1, and needs no rework of the artifact's store

Sequence that matters: the read-only client view first (low risk, immediate sales value), and
client-operated analysis only if there is real demand — the moment a client runs it themselves,
the liability conversation changes and the memo's disclaimer has to become a real term of service.

### Skill version (Claude or ChatGPT)

Worth building, and cheaper than it looks, because the prompts are already written and the
checkers are pure functions. A skill version wins on exactly the places the browser loses:

- **real spreadsheet parsing** — openpyxl/pandas over SheetJS, every sheet not just the first
- **real PDF extraction** — the §6.5 limitation disappears
- **the whole package at once** — point it at a folder and check every attachment in one run
- it composes with the skills DMS already has: `grant-ready-binder` for assembly, `xlsx` and
  `pdf` for the documents, `docx` for the narrative

Shape: `SKILL.md` carrying the prompt set and the scoring discipline, plus `scripts/checks.py` as
a direct port of Layer 0 (§4) with the test case from the example budget as its regression test.
That port is the highest-value next piece of work in this whole document — it makes the
arithmetic reusable everywhere and testable in CI.

### Sequenced roadmap

1. ~~Port Layer 0 to Python~~ — **done**: `.claude/skills/grant-desk-intake/scripts/grant_checks.py`,
   13 passing tests over the planted-defect budget
2. ~~Save the analyzed opportunity per client~~ — **done**: the three-slot pipeline (§4c)
3. ~~Skill version~~ — **done**: `grant-desk-intake`, composing with `grant-ready-binder`
4. Read-only client view on the existing WordPress stack — and the FluentCRM join lands here (§4c)
5. ~~Opportunity discovery~~ — **done**: Kindora live search on intake (§4b). Still open: retry
   *Granted* once its search tool stops timing out, and add URL/PDF fetching in the skill version
   where no sandbox blocks it
6. Client-operated analysis, only behind a real term of service

---

## 8. Design notes

Brand comes from the Grant Ready Binder rather than the Bid Desk, so the two desks read as
siblings from the same firm rather than the same page twice: navy `#1F3A5F` and gold `#C9A227`
on warm archival paper in light, a navy night in dark; Newsreader for display against the Bid
Desk's Spectral, IBM Plex Sans and Mono shared with it.

Gold is spent on two things only — the rubric and deadline urgency. Pass / needs-work / fail are
semantic, separate from the accent, and never carry meaning without a label beside them.
