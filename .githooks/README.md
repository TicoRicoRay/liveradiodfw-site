# Git hooks for liveradiodfw-site

One-time install per clone:

    git config core.hooksPath .githooks

That's it. After this, the hooks in this directory run automatically.

## What's here

### `pre-commit`

Blocks commits that stage `shows.json` without also staging at least one
`shows/*.html` file. This catches the exact failure mode of commit
`5f768ed` (2026-04-23), where a hand-edit to `shows.json` was pushed
without running the builder chain and left the live 3 Nations Brewing
show page showing the placeholder. See [R27 on the roadmap](https://github.com/TicoRicoRay/liveradiodfw-site/blob/docs/docs/roadmap.md)
and [B33 in bugs.md](https://github.com/TicoRicoRay/liveradiodfw-site/blob/docs/docs/bugs.md) for context.

**To bypass for a legitimate schema-only edit:**

    SKIP_SHOWS_JSON_CHECK=1 git commit -m "..."

## Why `.githooks/` and not `.git/hooks/`

`.git/hooks/` is local to each clone and not version-controlled. Putting
hooks in a tracked directory and pointing git at it with
`core.hooksPath` means every clone gets the same hooks after the one-time
config, and changes to the hooks ship through normal PR / review.
