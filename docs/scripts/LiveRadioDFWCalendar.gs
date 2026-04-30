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

    const action = data.action; // "create", "update", "delete", "list", "availability"

    if (action === 'create') {
      return _createEvent(data);
    } else if (action === 'update') {
      return _updateEvent(data);
    } else if (action === 'delete') {
      return _deleteEvent(data);
    } else if (action === 'list') {
      return _listEvents(data);
    } else if (action === 'availability') {
      return _getAvailability(data);
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

  // Accept either `guests` (original field name) or `attendees` (what update uses).
  // Caller-friendly: one API surface, two synonymous keys.
  const guestList = (data.guests || data.attendees || []);

  const event = cal.createEvent(data.title, start, end, {
    description: data.description || '',
    location: data.location || '',
    guests: guestList.join(','),
    sendInvites: false
  });

  return _json({
    status: 'created',
    eventId: event.getId(),
    title: data.title,
    start: start.toISOString(),
    end: end.toISOString(),
    guests: event.getGuestList().map(function(g) { return g.getEmail(); })
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

  // Guests/attendees: iterate the array and add each as a guest. Fixes B2 / closes R10.
  // Accept either `attendees` (natural for update) or `guests` (matches create's field name).
  // Apps Script CalendarApp does not expose a "replace all guests" primitive; addGuest
  // is a no-op if the email is already on the event, so repeated calls are safe.
  const guestList = data.attendees || data.guests;
  if (guestList && Array.isArray(guestList)) {
    guestList.forEach(function(email) { event.addGuest(email); });
  }

  return _json({
    status: 'updated',
    eventId: data.eventId,
    title: event.getTitle(),
    guests: event.getGuestList().map(function(g) { return g.getEmail(); })
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

/**
 * _getAvailability — return open Friday/Saturday dates over a forward window.
 *
 * Mirrors the logic of liveradiodfw_availability.py on Dopamine, server-side
 * under the calendar owner's auth, so Jarvis can call this from any sandbox
 * without OAuth-desktop creds. Closes B41.
 *
 * Request shape:
 *   { passphrase, action: "availability",
 *     monthsAhead?: number,    // default 6, max 12
 *     daysAhead?: number,      // alternative to monthsAhead; takes precedence if set
 *     weekdays?: number[]      // 0=Sun..6=Sat. Default [5,6] (Fri, Sat).
 *                              //   NOTE: this is JS getDay(); Python's weekday() differs.
 *   }
 *
 * Response shape:
 *   { status: "ok",
 *     generatedAt: ISO string,
 *     window: { start: "YYYY-MM-DD", end: "YYYY-MM-DD", days: number },
 *     openDates: ["YYYY-MM-DD", ...],
 *     blocked: [ { date: "YYYY-MM-DD", reasons: [titles...] } ]
 *   }
 *
 * Rules (kept identical to liveradiodfw_availability.py):
 *   - Any timed event on a date blocks that date.
 *   - Any all-day event blocks every date in its inclusive range.
 *   - Event titles containing "rehearsal" (case-insensitive) are ignored.
 *
 * Time zone:
 *   The script runs under the project's configured time zone (set in
 *   Apps Script project settings to America/Chicago when the project was
 *   created). Date keys in the response are Central-local YYYY-MM-DD.
 */
function _getAvailability(data) {
  const cal = CalendarApp.getCalendarById(CALENDAR_ID);
  if (!cal) return _json({ error: 'Calendar not found' }, 404);

  const tz = Session.getScriptTimeZone(); // expected: America/Chicago
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  let days;
  if (typeof data.daysAhead === 'number' && data.daysAhead > 0) {
    days = Math.min(data.daysAhead, 400);
  } else {
    const months = Math.min(Math.max(data.monthsAhead || 6, 1), 12);
    // Approximate months as 31-day blocks for window-end safety; events outside
    // the calendar month boundary are still captured because we walk per-day.
    days = months * 31;
  }
  const end = new Date(today.getTime() + days * 86400000);

  const weekdays = (Array.isArray(data.weekdays) && data.weekdays.length)
    ? data.weekdays
    : [5, 6]; // Fri, Sat in JS getDay() (0=Sun..6=Sat)

  // Pull all events in the window once. CalendarApp.getEvents expands recurrences
  // into instances, matching Python's singleEvents=True.
  const events = cal.getEvents(today, end);

  // Build blocked-date map. Key: YYYY-MM-DD in Central. Value: array of titles.
  const blockedMap = {};
  function addBlock(dateStr, reason) {
    if (!blockedMap[dateStr]) blockedMap[dateStr] = [];
    blockedMap[dateStr].push(reason);
  }

  events.forEach(function(ev) {
    const title = ev.getTitle() || '';
    if (/rehearsal/i.test(title)) return;

    if (ev.isAllDayEvent()) {
      // All-day: block every date from start (inclusive) to end (exclusive).
      // CalendarApp returns end as exclusive midnight; iterate up to but not including.
      let d = new Date(ev.getAllDayStartDate());
      const allDayEnd = new Date(ev.getAllDayEndDate());
      while (d < allDayEnd) {
        addBlock(Utilities.formatDate(d, tz, 'yyyy-MM-dd'), title);
        d = new Date(d.getTime() + 86400000);
      }
    } else {
      // Timed event: blocks the Central-local calendar date of its start.
      addBlock(Utilities.formatDate(ev.getStartTime(), tz, 'yyyy-MM-dd'), title);
    }
  });

  // Walk weekdays in window, separate into open vs blocked.
  const openDates = [];
  const blocked = [];
  let cursor = new Date(today);
  while (cursor < end) {
    if (weekdays.indexOf(cursor.getDay()) !== -1) {
      const key = Utilities.formatDate(cursor, tz, 'yyyy-MM-dd');
      if (blockedMap[key]) {
        blocked.push({ date: key, reasons: blockedMap[key] });
      } else {
        openDates.push(key);
      }
    }
    cursor = new Date(cursor.getTime() + 86400000);
  }

  return _json({
    status: 'ok',
    generatedAt: new Date().toISOString(),
    timezone: tz,
    window: {
      start: Utilities.formatDate(today, tz, 'yyyy-MM-dd'),
      end: Utilities.formatDate(end, tz, 'yyyy-MM-dd'),
      days: days
    },
    weekdays: weekdays,
    openDates: openDates,
    blocked: blocked
  });
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
// Deployed: 2026-04-17 ~20:52 Central — Version 2 — rotated passphrase (B7 Part 1) + extended _updateEvent and _createEvent to honor attendees/guests and return guests[] (R10, fixes B2) — by Ray, code authored by Jarvis. Smoke test passed via requests.post: list OK (98 events), old passphrase rejected 401, create+update with attendees returned guests[] correctly, delete OK.
// Deployed: PENDING — Version 3 — added _getAvailability action (B41) so Jarvis can read open Fri/Sat dates from any sandbox via the existing webhook + passphrase. No new scopes; CalendarApp grants read access already used by _listEvents. — code authored by Jarvis, deploy by Ray per docs/runbooks/publish-calendar-webhook.md.
