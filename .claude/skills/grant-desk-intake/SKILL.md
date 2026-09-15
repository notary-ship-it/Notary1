---
name: "grant-desk-intake"
description: "Read a grant notice (NOFO, RFA, foundation RFP) from a PDF or text, extract its deadlines, eligibility gates, scoring rubric and required attachments, score a client against it, and check a grant budget or narrative before submission. Use whenever Delaware Mobile Signings is working a grant for a client: a notice PDF to read, a rubric to score against, a budget spreadsheet to check, a narrative to check against a page limit, or a question about what a client still needs in order to apply. Also use when asked to prepare input for the DMS Grant Desk."
---

# Grant Desk Intake

The desk's reading and arithmetic, outside the browser. Use this when the work starts
from **files on disk** — a notice PDF, a budget workbook, a draft narrative — which is
where the published Grant Desk page cannot help, because a browser page cannot open a
local PDF folder or parse every sheet of a workbook.

Companion to the **grant-ready-binder** skill: that one assembles the client's binder,
this one decides what belongs in it for a given opportunity.

## The discipline that makes this worth anything

Three rules. They are not style preferences — breaking them produces confident output
that is wrong in the direction the client wants to hear.

1. **Unverified is never satisfied.** A field nobody has confirmed is `PENDING`, and
   `PENDING` scores as unsupported. Never credit a registration, credential, insurance
   limit or document that the record does not actually state.
2. **Arithmetic and judgment are reported separately.** `scripts/grant_checks.py`
   computes; you read. Never present a computed finding as your opinion or your opinion
   as computed. Never recompute by hand what the script already did.
3. **Score what the file evidences today, not what it could say.** A 20-point evaluation
   criterion does not score 15 because the client is capable of collecting data. It
   scores what a reviewer would find.

## 1. Read the notice

```bash
python3 scripts/grant_checks.py pdf NOTICE.pdf > notice.txt
```

Prefers `pdfplumber`, falls back to `pypdf`. If it warns that it found almost no text,
the PDF is scanned images — say so and ask for OCR or the text from the source posting.
Do not analyze an empty extraction. For a heavily formatted notice, the **pdf** skill
has better table handling; reach for it when clause tables matter.

Then extract the record. Return JSON only, no prose, matching:

```
{ opportunityNumber, title, funder, program, assistanceListing, opportunityType,
  contacts:{programOfficer:{name,phone,email}, grantsManagement},
  dates:{letterOfIntent, questionsDeadline, applicationDeadline, deadlineTime, timezone,
         awardNotice, projectStart},
  award:{totalProgramFunding, expectedAwards, ceiling, floor, projectPeriod, budgetPeriods},
  costShare:{required, percent, basis, inKindAllowed, notes},
  indirectCost:{policy, capPercent, deMinimisAllowed, notes},
  eligibility:[{requirement, hard, citation}], ineligibleEntities[],
  submission:{portal, pageLimit, pageLimitAppliesTo, font, spacing, margins, fileFormat,
              fileNamingRules, abstractLimit, otherLimits[]},
  requiredForms:[{name, note, citation}], requiredAttachments:[{name, note, citation}],
  reviewCriteria:[{criterion, points, whatReviewersLookFor, subElements[], citation}],
  bonusPoints:{available, points, basis},
  scoreThresholds:{minimumScore, historicalFundedScore, notes},
  unallowableCosts[], reportingRequirements[], redFlags[], competitiveNotes }
```

Rules that matter:

- **`reviewCriteria` is the point of the extraction.** One entry per scored criterion,
  its point value as a number when stated (null otherwise), and `whatReviewersLookFor`
  in the notice's own terms — including any sentence saying what will *not* score well.
- Cite the section for every requirement, criterion and attachment (`§5.3`, `IV.7(k)`).
- Not stated means `null`. Never infer a page limit, a match percentage or a deadline.
- `hard: true` only for a gate that disqualifies outright — entity type, status,
  geography, one-application limits, unresolved audit findings.
- Keep government forms (SF-424 family, certifications) separate from attachments the
  applicant writes.
- Red-flag: a deadline under 30 days out, an unwaivable match, a registration the client
  may not hold, a stated minimum score, and any date already past.

## 2. Score the client

Score each criterion conservatively (rule 3 above) and report per criterion: max points,
points the file supports **today**, what a reviewer would not find, points reachable
before the deadline, and the specific artifact that earns them. Name the artifact, not
the aspiration — *"name the literacy curriculum and its dose (sessions/week × weeks)"*,
never *"strengthen the approach"*.

Report **two separate scores**, never one blended number:

- **Projected reviewer score** — sum of supported points. Competitiveness.
- **Readiness index** /100 — registrations 25, required attachments 25, financial
  documentation 20, narrative evidence 20, capacity and partners 10. Deliverability.

### The registration runway

Federal registrations run in sequence and cannot be hurried. Sum the lead time still
outstanding and compare it to the days remaining:

| Step | Lead | Why |
| --- | --- | --- |
| EIN letter in hand, name matching IRS records exactly | 0 | SAM rejects any mismatch |
| SAM.gov registration active | ~21 d | entity validation is the usual hold-up |
| UEI issued | 0 | comes with the SAM registration |
| Grants.gov applicant profile | ~3 d | needs the E-Biz POC to exist |
| AOR authorized by the E-Biz POC | ~5 d | **most missed deadlines die here** |
| Workspace created, forms downloaded | ~1 d | confirms the real attachment slots |
| Submitted early enough to clear validation | ~3 d | a rejected package needs time to fix |

**If the chain is longer than the calendar, the recommendation is NO-GO** however strong
the program is. The useful advice is then: clear the chain now, apply next cycle.

## 3. Check the documents

Run the arithmetic first, always, and hand its output into your reading rather than
redoing it.

```bash
python3 scripts/grant_checks.py budget BUDGET.csv \
    --cap 10 --match 25 --ceiling 500000 --floor 150000 --json

python3 scripts/grant_checks.py narrative NARRATIVE.pdf \
    --page-limit 30 --spacing double --font "12-point Times New Roman" \
    --sub-element "baseline values" --sub-element "data collection methods"
```

Pass the notice's real figures from step 1. Exit status is 1 when anything is a blocker.
For `.xlsx`, convert every sheet first (the **xlsx** skill) — the script takes CSV, and
a workbook's later sheets are where the match detail usually hides.

The script checks: row cross-footing, column footing block by block, a labelled rate
against its base, indirect against the cap, cost share against the requirement, the
request against ceiling and floor, duplicate labels, blanks and negatives; and for
narratives: word and page count against the limit, placeholder text, and a keyword scan
against the criterion's sub-elements.

**Then read what arithmetic cannot decide**: is every line allocable to a stated
activity, is the basis of each figure given, is the match documented or merely asserted,
does the narrative answer every sub-element in the criterion's own order with specifics
rather than intentions. Report these separately from the script's findings.

Severity: **blocker** = the notice would reject it or a reviewer would score it near
zero; **fix** = it costs real points; **note** = worth tightening if there is time.
`where` must let someone find it — a line item label, a heading, a quoted phrase, never
"throughout". If a document is solid, say so; do not invent problems.

## 4. File the gaps against the binder

Every missing item belongs to one of the Grant Ready Binder's six tabs, so the gap list
doubles as the binder's build sheet:

1 Organizational · 2 Tax-Exempt · 3 Financial · 4 Federal Registration ·
5 Authorized Official & Governance · 6 Funding Strategy & Opportunities

For each: the item, its tab, why it is needed, whether it **blocks submission**, a
realistic lead time in days, and an owner. Hand off to **grant-ready-binder** to
assemble. The readiness memo belongs in tab 6.

## Output

Unless asked otherwise, produce: the recommendation (GO / GO WITH WORK / NO-GO) with a
2–5 sentence rationale, both scores, the eligibility gates with evidence, the rubric
table, the gap list by binder tab, and the registration runway verdict. If NO-GO, the
first sentence says plainly why to walk away.

Everything here is an internal assessment of what a client's file evidences. It is not a
prediction of the funder's decision, and should never be presented as one.

## Tests

`python3 scripts/test_grant_checks.py` — 13 tests over an example budget carrying three
planted defects. If they fail, the arithmetic has drifted from the Grant Desk page's and
the two will disagree about the same spreadsheet.
