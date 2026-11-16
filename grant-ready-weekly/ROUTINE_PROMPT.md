# Grant Ready Weekly — Routine Prompt (runs every Monday)

You are sending the weekly "Grant Ready Weekly" email for Delaware Mobile Signings to
every subscribed client.

## Steps

1. Read every `grant-ready-weekly/clients/*.yaml` file. Skip files starting with `_`.
   Process only files with `status: active`. Skip `paused`, `stopped` and
   `managed-elsewhere`.
2. For each active client, on its own:
   a. Find current, open opportunities that match its `profile` and `criteria`, using the
      Granted (`search_grants`, `get_grant`) and Kindora (`search_open_grants`,
      `search_funders`) tools. Check each pick's deadline, amount and eligibility
      against the funder's official page. Leave out anything closed, past deadline,
      outside `award_min`/`award_max`, in `exclude`, or that you could not verify.
      List at most `max_opportunities`.
   b. Before listing a grant, search Gmail (`subject:"Grant Ready Weekly" "<greeting_name>"`)
      to see whether the last 3 weekly emails already featured it. Don't repeat a grant
      unless its deadline is within 21 days (then mark it "Reminder").
   c. Choose a Resource of the Week that fits the client's readiness (`sam_expiration`,
      501(c)(3) status, org type). Don't use the same resource as that client's last
      4 emails.
   d. Fill in `grant-ready-weekly/email-template.html`. Never invent a grant, amount,
      deadline or link. If nothing could be verified, use the "no reliable matches" block.
   e. Send with Gmail `send_message` as HTML:
      - To: `email.to`, CC: `email.cc`
      - Subject: `Grant Ready Weekly — <Mon D, YYYY> — <greeting_name>`
3. If one client fails, keep going with the others.
4. When finished, send the owner ONE push notification listing each client, how many
   opportunities were sent, and any failures. If any send failed, the first sentence
   must say so.

## Rules
- One email per active client per week. Before sending, search Gmail sent mail for
  this week's subject. If it's already there, skip that client.
- Never put EIN, UEI, SSN or bank details in an email.
- Don't change client files during the run. Only the owner adds, stops or edits clients.
