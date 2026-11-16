# Grant Ready Weekly — Multi-Client Subscription System

A copy of the Plain Truth Baptist Church "Grant Ready Weekly" routine, built so it
works for **any number of subscribing clients**. You only set up one weekly routine.
Each client is one small file in `clients/`.

## How it works

1. Every Monday the routine runs `ROUTINE_PROMPT.md`.
2. It reads every file in `clients/` whose `status` is `active`.
3. For each one it looks up matching grants using that client's criteria, then sends
   that client its own branded email using `email-template.html`.
4. Clients marked `stopped` or `paused` get no email.

## Day-to-day commands (just say these to Claude)

| You say | Claude does |
|---|---|
| "New Grant Ready subscriber: **[client name]**, contacts …, criteria …" | Copies `clients/_TEMPLATE.yaml` to `clients/<client-slug>.yaml`, fills it in, sets `status: active`, commits and pushes. The client gets an email starting the next Monday. |
| "Stop Grant Ready for **[client name]**" | Sets `status: stopped` and fills in `stopped_on`. Emails end the following Monday. The file stays as a record. |
| "Pause / resume **[client name]**" | Sets `status: paused` or back to `active`. |
| "Change criteria for **[client name]** …" | Edits that client's file. |

## Information needed for a new client

- Legal name and the name used in the greeting
- Contact emails (CC'd), plus the To address (defaults to you)
- Organization type (church / nonprofit / small business / etc.), state and county
- Funding focus areas and keywords
- Award size range, and any exclusions (for example, "no loans", "no federal")
- Readiness facts: SAM/UEI status, 501(c)(3) status, EIN on file (yes/no only — no numbers)

## Setup (once)

Point one weekly scheduled routine (Mondays) at this prompt:

> Run the Grant Ready Weekly routine exactly as written in
> `grant-ready-weekly/ROUTINE_PROMPT.md` in the notary-ship-it/Notary1 repo.

**Plain Truth Baptist Church:** `clients/plain-truth-baptist-church.yaml` is included
with `status: managed-elsewhere`, so this system skips it while the original routine
keeps running. To move Plain Truth onto this system, change it to `active` and turn off
the old routine, so the church doesn't get two emails.
