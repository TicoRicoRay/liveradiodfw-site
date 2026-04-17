# Live Radio DFW — Documentation

This is the `docs` branch of the liveradiodfw-site repo. It holds project docs, postmortems, runbooks, and architecture notes. It is **not** served on the live site — that's the `gh-pages` branch.

## Layout

```
docs/
├── project-plan.md          # Open items / roadmap
├── runbooks/                # How-to guides for common tasks
├── postmortems/             # What broke, why, and what we changed
└── architecture/            # How the system works
```

## Editing

Edit directly on github.com, or clone and push:

```bash
git clone -b docs git@github.com:TicoRicoRay/liveradiodfw-site.git liveradiodfw-docs
```

## What does NOT belong here (since this branch is public)

- Webhook URLs or passphrases
- Venue contact info / personal phone numbers
- Band finances (guarantees, splits, tax info)
- Signed contracts

If any of that becomes necessary, create a separate **private** `liveradiodfw-ops` repo.
