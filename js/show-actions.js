/* =============================================
   LIVE RADIO DFW - Show Actions (Add to Calendar + Share)
   ============================================= */

(function () {
  'use strict';

  // --- Add to Calendar ---
  // Generates .ics file content and triggers download
  // Data attributes: data-cal-title, data-cal-date, data-cal-time, data-cal-venue, data-cal-address, data-cal-url
  function parseShowTime(dateStr, timeStr) {
    // Parse "7:15 PM" style time with a YYYY-MM-DD date
    var upper = timeStr.toUpperCase().trim();
    var isPM = upper.indexOf('PM') !== -1;
    var isAM = upper.indexOf('AM') !== -1;
    var clean = upper.replace('PM', '').replace('AM', '').trim();
    var parts = clean.split(':');
    var hour = parseInt(parts[0], 10);
    var minute = parts.length > 1 ? parseInt(parts[1], 10) : 0;
    if (isPM && hour !== 12) hour += 12;
    if (isAM && hour === 12) hour = 0;

    // Build Date object (local time - Central)
    var dp = dateStr.split('-');
    return new Date(parseInt(dp[0]), parseInt(dp[1]) - 1, parseInt(dp[2]), hour, minute, 0);
  }

  function formatICSDate(d) {
    // Format as YYYYMMDDTHHMMSS (local time, no Z - we'll use TZID)
    var pad = function (n) { return n < 10 ? '0' + n : '' + n; };
    return d.getFullYear() +
      pad(d.getMonth() + 1) +
      pad(d.getDate()) + 'T' +
      pad(d.getHours()) +
      pad(d.getMinutes()) +
      pad(d.getSeconds());
  }

  function generateICS(title, start, durationHours, location, address, url) {
    var end = new Date(start.getTime() + durationHours * 60 * 60 * 1000);
    var now = new Date();
    var uid = 'lrdfw-' + formatICSDate(start) + '@liveradiodfw.com';

    var lines = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//LiveRadioDFW//Shows//EN',
      'CALSCALE:GREGORIAN',
      'METHOD:PUBLISH',
      'BEGIN:VEVENT',
      'DTSTART;TZID=America/Chicago:' + formatICSDate(start),
      'DTEND;TZID=America/Chicago:' + formatICSDate(end),
      'DTSTAMP:' + formatICSDate(now) + 'Z',
      'UID:' + uid,
      'SUMMARY:' + title,
      'LOCATION:' + (location + (address ? ', ' + address : '')).replace(/,/g, '\\,'),
      'URL:' + url,
      'STATUS:CONFIRMED',
      'END:VEVENT',
      'END:VCALENDAR'
    ];

    return lines.join('\r\n');
  }

  function downloadICS(filename, content) {
    var blob = new Blob([content], { type: 'text/calendar;charset=utf-8' });
    var link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  }

  document.querySelectorAll('[data-cal-title]').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var title = btn.getAttribute('data-cal-title');
      var dateStr = btn.getAttribute('data-cal-date');
      var timeStr = btn.getAttribute('data-cal-time');
      var venue = btn.getAttribute('data-cal-venue') || '';
      var address = btn.getAttribute('data-cal-address') || '';
      var url = btn.getAttribute('data-cal-url') || window.location.href;

      var start = parseShowTime(dateStr, timeStr);
      var ics = generateICS(title, start, 3, venue, address, url);
      var filename = 'liveradiodfw-' + dateStr + '.ics';
      downloadICS(filename, ics);
    });
  });

  // --- Enhanced Share ---
  // Uses Web Share API on mobile, shows dropdown on desktop
  document.querySelectorAll('[data-share]').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();

      var text = btn.getAttribute('data-share');
      var shareUrl = btn.getAttribute('data-share-url') || window.location.href;

      // If on individual show page, use canonical URL
      var canonical = document.querySelector('link[rel="canonical"]');
      if (canonical && !btn.getAttribute('data-share-url')) {
        shareUrl = canonical.getAttribute('href');
      }

      // Mobile: use native share
      if (navigator.share) {
        navigator.share({ title: text, text: text, url: shareUrl }).catch(function () {});
        return;
      }

      // Desktop: show dropdown
      var existing = document.querySelector('.share-dropdown');
      if (existing) {
        existing.remove();
        return;
      }

      var dropdown = document.createElement('div');
      dropdown.className = 'share-dropdown';

      var encodedUrl = encodeURIComponent(shareUrl);
      var encodedText = encodeURIComponent(text);

      var options = [
        { label: 'Copy Link', icon: 'link', action: 'copy' },
        { label: 'Facebook', icon: 'fb', url: 'https://www.facebook.com/sharer/sharer.php?u=' + encodedUrl },
        { label: 'Text/SMS', icon: 'sms', url: 'sms:?body=' + encodedText + '%20' + encodedUrl }
      ];

      options.forEach(function (opt) {
        var item = document.createElement('button');
        item.className = 'share-dropdown-item';
        item.textContent = opt.label;

        if (opt.action === 'copy') {
          item.addEventListener('click', function () {
            navigator.clipboard.writeText(shareUrl).then(function () {
              item.textContent = 'Copied!';
              setTimeout(function () { dropdown.remove(); }, 1200);
            });
          });
        } else {
          item.addEventListener('click', function () {
            window.open(opt.url, '_blank', 'width=600,height=400');
            dropdown.remove();
          });
        }

        dropdown.appendChild(item);
      });

      // Position dropdown near the button
      btn.style.position = 'relative';
      btn.appendChild(dropdown);

      // Close on outside click
      setTimeout(function () {
        document.addEventListener('click', function closeDropdown(ev) {
          if (!dropdown.contains(ev.target) && ev.target !== btn) {
            dropdown.remove();
            document.removeEventListener('click', closeDropdown);
          }
        });
      }, 10);
    });
  });

})();
