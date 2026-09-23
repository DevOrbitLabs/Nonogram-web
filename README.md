# Nonogram: Cozy Picture Cross — website

The showcase site and the App-Store-required legal pages for **Nonogram: Cozy Picture Cross**
(iOS, App Store id `6795158972`).

Live: <https://nonogramcozy.netlify.app>

| Page | Path | Also served at |
|---|---|---|
| Home | `index.html` | `/` |
| Privacy Policy | `privacy.html` | `/privacy`, `/privacy-policy`, `/nonogram/privacy` |
| Terms of Use | `terms.html` | `/terms`, `/nonogram/terms` |

The `/nonogram/*` redirects exist because the app's Settings screen links there; they keep an
already-shipped build's legal links working whatever the canonical path becomes.

## Stack

Static HTML and one hand-written stylesheet. **No build step and no framework.** Deployed by
Netlify straight from `main`.

Fonts are Fredoka (display) and Nunito Sans (body), loaded from Google Fonts. Everything else is
local. **The page renders fully with JavaScript disabled** — the only script adds the interactive
hero puzzle and the footer year, and neither is needed to read the site.

## Where the content comes from

Nothing here was written from a template or from memory.

- **Palette** is the app's own asset catalog — `Surface #F7F6F3`, `LaunchBackground #F6F2E8`,
  `BoardBackground #D2CDC4`, `ClueText #292826`, `AccentColor #4D9850` — plus two colours sampled
  from the app icon, its canopy `#52A153` and its trunk `#AA7A3E`.
- **Screenshots** in `assets/screens/` are unframed captures from the app's own design-review pass
  (`Docs/DESIGN/finalpass/` in the app repo). The iPhone bezel is CSS. Every caption describes the
  exact screen it sits beside.
- **The hero puzzle is the app icon.** Its six-by-six solution and its real row and column clues are
  in `index.html`; solving it colours the tree in the icon's own two colours.
- **The legal pages are derived from `Docs/PRIVACY/DECLARATION.md`** in the app repo, which
  `Scripts/privacy_scan.py --scan` produces by measuring the binary — the SDKs it links, the hosts it
  contacts, the payloads it sends. They are not a template's optimistic defaults.

## Gates

Both must pass before anything is pushed or redeployed.

```bash
python3 claims_lint.py .                      # exit 0 — no unjustified claim on any surface
python3 ../Nonogram/Scripts/privacy_scan.py ../Nonogram --check   # exit 0 — the declaration is current
```

`claims_lint.py` scans the visible text **and** the JSON-LD of every page for six claim families:
price, discount, trial, tier, absolute privacy claims and security claims. Two privacy sentences are
justified in `claims-allowlist.json`, each with a `file:line` in the app repo; an entry with blank
evidence fails on purpose.

⛔ **Re-run both whenever the app changes.** `DECLARATION.md` carries a fingerprint over the app's
dependency manifests and analytics enums — an SDK added later reopens the question, and a sentence
on these pages can become false without anyone editing it.

## Rules this site is held to

- **No price, no discount percentage, no per-tier feature table, no trial language** — anywhere,
  including the JSON-LD. Pricing defers to the App Store.
- **Never "no ads" or "ad-free"** in any form. The game ships advertising and the site says so
  plainly, on the home page and in the Terms.
- **Never "no lives to buy"** (struck 2026-08-18) and never the trademarked genre names. The wedge
  the site may state is: no energy, no waiting, every puzzle open from the start, and a restart that
  is instant and free.
- Whatever one page asserts, all of them assert — the home page, both legal pages and the JSON-LD.

## Updating

Edit, re-run the two gates, re-render and look at the pages at 1440 and 390 wide, then push. Netlify
redeploys from `main` on its own.

© 2026 DevOrbit Labs.
