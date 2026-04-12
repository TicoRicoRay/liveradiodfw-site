/**
 * nav-loader.js — Global nav include for LiveRadioDFW
 * Fetches nav.html, injects it at the top of <body>,
 * and sets the .active class on the current page's nav link.
 *
 * Works on GitHub Pages (relative paths).
 * Hides body until nav is injected to prevent flash of unstyled content.
 */
(function () {
  // Determine the base path for nav.html (handles subdirectory deployments)
  var scripts = document.getElementsByTagName('script');
  var scriptSrc = '';
  for (var i = 0; i < scripts.length; i++) {
    if (scripts[i].src && scripts[i].src.indexOf('nav-loader.js') !== -1) {
      scriptSrc = scripts[i].src;
      break;
    }
  }
  // Base path is the directory containing js/nav-loader.js, i.e. one level up
  var basePath = scriptSrc ? scriptSrc.replace(/js\/nav-loader\.js.*$/, '') : '';
  var navUrl = basePath + 'nav.html';

  /**
   * Map pathname segments to nav link hrefs.
   * Pages not in this list (e.g. book.html, contact.html, press-kit.html,
   * corporate-events.html, private-parties.html) have no active nav link.
   */
  var pageMap = {
    'index.html':                          'index.html',
    '':                                    'index.html',   // root /
    'shows.html':                          'shows.html',
    'songs.html':                          'songs.html',
    'the-all-80s-hits-station.html':       'songs.html',
    'the-all-70s-no-disco-hits-station.html': 'songs.html',
    'the-classic-rock-station.html':       'songs.html',
    'the-all-oldies-hits-station.html':    'songs.html',
    'videos.html':                         'videos.html',
    'about.html':                          'about.html',
    'members.html':                        'members.html',
    'store.html':                          'store.html'
  };

  function getPageFilename() {
    var path = window.location.pathname;
    // Get last segment
    var parts = path.split('/');
    var filename = parts[parts.length - 1] || '';
    // Strip query string/hash just in case
    filename = filename.split('?')[0].split('#')[0];
    return filename;
  }

  function setActiveLink(navEl) {
    var filename = getPageFilename();
    var activeHref = pageMap[filename] || null;
    if (!activeHref) return;

    // Remove any existing active classes
    var links = navEl.querySelectorAll('a.active');
    for (var i = 0; i < links.length; i++) {
      links[i].classList.remove('active');
    }

    // Set active on matching nav-links <a>
    var navLinks = navEl.querySelectorAll('.nav-links a');
    for (var j = 0; j < navLinks.length; j++) {
      var href = navLinks[j].getAttribute('href');
      if (href === activeHref) {
        navLinks[j].classList.add('active');
      }
    }
  }

  function injectNav(html) {
    // Create a temporary container to parse the HTML
    var tmp = document.createElement('div');
    tmp.innerHTML = html;

    // Insert all children at the top of body
    var body = document.body;
    var ref = body.firstChild;
    while (tmp.firstChild) {
      body.insertBefore(tmp.firstChild, ref);
    }

    // Set active class
    setActiveLink(document.body);

    // Reveal body
    document.documentElement.style.visibility = '';
  }

  // Use XMLHttpRequest for broadest compatibility (no fetch polyfill needed)
  var xhr = new XMLHttpRequest();
  xhr.open('GET', navUrl, true);
  xhr.onreadystatechange = function () {
    if (xhr.readyState === 4) {
      if (xhr.status === 200 || xhr.status === 0) {
        injectNav(xhr.responseText);
      }
      // On failure, page is already visible — nothing to do
    }
  };
  xhr.onerror = function () {
    // Fetch failed silently — page renders without nav
  };
  xhr.send();
})();
