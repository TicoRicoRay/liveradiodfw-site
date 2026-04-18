/**
 * LiveRadioDFW — Google Calendar Webhook
 * Allows external systems to create, update, and delete events
 * on the band's Google Calendar via HTTP POST.
 *
 * PASSPHRASE must match on every request.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * CANONICAL MASTER COPY
 * ─────────────────────────────────────────────────────────────────────────────
 * This file is the source of truth for the webhook code. The DEPLOYED version
 * runs at script.google.com, owned by the Google account info@liveradiodfw.com,
 * project name "LiveRadioDFW Calendar".
 *
 * Calendar: info@liveradiodfw.com (free Google personal account on the band
 * domain; MX stays on Microsoft 365, Google account is for Calendar only).
 *
 * PUBLISH WORKFLOW
 * Jarvis cannot publish Apps Script changes. Follow docs/runbooks/
 * publish-calendar-webhook.md to push a change from this file to the deployed
 * web app. Never edit the Apps Script editor directly without also updating
 * this file — the repo master and the deployed script must stay in sync.
 *
 * PASSPHRASE
 * The real passphrase is NEVER committed to this public repo. The constant
 * below is a placeholder. Before deploying, replace it with the real value
 * from Ray's password manager. After saving and deploying, DO NOT paste the
 * real value back into this file when updating the repo master.
 */

const PASSPHRASE = '__REPLACE_BEFORE_DEPLOY__';
const CALENDAR_ID = 'info@liveradiodfw.com';

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);

    if (data.passphrase !== PASSPHRASE) {
      return _json({ error: 'Unauthorized' }, 401);
    }

    const action = data.action; // "create", "update", "delete", "list"

    if (action === 'create') {
      return _createEvent(data);
    } else if (action === 'update') {
      return _updateEvent(data);
    } else if (action === 'delete') {
      return _deleteEvent(data);
    } else if (action === 'list') {
      return _listEvents(data);
    } else {
      return _json({ error: 'Unknown action: ' + action }, 400);
    }
  } catch (err) {
    return _json({ error: err.message }, 500);
  }
}

function _createEvent(data) {
  const cal = CalendarApp.getCalendarById(CALENDAR_ID);
  if (!cal) return _json({ error: 'Calendar not found' }, 404);

  const start = new Date(data.start);
  const end = new Date(data.end);
  const event = cal.createEvent(data.title, start, end, {
    description: data.description || '',
    location: data.location || '',
    guests: (data.guests || []).join(','),
    sendInvites: false
  });

  return _json({
    status: 'created',
    eventId: event.getId(),
    title: data.title,
    start: start.toISOString(),
    end: end.toISOString()
  });
}

function _updateEvent(data) {
  const cal = CalendarApp.getCalendarById(CALENDAR_ID);
  if (!cal) return _json({ error: 'Calendar not found' }, 404);

  const event = cal.getEventById(data.eventId);
  if (!event) return _json({ error: 'Event not found: ' + data.eventId }, 404);

  if (data.title) event.setTitle(data.title);
  if (data.description !== undefined) event.setDescription(data.description);
  if (data.location !== undefined) event.setLocation(data.location);
  if (data.start && data.end) event.setTime(new Date(data.start), new Date(data.end));

  return _json({
    status: 'updated',
    eventId: data.eventId,
    title: event.getTitle()
  });
}

function _deleteEvent(data) {
  const cal = CalendarApp.getCalendarById(CALENDAR_ID);
  if (!cal) return _json({ error: 'Calendar not found' }, 404);

  const event = cal.getEventById(data.eventId);
  if (!event) return _json({ error: 'Event not found: ' + data.eventId }, 404);

  const title = event.getTitle();
  event.deleteEvent();

  return _json({
    status: 'deleted',
    eventId: data.eventId,
    title: title
  });
}

function _listEvents(data) {
  const cal = CalendarApp.getCalendarById(CALENDAR_ID);
  if (!cal) return _json({ error: 'Calendar not found' }, 404);

  const start = new Date(data.start || new Date().toISOString());
  const end = new Date(data.end || new Date(Date.now() + 365 * 86400000).toISOString());
  const events = cal.getEvents(start, end);

  const results = events.map(function(ev) {
    return {
      eventId: ev.getId(),
      title: ev.getTitle(),
      start: ev.getStartTime().toISOString(),
      end: ev.getEndTime().toISOString(),
      location: ev.getLocation(),
      description: ev.getDescription()
    };
  });

  return _json({ status: 'ok', count: results.length, events: results });
}

function _json(obj, code) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

// Test function — run this in the editor to verify calendar access
function testAccess() {
  const cal = CalendarApp.getCalendarById(CALENDAR_ID);
  if (cal) {
    Logger.log('SUCCESS — Calendar found: ' + cal.getName());
  } else {
    Logger.log('FAIL — Cannot access calendar: ' + CALENDAR_ID);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// DEPLOYMENT LOG
// ─────────────────────────────────────────────────────────────────────────────
// Append a line each time this master is published to script.google.com.
// Format: // Deployed: YYYY-MM-DD HH:MM Central — <description> — by <name>
// See docs/runbooks/publish-calendar-webhook.md

// Deployed: 2026-04-17 — initial master-copy commit (functionally identical to then-deployed version, passphrase redacted) — by Ray (captured by Jarvis)
