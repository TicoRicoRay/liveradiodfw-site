# Runbook: Publishing the Calendar Webhook (Apps Script)

_How Ray publishes a new version of the `LiveRadioDFW Calendar` Google Apps Script webhook after the code on the `docs` branch changes._

Jarvis cannot push to Google Apps Script directly. This step is manual until Apps Script's `clasp` CLI (or equivalent) is wired up.

---

## Source of truth

- **Master copy (editable, reviewable, committed):** [`docs/scripts/LiveRadioDFWCalendar.gs`](../scripts/LiveRadioDFWCalendar.gs) on the `docs` branch of `TicoRicoRay/liveradiodfw-site`.
- **Deployed copy (what actually runs):** the Apps Script project **"LiveRadioDFW Calendar"** at [script.google.com](https://script.google.com), owned by the Google account `info@liveradiodfw.com`.

The master copy must always be **functionally identical** to the deployed copy except for one intentional difference: the master copy has the passphrase redacted to `'__REPLACE_BEFORE_DEPLOY__'`. The deployed copy has the real passphrase. The real passphrase lives in Ray's password manager and (today) also inside `sync_calendar.py` on the `gh-pages` branch. See [bugs.md B7](../bugs.md#b7-webhook-passphrase-and-url-are-publicly-readable-on-the-live-site) for the ongoing work to stop putting the real passphrase on `gh-pages`.

---

## When to run this runbook

Any time `docs/scripts/LiveRadioDFWCalendar.gs` changes on the `docs` branch. Common triggers:

- Jarvis proposed a fix (e.g. R10 extends `_updateEvent` to honor attendees).
- A new action is added (e.g. a fifth action beyond list/create/update/delete).
- A behavior change in an existing action.
- A security change (e.g. rotating the passphrase, adding an IP allow-list).

Do **not** run this runbook just to reformat the master or adjust comments. Keep functional changes and cosmetic changes in separate docs-branch commits so the diff you paste below is small and reviewable.

---

## Before you start

- [ ] Confirm the master copy compiles cleanly in your head (or in a diff review with Jarvis).
- [ ] Note the passphrase location: password manager → entry `LiveRadioDFW Calendar webhook passphrase`. Do NOT copy it into any repo file, chat, or note.
- [ ] If you are rotating the passphrase in this publish, also plan to update `sync_calendar.py` on `gh-pages` in the same batch. Everything breaks if these drift.

---

## Steps

### 1. Open the Apps Script project

1. Open a browser and sign in as `info@liveradiodfw.com`.
2. Go to [script.google.com](https://script.google.com).
3. Open the project **"LiveRadioDFW Calendar"**.

If you don't see the project, you're signed in as the wrong Google account. The project does not exist on rmyers@futurebright.com, ray.myers@eosworldwide.com, or any other account.

### 2. Copy the master code

1. In your local clone of `liveradiodfw-site` on the `docs` branch, open `docs/scripts/LiveRadioDFWCalendar.gs`.
2. Select all, copy.
3. In the Apps Script editor, open the `Code.gs` (or equivalently-named) file.
4. Select all, paste.

### 3. Restore the real passphrase

1. Find the line `const PASSPHRASE = '__REPLACE_BEFORE_DEPLOY__';`
2. Replace `'__REPLACE_BEFORE_DEPLOY__'` with the real passphrase string from your password manager.
3. Leave the single quotes and semicolon exactly as they are.

**Do not** save a copy of the pasted code with the real passphrase anywhere else. When you're done, close the tab \u2014 don't accidentally paste the real passphrase into Slack, chat, a notepad, or another file.

### 4. Save and deploy

1. Save (\u2318/Ctrl + S).
2. In the top-right, click **Deploy** \u2192 **Manage deployments**.
3. Find the existing deployment (it will be a Web App deployment whose URL matches the one in `sync_calendar.py`).
4. Click the pencil (Edit) icon.
5. In the **Version** dropdown, select **New version**.
6. Add a short description, e.g. `R10: _updateEvent honors attendees`.
7. Leave **Execute as** and **Who has access** unchanged (changing these can break `sync_calendar.py`'s ability to call the webhook). Typical values: Execute as = "Me (info@liveradiodfw.com)", Who has access = "Anyone".
8. Click **Deploy**.

The deployment URL does **not** change when you publish a new version of an existing deployment. The URL only changes if you create a new deployment from scratch \u2014 don't do that unless you also plan to update `sync_calendar.py`.

### 5. Smoke-test

From any shell with `curl`:

```bash
curl -sSL -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "{\"passphrase\":\"$PASSPHRASE\",\"action\":\"list\"}" | head -c 500
```

(Use environment variables or paste inline \u2014 don't commit.)

Expected: `{"status":"ok","events":[...]}`.

If you get `{"status":"error","message":"bad passphrase"}`, you pasted the redacted master without restoring the passphrase. Go back to step 3.

If you get HTML instead of JSON, the deployment failed or the URL is wrong. Check step 4.

### 6. Log the publish

In the same `docs`-branch commit that landed the master-code change (or a follow-up commit), append a line to the **deployment log** at the bottom of `docs/scripts/LiveRadioDFWCalendar.gs`:

```
// Deployed: YYYY-MM-DD HH:MM Central \u2014 <short description> \u2014 by Ray
```

This gives us a trail of which master-copy revision corresponds to which deployed version.

---

## Rollback

If the new deployment is broken:

1. **Fast rollback:** in Apps Script \u2192 Deploy \u2192 Manage deployments, edit the Web App deployment, switch the **Version** dropdown back to the previous version, click Deploy.
2. Open a `docs`-branch fix for the master code. Do not leave the master and deployed copies diverged for more than one session \u2014 future-Jarvis will trust the master and mis-diagnose.

---

## What NOT to do

- **Never** commit the real passphrase to any branch of any repo.
- **Never** edit directly in the Apps Script editor without also updating the master copy on the `docs` branch in the same session. Drift between the two is how root-cause investigations go bad.
- **Never** publish from a branch other than `docs`. The master copy lives on `docs` only.
- **Never** change the deployment URL without updating `sync_calendar.py` on `gh-pages` in the same batch.

---

## Related

- [architecture/calendar-sync.md](../architecture/calendar-sync.md) \u2014 overall data flow.
- [architecture/sources-of-truth.md](../architecture/sources-of-truth.md#shows--gigs) \u2014 canonical statement that info@ owns the calendar.
- [bugs.md B2](../bugs.md#b2-webhook-attendees-field-is-a-silent-no-op) \u2014 attendee no-op, root cause in `_updateEvent`.
- [bugs.md B3](../bugs.md#b3-outlook-native-event-ids-cant-be-updated-via-the-webhook) \u2014 Outlook-native event IDs.
- [bugs.md B7](../bugs.md#b7-webhook-passphrase-and-url-are-publicly-readable-on-the-live-site) \u2014 passphrase exposure on gh-pages.
- [roadmap.md R10](../roadmap.md#r10-extend-_updateevent-to-honor-attendees) \u2014 pending attendee-support change.
