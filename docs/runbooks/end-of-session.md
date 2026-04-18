# End-of-session workflow

_When Ray says "wrap up," "close out the thread," "end of session," or similar, run this checklist before the thread is abandoned._

This runbook exists so Ray can use a short prompt like **"Jarvis, wrap up"** instead of listing every step. At that point in the thread you already have full context, so all you need is the trigger.

---

## Checklist

### 1. Capture anything new from this session

Walk back through the session. For each item surfaced:

- **New defect?** → add to [bugs.md](../bugs.md) with next `B<n>` number, following the "How to add" template at the top of that file.
- **New Jarvis blind spot observed?** → add to [bugs.md](../bugs.md) with next `J<n>` number.
- **New planned work / enhancement?** → add to [roadmap.md](../roadmap.md) with next `R<n>` number, following that file's "How to add" template.
- **New item that needs Ray+Jarvis discussion before triage?** → add to the "Pending discussion" section of [project-plan.md](../project-plan.md) with next `D<n>` number.
- **Bug closed this session?** → remove from its open-bugs section in `bugs.md` and add a one-line entry to the "Fixed recently" section at the bottom.

If you are unsure whether something is a defect, a roadmap item, or noise: **ask Ray before writing the entry.** A half-complete entry is worse than no entry.

### 2. Update `docs/project-plan.md`

All three of these, every time:

- **Refresh the `_Last updated:_` timestamp** at the top of the file. Use Central time, format `YYYY-MM-DD · H:MM AM/PM Central`.
- **Rewrite the "Pick up here next session" context paragraph** to describe what this session actually accomplished. Be specific. The paragraph should read like a briefing to a cold agent who has no memory of the session.
- **Refresh the "Top priorities right now" list.** Add newly-surfaced priorities, remove items closed this session, reorder if priorities shifted.
- **"Recently closed" subsection:** add any bugs closed this session (one-liner each).

### 3. Update architecture docs if anything structural changed this session

If the session changed anything about how the system is wired - not just content edits - update the relevant architecture doc in `docs/architecture/` before committing. This is how `architecture/` stays current instead of drifting into fiction.

Check each of these against what happened this session:

- **New, changed, or deleted scheduled task / cron?** Update [`architecture/scheduled-tasks.md`](../architecture/scheduled-tasks.md). One-shot session timers are not scheduled tasks for inventory purposes - only durable recurring jobs count.
- **New connector connected, or existing connector's identity/use changed?** Update [`architecture/connectors.md`](../architecture/connectors.md). Classify into active-band-use / available-if-needed / off-limits / not-band-relevant. If the new connector shares identity with an off-limits account (EOS, personal health, etc.), it goes straight to the off-limits section.
- **Change to where a data type lives** (calendar host, contact system, DNS, hosting, repo layout)? Update [`architecture/sources-of-truth.md`](../architecture/sources-of-truth.md).
- **Change to the calendar-sync pipeline** (webhook, `sync_calendar.py`, ticket-price parser, merge behavior)? Update [`architecture/calendar-sync.md`](../architecture/calendar-sync.md).
- **Change to the monthly availability email pipeline**? Update [`architecture/marketing-automation.md`](../architecture/marketing-automation.md).

If nothing structural changed, skip this step. If unsure whether something counts as structural, ask Ray - a missed update is worse than a one-line "no change."

### 4. Commit and push

One commit is fine if the changes are related. Otherwise use separate commits. Standard format:

```
docs: <what changed>
```

Push to the `docs` branch. Always use the LiveRadioDFW identity:

```
git -c user.name="LiveRadioDFW" -c user.email="info@liveradiodfw.com" commit -m "..."
git push origin docs
```

### 5. Confirm with Ray

Reply to Ray with:
- One-line summary of what was added/updated/closed
- Commit SHA(s) as clickable links to the GitHub commit page
- Any open questions or items Ray still needs to act on outside the thread

### 6. Sanity-check the thread itself

Before Ray leaves, note whether any of these failed this session (if yes → they become new `J<n>` entries for the next cold-start test):

- Jarvis self-identified as Jarvis, called the user Ray
- 60-min timer auto-started without Ray asking
- Docs were read before acting
- Any new bug/roadmap entry followed the template
- Cardinal rules respected without being re-told (EOS calendar untouched, "Central" not CDT/CST, no em-dashes, no "15 minutes" estimates, GCal = source of truth for shows, Mailchimp = venue contacts, Cloudflare = DNS)

---

## The short prompt Ray can use

Ray only needs to type one of these — Jarvis has full session context at that point and runs this runbook:

- **"Jarvis, wrap up."**
- **"End of session — run the close-out checklist."**
- **"Close out the thread."**

If the thread has memory-triggered on "Live Radio DFW" but the agent doesn't know what "wrap up" means, Ray can add `see docs/runbooks/end-of-session.md` to the prompt.
