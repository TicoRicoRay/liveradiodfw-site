/* =============================================
   LIVE RADIO DFW — Main JavaScript
   ============================================= */

document.addEventListener('DOMContentLoaded', function () {

  // --- Dark Mode Toggle ---
  // Precedence on every page load: saved choice (localStorage) > OS preference > light.
  // The inline head script in every HTML file sets data-theme *before* paint using the
  // same precedence, so this block just reads what's already there and wires the toggle.
  // See B12: earlier behavior re-read OS preference on every page load, overriding the
  // user's last click as soon as they navigated. Fixed 2026-04-20 PM.
  const themeToggle = document.querySelector('[data-theme-toggle]');
  const root = document.documentElement;
  let currentTheme = root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  updateThemeIcon();

  document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', currentTheme);
      try { localStorage.setItem('theme', currentTheme); } catch (_) { /* private mode: choice is session-only */ }
      updateThemeIcon();
    });
  });

  function updateThemeIcon() {
    const toggles = document.querySelectorAll('[data-theme-toggle]');
    toggles.forEach(function (t) {
      t.setAttribute('aria-label', 'Switch to ' + (currentTheme === 'dark' ? 'light' : 'dark') + ' mode');
      if (currentTheme === 'dark') {
        t.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>';
      } else {
        t.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
      }
    });
  }

  // --- Mobile Menu ---
  const hamburger = document.querySelector('.hamburger');
  const mobileOverlay = document.querySelector('.mobile-overlay');

  if (hamburger && mobileOverlay) {
    hamburger.addEventListener('click', function () {
      hamburger.classList.toggle('active');
      mobileOverlay.classList.toggle('open');
      document.body.style.overflow = mobileOverlay.classList.contains('open') ? 'hidden' : '';
    });

    // Close on link click
    mobileOverlay.querySelectorAll('a:not(.mobile-dropdown-toggle)').forEach(function (link) {
      link.addEventListener('click', function () {
        hamburger.classList.remove('active');
        mobileOverlay.classList.remove('open');
        document.body.style.overflow = '';
      });
    });

    // Mobile dropdown
    mobileOverlay.querySelectorAll('.mobile-dropdown-toggle').forEach(function (toggle) {
      toggle.addEventListener('click', function (e) {
        e.preventDefault();
        var items = toggle.nextElementSibling;
        if (items) {
          items.classList.toggle('open');
        }
      });
    });
  }

  // --- Desktop Dropdown (click support for touch) ---
  // Songs dropdown
  document.querySelectorAll('.nav-dropdown').forEach(function (dropdown) {
    dropdown.addEventListener('click', function (e) {
      if (window.innerWidth <= 1100) return;
      dropdown.classList.toggle('open');
    });
  });

  // Book the Band CTA dropdown
  document.querySelectorAll('.nav-cta-dropdown').forEach(function (dropdown) {
    dropdown.addEventListener('click', function (e) {
      if (window.innerWidth <= 1100) return;
      // If clicking the link itself and menu is closed, toggle open
      // If clicking a menu item, let it navigate
      if (e.target.closest('.nav-cta-menu')) return;
      e.preventDefault();
      dropdown.classList.toggle('open');
    });
  });

  // Close all dropdowns when clicking outside
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.nav-dropdown') && !e.target.closest('.nav-cta-dropdown')) {
      document.querySelectorAll('.nav-dropdown.open, .nav-cta-dropdown.open').forEach(function (d) {
        d.classList.remove('open');
      });
    }
  });

  // --- Share Buttons ---
  // Handled by show-actions.js (enhanced share with dropdown + Add to Calendar)

  // --- Scroll animations ---
  // Immediately reveal any fade-in elements already in viewport on load
  function revealVisible() {
    document.querySelectorAll('.fade-in:not(.fade-in-visible)').forEach(function (el) {
      var rect = el.getBoundingClientRect();
      if (rect.top < window.innerHeight + 60) {
        el.classList.add('fade-in-visible');
      }
    });
  }
  revealVisible(); // run immediately
  setTimeout(revealVisible, 100); // run again after layout settles
  setTimeout(revealVisible, 400); // and once more for slow renders

  var observerOptions = { threshold: 0.05, rootMargin: '0px 0px 0px 0px' };
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('fade-in-visible');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.fade-in').forEach(function (el) {
    observer.observe(el);
  });

  // --- Active nav link ---
  var currentPage = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(function (link) {
    var href = link.getAttribute('href');
    if (href === currentPage || (currentPage === 'index.html' && href === 'index.html')) {
      link.classList.add('active');
    }
  });

});

// =============================================
// SHOWS: Auto-hide past shows, show "View Past Shows" toggle
// Each show card needs data-show-date="YYYY-MM-DD"
// =============================================
(function () {
  var list = document.querySelector('.shows-page-list');
  if (!list) return;

  // Skip on archive pages (past-shows.html) - every card is meant to show
  if (list.hasAttribute('data-past-only')) return;

  var today = new Date();
  today.setHours(0, 0, 0, 0); // compare date only, not time

  var cards = list.querySelectorAll('[data-show-date]');
  var pastCards = [];
  var upcomingCount = 0;

  cards.forEach(function (card) {
    var d = new Date(card.dataset.showDate + 'T00:00:00');
    if (d < today) {
      card.classList.add('show-past');
      pastCards.push(card);
    } else {
      upcomingCount++;
    }
  });

  // Hide past shows initially
  pastCards.forEach(function (card) {
    card.style.display = 'none';
  });

  // If no upcoming shows, display a message
  if (upcomingCount === 0 && cards.length > 0) {
    var noShows = document.createElement('p');
    noShows.className = 'no-shows-msg';
    noShows.textContent = 'No upcoming shows scheduled right now. Check back soon or sign up for text alerts below.';
    noShows.style.cssText = 'text-align:center;color:var(--text-secondary);padding:2rem 0;';
    list.insertBefore(noShows, list.firstChild);
  }

  // Add "View Past Shows" toggle if there are any past shows
  if (pastCards.length > 0) {
    var toggle = document.createElement('button');
    toggle.textContent = 'View Previous Shows (' + pastCards.length + ')';
    toggle.className = 'past-shows-toggle';
    toggle.setAttribute('aria-expanded', 'false');

    var expanded = false;
    toggle.addEventListener('click', function () {
      expanded = !expanded;
      pastCards.forEach(function (card) {
        card.style.display = expanded ? '' : 'none';
      });
      toggle.textContent = expanded
        ? 'Hide Previous Shows'
        : 'View Previous Shows (' + pastCards.length + ')';
      toggle.setAttribute('aria-expanded', String(expanded));
    });

    // Insert toggle after the shows list
    list.parentNode.insertBefore(toggle, list.nextSibling);
  }
})();

// Auto-update copyright year
(function() {
  var el = document.getElementById('copyright-year');
  if (el) el.textContent = '\u00A9 ' + new Date().getFullYear();
})();
