#!/usr/bin/env python3
"""
build_includes.py — LiveRadioDFW static include builder
========================================================
Single point of maintenance for nav, footer, canonical/og:url, and sitemap.

Source of truth:
    includes/nav.html       — site navigation + mobile overlay
    includes/footer.html    — site footer (contact, social, copyright)
    (this script)           — canonical + og:url URL derivation rule
                            — sitemap.xml page list

How it works:
    1. Reads the include templates from includes/
    2. Scans all .html files in the site root + subdirs (excludes includes/)
    3. Replaces content between markers with the current template:
         Nav:       <!-- BEGIN_NAV -->       ... <!-- END_NAV -->
         Footer:    <!-- BEGIN_FOOTER -->    ... <!-- END_FOOTER -->
         Canonical: <!-- BEGIN_CANONICAL --> ... <!-- END_CANONICAL -->
    4. For canonical: auto-inserts markers into <head> if missing.
       Derives extensionless URL from file path (index.html -> /, about.html -> /about,
       shows/foo-2025-01-01.html -> /shows/foo-2025-01-01). Writes both
       <link rel="canonical"> and <meta property="og:url">.
    5. Regenerates sitemap.xml from the same page list (excluding NOINDEX_PAGES),
       preserving existing <priority>/<changefreq> metadata per page.
    6. Reports what changed

Exclusions:
    NOINDEX_PAGES — skipped for canonical AND sitemap. Pages that shouldn't
    appear in search (thanks.html, orphaned legacy pages).

Usage:
    python build_includes.py          # update all pages + sitemap
    python build_includes.py -v       # verbose — show each file

Called automatically by sync_calendar.py after build_shows.py.
"""

import re
import sys
from pathlib import Path

BASE = Path(__file__).parent
INCLUDES = BASE / "includes"

# ── Canonical URL config ──────────────────────────────────────────────────────
SITE_ORIGIN = "https://liveradiodfw.com"  # no www, no trailing slash

# Pages that should NOT appear in search results — excluded from canonical
# stamping AND from sitemap. Paths are relative to repo root, forward slashes.
# Rule: anything Google could see as duplicate content needs to be fixed, not
# hidden. Only exclude files that are not real pages.
NOINDEX_PAGES = {
    "nav.html",      # legacy nav-template fragment in root (kept for build_nav.py);
                     # not a real page, no <head>, cannot be canonicalized.
                     # Dual-source cleanup with includes/nav.html is a separate bug.
}

# ── Load templates ────────────────────────────────────────────────────────────
nav_html = (INCLUDES / "nav.html").read_text()
footer_html = (INCLUDES / "footer.html").read_text()

# ── Regex patterns for replacement ────────────────────────────────────────────
NAV_PATTERN = re.compile(
    r"<!-- BEGIN_NAV -->.*?<!-- END_NAV -->",
    re.DOTALL
)
FOOTER_PATTERN = re.compile(
    r"<!-- BEGIN_FOOTER -->.*?<!-- END_FOOTER -->",
    re.DOTALL
)
CANONICAL_PATTERN = re.compile(
    r"<!-- BEGIN_CANONICAL -->.*?<!-- END_CANONICAL -->",
    re.DOTALL
)
# Match any existing stray canonical/og:url lines (outside markers) so we can
# clean them up on first run. Matches one full tag on its own line.
STRAY_CANONICAL_PATTERN = re.compile(
    r'^[ \t]*<link\s+rel="canonical"[^>]*>\s*\n',
    re.MULTILINE
)
STRAY_OGURL_PATTERN = re.compile(
    r'^[ \t]*<meta\s+property="og:url"[^>]*>\s*\n',
    re.MULTILINE
)

verbose = "-v" in sys.argv


def canonical_url_for(rel_path_str):
    """Derive the canonical (extensionless) URL for a page path.

    Examples:
        index.html                         -> https://liveradiodfw.com/
        about.html                         -> https://liveradiodfw.com/about
        shows/foo-2025-01-01.html          -> https://liveradiodfw.com/shows/foo-2025-01-01
    """
    p = rel_path_str.replace("\\", "/")  # windows safety
    if p == "index.html":
        return SITE_ORIGIN + "/"
    if p.endswith("/index.html"):
        return SITE_ORIGIN + "/" + p[:-len("index.html")]
    if p.endswith(".html"):
        p = p[:-len(".html")]
    return SITE_ORIGIN + "/" + p


def build_canonical_block(url, indent="  "):
    """Return the marker-wrapped canonical + og:url block."""
    return (
        f"{indent}<!-- BEGIN_CANONICAL -->\n"
        f'{indent}<link rel="canonical" href="{url}">\n'
        f'{indent}<meta property="og:url" content="{url}">\n'
        f"{indent}<!-- END_CANONICAL -->"
    )


def insert_canonical_markers(content, block):
    """Insert the canonical block into <head> if markers don't exist.

    Strategy: insert right before </head>. If an existing stray
    <link rel="canonical"> or <meta property="og:url"> is present, it is
    removed first so the marker block becomes the single source of truth.
    """
    if "<!-- BEGIN_CANONICAL -->" in content:
        return content
    # Remove any stray canonical/og:url lines that aren't in markers
    content = STRAY_CANONICAL_PATTERN.sub("", content)
    content = STRAY_OGURL_PATTERN.sub("", content)
    # Insert before </head>
    if "</head>" not in content:
        return content  # no <head> — skip silently
    return content.replace("</head>", block + "\n</head>", 1)


def rewrite_paths_for_subdir(html_text):
    """Rewrite root-relative paths to ../  for pages in subdirectories.

    Converts href="index.html" → href="../index.html"
    Converts src="img/logo.jpg" → src="../img/logo.jpg"
    Does NOT touch absolute URLs (http://, https://, //, #, mailto:, tel:).
    """
    def _fix(match):
        attr = match.group(1)   # href= or src=
        quote = match.group(2)  # " or '
        path = match.group(3)   # the path value
        # Skip absolute URLs, anchors, javascript:, mailto:, tel:
        if path.startswith(("http://", "https://", "//", "#", "mailto:", "tel:", "javascript:", "data:")):
            return match.group(0)
        # Skip already-relative paths (starts with ../)
        if path.startswith("../"):
            return match.group(0)
        return f'{attr}{quote}../{path}{quote}'

    return re.sub(r'((?:href|src|action)=)(["\'])([^"\']*)\2', _fix, html_text)


# ── Collect all HTML files (root + subdirectories) ────────────────────────────
html_files = sorted(BASE.glob("*.html"))
# Add subdirectory pages (shows/, etc.) but exclude includes/
for subdir in sorted(BASE.iterdir()):
    if subdir.is_dir() and subdir.name not in ("includes", "css", "js", "img", ".git", "node_modules", "cache", "files"):
        html_files.extend(sorted(subdir.glob("*.html")))

# ── Process all HTML files ────────────────────────────────────────────────────
updated = []
skipped = []

for html_file in html_files:
    original = html_file.read_text()
    content = original

    # Determine if file is in a subdirectory
    is_subdir = html_file.parent != BASE

    # Prepare include content (rewrite paths for subdirs)
    nav_content = rewrite_paths_for_subdir(nav_html.strip()) if is_subdir else nav_html.strip()
    footer_content = rewrite_paths_for_subdir(footer_html.strip()) if is_subdir else footer_html.strip()

    # Replace nav
    if "<!-- BEGIN_NAV -->" in content:
        content = NAV_PATTERN.sub(nav_content, content)

    # Replace footer
    if "<!-- BEGIN_FOOTER -->" in content:
        content = FOOTER_PATTERN.sub(footer_content, content)

    rel_path = html_file.relative_to(BASE)
    rel_str = str(rel_path).replace("\\", "/")

    # Canonical + og:url (skip noindex pages)
    if rel_str not in NOINDEX_PAGES:
        url = canonical_url_for(rel_str)
        block = build_canonical_block(url)
        # Insert markers if missing, then (re)stamp inside them
        content = insert_canonical_markers(content, block)
        if "<!-- BEGIN_CANONICAL -->" in content:
            content = CANONICAL_PATTERN.sub(
                block.lstrip(),  # pattern match starts at marker, no leading indent
                content,
            )

    if content != original:
        html_file.write_text(content)
        updated.append(str(rel_path))
        if verbose:
            print(f"  ✓ {rel_path}")
    else:
        skipped.append(str(rel_path))
        if verbose:
            print(f"  · {rel_path} (no change)")

print(f"build_includes: {len(updated)} updated, {len(skipped)} unchanged")
if updated:
    print(f"  Updated: {', '.join(updated)}")


# ── Sitemap regeneration ──────────────────────────────────────────────────────
def regenerate_sitemap(html_files):
    """Rewrite sitemap.xml from html_files, preserving per-URL priority/changefreq.

    - URLs are the extensionless canonical form.
    - NOINDEX_PAGES are excluded.
    - Existing <priority>/<changefreq> values are preserved by matching on the
      OLD sitemap URL (with .html) mapped to the new extensionless form.
    - New pages get sensible defaults based on path.
    """
    sitemap_path = BASE / "sitemap.xml"

    # Parse existing sitemap for per-URL metadata
    existing = {}  # canonical_url -> (priority, changefreq)
    if sitemap_path.exists():
        old = sitemap_path.read_text(encoding="utf-8")
        for m in re.finditer(
            r"<url>\s*<loc>([^<]+)</loc>"
            r"(?:\s*<priority>([^<]+)</priority>)?"
            r"(?:\s*<changefreq>([^<]+)</changefreq>)?",
            old,
        ):
            loc, pri, cf = m.group(1), m.group(2), m.group(3)
            # Normalize old .html URL to the canonical extensionless form
            # so we can match new pages to old metadata.
            norm = loc
            if norm.endswith("/index.html"):
                norm = norm[: -len("index.html")]
            elif norm.endswith(".html"):
                norm = norm[: -len(".html")]
            existing[norm] = (pri, cf)

    def default_meta(rel_str):
        """Fallback priority/changefreq for pages not in the old sitemap."""
        if rel_str == "index.html":
            return ("1.0", "weekly")
        if rel_str.startswith("shows/"):
            return ("0.5", "yearly")
        return ("0.6", "monthly")

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    count = 0
    for html_file in html_files:
        rel_str = str(html_file.relative_to(BASE)).replace("\\", "/")
        if rel_str in NOINDEX_PAGES:
            continue
        url = canonical_url_for(rel_str)
        pri, cf = existing.get(url, (None, None))
        if pri is None or cf is None:
            dpri, dcf = default_meta(rel_str)
            pri = pri or dpri
            cf = cf or dcf
        lines.append(
            f"  <url><loc>{url}</loc>"
            f"<priority>{pri}</priority>"
            f"<changefreq>{cf}</changefreq></url>"
        )
        count += 1
    lines.append("</urlset>")
    lines.append("")  # trailing newline

    new_sitemap = "\n".join(lines)
    old_sitemap = sitemap_path.read_text(encoding="utf-8") if sitemap_path.exists() else ""
    if new_sitemap != old_sitemap:
        sitemap_path.write_text(new_sitemap, encoding="utf-8")
        print(f"sitemap.xml: regenerated with {count} URLs")
    else:
        print(f"sitemap.xml: no change ({count} URLs)")


regenerate_sitemap(html_files)
