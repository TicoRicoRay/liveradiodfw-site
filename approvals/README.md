# approvals/

Scaffolding for the reply-to-approve show-description workflow (B32 / R25).

## Files

- `pending.json` - queue of pending approvals. Written by Part B's
  `process_approvals.py` (next session) when the daily sync emails a draft.
  Read and consumed when Ray replies `APPROVE <token>` or `EDIT <token>`
  from `info@liveradiodfw.com`.

## Why this lives in the site repo and not the marketing repo

The source of truth for `shows.json` is the site repo. Approval state is
shows-adjacent data: when a token is consumed, the resulting write is
`shows.json` on `master`. Keeping `pending.json` in the same repo lets
Part B's processor run a single git pull / write / commit / push without
cross-repo coordination.

## Part A (2026-04-23) status

Only the scaffold exists. The daily sync alert email (sync_runner.py on
the Windows box) now emits APPROVE / EDIT mailto links with tokens, but
nothing reads replies yet. Until Part B lands, Ray forwards approval
replies to Jarvis in a session and Jarvis applies them to `shows.json`
manually.

## Part B preview

`process_approvals.py` will run every 15 minutes on the Windows box via
Task Scheduler, poll `info@liveradiodfw.com` over IMAP, match reply
subjects against `pending.json` tokens, and on match:

- APPROVE -> write the draft as-is to `shows.json[show].description`,
  commit as "Ray", push to master, mark token `approved`.
- EDIT -> parse everything after `TOKEN: <token>` in the reply body as
  the final description, write to `shows.json[show].description`,
  commit as "Ray", push to master, mark token `edited`.

Cardinal-rule gates (ASCII only, no em-dashes) will be enforced before
write; any rule violation rejects the reply and sends a short failure
email back so Ray can resubmit.
