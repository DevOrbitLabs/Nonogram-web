# Nonogram: Cozy Picture Cross — website

The showcase site and the App-Store-required legal pages for **Nonogram: Cozy Picture Cross**
(iOS, App Store id `6795158972`).

Live: <https://nonogram.halimozturk.com> (family design v1; see `family.css` + `nonogram.css`). Deployed by CLI (`netlify deploy`), not git-linked.

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
  from an earlier app icon (a tree), its canopy `#52A153` and its trunk `#AA7A3E`. Those two still
  colour the hero puzzle below, which was never updated to the current icon — see the hero note.
- **Screenshots** in `assets/screens/` are RAW, unframed captures from the app's own
  `Docs/Screenshots/en-US/{iphone,ipad}/` (2026-10-03). The iPhone/iPad bezel is CSS. Every caption
  describes the exact screen it sits beside.
- **The hero puzzle is an earlier app icon, kept on purpose.** Its six-by-six solution and its real
  row and column clues are in `index.html`; solving it colours a tree in that earlier icon's two
  colours. The current app icon (a green clue-corner mark with a hot-air balloon) is used everywhere
  else on the site — the nav mark, the footer mark, `assets/icon-1024.png` and `assets/og-cover.png`
  — but the interactive hero puzzle itself was deliberately left unchanged; reworking a 36-cell
  solvable puzzle for the new icon is tracked separately, not done in this pass.
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
