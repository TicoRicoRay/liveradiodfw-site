# Approval workflow

**Purpose:** Let Ray approve proposed show descriptions with a single email reply, instead of convening a Jarvis session for every new show.

**Status:** Part A shipped 2026-04-23 AM. Part B queued. Part C deferred.

**Primary references:** [B32](../bugs.md#b32-no-low-friction-path-to-approve-proposed-show-descriptions) (defect), [R25](../roadmap.md#r25-reply-to-approve-workflow-for-show-descriptions) (roadmap with full three-part plan).

---

## The problem

The daily calendar sync (`sync_runner.py` on Ray's Windows box) flags any new public show that is missing its About-this-show description and emails `info@liveradiodfw.com` a machine-generated draft under "Proposed description draft." Ray reads that email in Outlook on his iPhone or in a desktop browser. Until 2026-04-23 there was no way to move that draft text into `shows.json[show].description` without opening a Jarvis session and pasting it. For the common case where the draft is already good enough, that is pure ceremony.

Cardinal rule: Ray approves before publish. We are not removing the approval step. We are making it cheap.

---

## System shape

```
Google Calendar (source of truth for schedule)
        |
        v
  8:00 AM Central -- Windows Task Scheduler -- sync_runner.py
        |
        | writes shows.json, commits to master, pushes
        v
  liveradiodfw-site / master -- GitHub Pages rebuild -- www.liveradiodfw.com
        |
        | if any public show is missing description:
        v
  SMTP (Gmail app password) -- send_alert_email()
        |
        v
  info@liveradiodfw.com  <-- Ray reads in Outlook
        |
        | Ray replies via mailto APPROVE / EDIT link
        v
  [Part B, not yet shipped] IMAP poller on Windows box
        |
        | matches subject token, writes shows.json, commits as "Ray"
        v
  liveradiodfw-site / master  (same channel as the sync)
```

---

## Part A -- shipped 2026-04-23 AM

### What it does

1. `sync_lib.approval_token(show, draft)` returns a stable 12-char sha256 prefix of `date|venue|draft`. Same inputs always produce the same token; any change to the draft text invalidates the token, which correctly invalidates any stale pending approval.
2. `sync_lib.build_approval_email_section(show, draft, alert_email)` renders the MISSING-INFO block for a description-missing show. Output is plain text (what `EmailMessage.set_content()` sends). Contains:
   - The show title and date.
   - The full draft.
   - A `mailto:` link pre-addressed to `alert_email` with subject `APPROVE <token>`.
   - A `mailto:` link pre-addressed to `alert_email` with subject `EDIT <token>` and a pre-filled body containing the draft wrapped with a `TOKEN: <token>` line so Part B can separate token from edited text.
   - The bare token (for Part B reference and debugging).
3. `sync_runner.py` imports the new helper and delegates to it whenever the missing field is the description AND a usable draft was produced. Falls back to the legacy plain block for other missing fields and for cases where a draft could not be produced (private show, missing venue/city, TBA time).
4. `approvals/pending.json` scaffolded in the site repo with the schema Part B will write. Empty list today.
5. `test_description_handling.py` extended with 6 cases covering token stability, cross-show invariance, cross-draft invariance, APPROVE and EDIT mailto presence, ASCII-only gate, and em-dash / smart-quote gate.

### What it does NOT do

- Nothing parses replies yet. Part B is where that lives.
- Nothing writes `shows.json`. Part B does that too.
- Nothing expires pending approvals. Part B handles expiry.

Until Part B ships, an APPROVE reply goes to `info@` and sits there. Ray can forward it to Jarvis in a session and Jarvis applies it manually.

### Why mailto with token in subject, not plus-subaddressing or query-only

- Token-in-subject does not depend on the mail host supporting plus-subaddressing (`info+approve-<token>@`). Microsoft 365 supports it, but relying on it means any future delegate mailbox on a different host could break silently.
- Token-in-subject survives mail-client quirks. Outlook iOS, Outlook web, Apple Mail, and Gmail all produce a reply whose subject starts with the original subject. Some clients strip query parameters from mailto URLs but all preserve the subject.
- Subject matching is trivial on the Part B side: regex for `^(?:Re:\s*)?(APPROVE|EDIT)\s+([a-f0-9]{12})\b`.

### Why plain text, not HTML

- `EmailMessage.set_content()` produces text/plain. HTML would require `add_alternative()` plus careful multipart structuring, plus rendering defenses against Outlook's HTML rewriting.
- All mainstream clients auto-linkify bare `mailto:` URLs in plain text. The resulting user experience is visually less pretty than styled buttons but functionally identical: tap the link, the mail composer opens pre-addressed with the correct subject, tap send.
- Plain text is forgiving. It survives quoting, forwarding, mobile-client re-wrapping, and copy-paste in a way HTML does not.

---

## Part B -- planned, not yet shipped

### Goal

A `process_approvals.py` script on Ray's Windows box, running every 15 minutes via a second Windows Task Scheduler task, that polls `info@liveradiodfw.com` over IMAP and consumes APPROVE / EDIT replies.

### Inputs

- `pending.json` (site repo, master). Read to find what tokens are currently awaiting a reply. Written to remove consumed tokens.
- IMAP mailbox at `info@liveradiodfw.com`. Read-only on inbox; mark messages read after consumption.
- Local clone of `liveradiodfw-site` at `C:\Tools\LiveRadioDFW\liveradiodfw-site\`. Git pull, edit `shows.json`, commit as "Ray", push.

### Trust boundary

Ray is the only person with access to `info@liveradiodfw.com` today. Sender allowlist on replies: `info@liveradiodfw.com` (self-sent; Outlook preserves this when Ray replies to himself) and `rmyers@futurebright.com` (Ray's personal address in case he reads from there). Any other sender is rejected and logged.

### Cardinal-rule gate

Any reply that would write to `shows.json` goes through a pre-commit gate:
- Must be pure ASCII.
- Must not contain em-dash (U+2014), en-dash (U+2013), or smart quotes (U+2018-U+201D).
- Must not contain HTML tags.
- Must be between 50 and 2000 characters.

Gate violations reject the reply and send a short failure email back to `info@` explaining the violation so Ray can resubmit. No partial writes, no silent normalization.

### APPROVE path

1. Parse subject: extract token.
2. Look up token in `pending.json`. If not found: log, discard.
3. Load the draft from the pending entry (not from the reply body, to guarantee no Outlook-introduced character changes).
4. Run cardinal-rule gate on the draft (should always pass since sync_lib generated it, but defense in depth).
5. `git pull`, load `shows.json`, set `shows[match].description = draft`, write.
6. Commit as "Ray <rmyers@futurebright.com>" with message `Approved description: <venue> <date> (<token>)`.
7. Push to `master`.
8. Remove token from `pending.json`. Append entry to `approvals/log.json`.
9. Send a short confirmation email back to Ray with the commit URL.

### EDIT path

1. Parse subject: extract token.
2. Parse body: find the `TOKEN: <token>` marker. Everything after that line is the edited description.
3. Verify subject token matches body token; reject on mismatch.
4. Look up token in `pending.json`. If not found: log, discard.
5. Run cardinal-rule gate on the edited text.
6. Same git pull / edit / commit / push / log flow as APPROVE, but `message = "Edited approval: ..."`.

### Expiry

Pending tokens are dropped after 30 days. The next sync after expiry will re-generate the same token (since `sha256(date|venue|draft)` is stable) and re-surface it in the alert email, so no intent is lost.

### Second Task Scheduler task

Same pattern as `LiveRadioDFW Daily Calendar Sync` (B7 Part 2 install), but triggers every 15 minutes instead of daily at 8 AM. Same "run only when user logged on" constraint applies until R24 is resolved; acceptable for the same reasons (Ray lives on this machine).

---

## Part C -- deferred

Stage 2 of B16.2 (auto-publish without approval) becomes realistic only after Part B has been exercised 5+ times and the approve-vs-edit ratio is known. Currently zero data points. Decision deferred until data is available.

---

## Cardinal rules honored in this design

- Approval remains human-in-the-loop. Cardinal rule.
- ASCII only / no em-dashes. Enforced in sync_lib generator, enforced in Part B gate, tested in `test_description_handling.py`.
- Non-destructive merge. Part B never rewrites fields other than `description`.
- Central time references only. All timestamps in commit messages and log files use `America/Chicago` or the literal string `Central`.
- Verify SSL within 30 minutes of any deploy-adjacent change. Part A does not change DNS or TLS surface; no SSL verification required for this shipment.
- No content duplicated across repos. sync_lib stays in liveradiodfw-site; sync_runner stays in liveradiodfw-marketing; `pending.json` lives only in liveradiodfw-site.

---

## History

- 2026-04-23 AM: Part A shipped. File created.
