#!/usr/bin/env python3
"""
claims_lint.py — published-surface claim scanner (§3.2(f) account-safety gate).

WHAT IT IS FOR
--------------
Apple's own "flagged for termination" checklist names seven behaviours. Two of them are claims a
developer writes down and then fails to keep true:

    1. inaccurate metadata describing your app or service
    6. engaging in misleading purchasing or bait and switch schemes

This tool scans every PUBLISHED surface for the claim families that went wrong in the 2026-08-04
portfolio audit, and fails unless each hit is explicitly justified in an allow-list that names its
evidence. It does NOT try to decide truth by itself — it makes an unjustified absolute claim
impossible to ship silently.

WHY AN ALLOW-LIST INSTEAD OF AUTO-VERIFICATION
----------------------------------------------
The defect was never "nobody could check". It was that nobody was ASKED to check. Every false line
in the audit was written by someone confident it was true: "local-first, so no backend"; "3-day
trial, weekly" straight out of the local .storekit. Inverting the burden — every absolute claim must
carry a pointer to the code or the live-ASC read that proves it — is the part that generalises.

WHAT IT SCANS
-------------
* visible HTML text (tags stripped)
* <script type="application/ld+json"> STRUCTURED DATA — string values are scanned too. Debt
  Snowball's false FAQ answer ("we cannot see your debts") existed twice; the machine-readable copy
  is the one Google surfaces, and a visible-text-only scanner would have cleared the page.
* .md / .txt (Terms, DPA, store-metadata drafts) when pointed at them

Usage:
    claims_lint.py <path> [<path> ...] [--allow claims-allowlist.json] [--category price,privacy]
    claims_lint.py <dir> --init          # scaffold an allow-list from current hits (REVIEW IT)

Exit 0 = clean, 1 = unjustified claims found, 2 = usage/IO error.
"""
import sys, os, re, json, html, argparse

# --------------------------------------------------------------------------- claim families
# Each: (category, compiled regex, why it is dangerous)
# Keep patterns narrow enough to be actionable. A gate that cries wolf gets ignored, which is worse
# than no gate — but note the asymmetry: a MISSED false claim can cost the account, so when in
# doubt these lean toward flagging and let the allow-list carry the justification.
FAMILIES = [
    # ---- misleading purchasing (Apple checklist item 6) -----------------------------------
    ("price", r"(?<![\w])(?:[$£€]\s?\d+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?\s?(?:USD|EUR|GBP|TRY))"
              r"(?:\s?/\s?(?:wk|week|mo|month|yr|year))?",
     "A concrete price rots: regional tiers differ, Apple moves currency bands, and the page is "
     "false the moment StoreKit drifts. Standing rule (2026-08-04): defer to the App Store."),

    ("discount", r"(?i)\b(?:save|discount(?:ed)?(?:\s+by)?|up\s+to)\s*\d{1,3}\s?%|\b\d{1,3}\s?%\s*(?:off|discount|savings)",
     "A discount percentage is arithmetic over two prices; it is false whenever either moves, and "
     "'Save 28%' was live on a page whose two prices were themselves wrong."),

    ("trial", r"(?i)\b(?:\d+|one|two|three|five|seven|fourteen|thirty)[\s-]*(?:day|week|month)s?"
              r"[\s-]*(?:free[\s-]*)?trial\b|\bfree\s+for\s+\d+\s+(?:day|week|month)s?\b"
              r"|\btrial\s+ends?\s+in\b|\bstart\s+(?:your\s+)?free\s+trial\b",
     "A trial duration, and WHICH PLAN carries it, must be read from live ASC "
     "(GET /v1/subscriptions/{id}/introductoryOffers) — never from the local .storekit or AppConfig. "
     "BondAlchemy's local config said '3-day, weekly'; ASC said 7-day, monthly, in 175 territories, "
     "and every published surface was written from the wrong one."),

    ("tier", r"(?i)\b(?:most\s+popular|best\s+value|compare\s+plans|per[\s-]plan|"
             r"(?:monthly|yearly|annual)\s+(?:also\s+)?(?:adds|includes|unlocks)\b)",
     "A per-plan feature list is false by construction when the app has ONE entitlement. Derive the "
     "tier map from the entitlement check, not from marketing: one entitlements[...] lookup => one "
     "tier => any 'Plan B also gets X' copy is fiction."),

    # ---- inaccurate metadata / misleading content (items 1 & 2) ---------------------------
    ("privacy_absolute",
     r"(?i)\b(?:no\s+data\s+(?:collection|is\s+collected)|we\s+(?:do\s+not|don't|never)\s+"
     r"(?:collect|access|store|see|share|track)|never\s+(?:leaves?|leave)\s+your\s+device|"
     r"stays?\s+(?:private\s+)?on\s+your\s+device|we\s+(?:cannot|can't|have\s+no)\s+(?:access|see)|"
     r"100%\s+private|fully\s+private|no\s+tracking|zero\s+data|we\s+run\s+no\s+server|"
     r"anonymi[sz]ed(?:\s+\w+){0,2}\s*\(?no\s+pii)",
     "An absolute privacy claim must match the App Privacy declaration AND the code. This is the "
     "single check that would have caught the highest-severity finding of the whole audit. Watch for "
     "the two shapes that fooled everyone: a Cloud Function IS a first-party backend, and a "
     "self-hosted AI proxy makes the developer able to see the payload by construction."),

    ("security_claim",
     r"(?i)\b(?:certificate\s+pinning|end[\s-]to[\s-]end\s+encrypt|military[\s-]grade|"
     r"bank[\s-]level\s+security|regular\s+security\s+audits?|penetration\s+test|SOC\s?2|"
     r"ISO\s?27001|HIPAA[\s-]compliant)",
     "A security assertion needs a code fingerprint exactly like a data-collection claim. "
     "'Certificate pinning' and 'regular security audits' were both published with no implementation "
     "behind either."),
]

TEXT_EXT = {".html", ".htm", ".md", ".txt", ".json"}

# Repo-meta files are not PUBLISHED surfaces — a "MOST POPULAR" line in the site repo's own
# CLAUDE.md is a note to the agent, not a claim to a customer. Scanning them produces noise that
# trains the operator to ignore the gate.
SKIP_BASENAMES = {"claude.md", "readme.md", "agents.md", "contributing.md", "changelog.md",
                  "claims-allowlist.json", "package.json", "package-lock.json"}

# A claim that is explicitly DENIED is not a claim. Phase 2 rewrote BondAlchemy's DPA to say
# "the app does not implement certificate pinning … earlier versions of this page stated otherwise,
# and that was incorrect" — the honest correction itself must not trip the gate that asked for it.
NEGATION = re.compile(
    r"(?i)\b(?:no|not|never|without|nor|makes?\s+no\s+claim|do(?:es)?n['’]?t|"
    r"lacks?|absent|disabled?)\b")


def _negated(line, start):
    """True if a negation sits within the ~70 chars before the match (same sentence)."""
    window = line[max(0, start - 70):start]
    window = re.split(r"[.;!?]\s", window)[-1]
    return bool(NEGATION.search(window))


def strip_html(raw):
    """Return (visible_text, [jsonld_strings]) with original line numbers preserved."""
    # Pull JSON-LD blocks out first so we can scan their string VALUES, not their syntax.
    jsonld = []
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                         raw, re.S | re.I):
        line0 = raw[:m.start()].count("\n") + 1
        try:
            data = json.loads(m.group(1))
        except Exception:
            jsonld.append((line0, m.group(1)))
            continue

        def walk(node):
            if isinstance(node, dict):
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
            elif isinstance(node, str):
                jsonld.append((line0, node))
        walk(data)

    # Blank out script/style bodies but KEEP their newlines so line numbers stay honest.
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    txt = re.sub(r"<script\b.*?</script>", blank, raw, flags=re.S | re.I)
    txt = re.sub(r"<style\b.*?</style>", blank, txt, flags=re.S | re.I)
    txt = re.sub(r"<[^>]+>", lambda m: " " * len(m.group(0)), txt)
    return html.unescape(txt), jsonld


def scan_file(path, categories):
    hits = []
    try:
        raw = open(path, encoding="utf-8", errors="replace").read()
    except OSError as e:
        print(f"!! cannot read {path}: {e}", file=sys.stderr)
        return hits

    if path.lower().endswith((".html", ".htm")):
        text, jsonld = strip_html(raw)
    else:
        text, jsonld = raw, []

    lines = text.split("\n")
    for cat, pat, why in FAMILIES:
        if categories and cat not in categories:
            continue
        rx = re.compile(pat)
        # `security_claim` and `tier` are assertions that a preceding negation genuinely cancels
        # ("does not implement certificate pinning"). The privacy/price families are NOT
        # negation-exempt: "we do not collect" IS the dangerous claim, and negating it is the whole
        # point of the pattern.
        honour_negation = cat in ("security_claim", "tier")
        for i, line in enumerate(lines, 1):
            for m in rx.finditer(line):
                if honour_negation and _negated(line, m.start()):
                    continue
                hits.append({"file": path, "line": i, "category": cat,
                             "match": " ".join(m.group(0).split()), "where": "text", "why": why})
        for line0, s in jsonld:
            for m in rx.finditer(s):
                if honour_negation and _negated(s, m.start()):
                    continue
                hits.append({"file": path, "line": line0, "category": cat,
                             "match": " ".join(m.group(0).split()), "where": "json-ld", "why": why})

    # Collapse duplicates that differ only by whitespace inside the match.
    seen, uniq = set(), []
    for h in hits:
        k = (h["file"], h["line"], h["category"], h["match"].lower(), h["where"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(h)
    return uniq


def collect(paths):
    out = []
    for p in paths:
        if os.path.isfile(p):
            out.append(p)
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in
                           {".git", "node_modules", "assets", "DerivedData", ".netlify"}]
                for f in sorted(files):
                    if (os.path.splitext(f)[1].lower() in TEXT_EXT
                            and f.lower() not in SKIP_BASENAMES):
                        out.append(os.path.join(root, f))
        else:
            print(f"!! not found: {p}", file=sys.stderr)
    return out


def key_of(h):
    return f"{os.path.basename(h['file'])}::{h['category']}::{h['match'].lower()}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--allow", default=None,
                    help="allow-list JSON (default: <first path>/claims-allowlist.json)")
    ap.add_argument("--category", default=None, help="comma list to restrict families")
    ap.add_argument("--init", action="store_true",
                    help="write an allow-list skeleton from current hits — REVIEW EVERY ENTRY")
    a = ap.parse_args()

    cats = set(a.category.split(",")) if a.category else None
    files = collect(a.paths)
    if not files:
        print("[claims-lint] no scannable files found", file=sys.stderr)
        return 2

    hits = []
    for f in files:
        hits.extend(scan_file(f, cats))

    allow_path = a.allow or os.path.join(
        a.paths[0] if os.path.isdir(a.paths[0]) else os.path.dirname(a.paths[0]) or ".",
        "claims-allowlist.json")

    if a.init:
        skel = {"_README": "Every entry must carry `evidence`: a file:line in the app repo, or the "
                           "live-ASC endpoint that proves the claim. An entry with an empty evidence "
                           "string FAILS the gate — that is deliberate.",
                "allow": {key_of(h): {"evidence": "", "note": h["match"]} for h in hits}}
        with open(allow_path, "w", encoding="utf-8") as fh:
            json.dump(skel, fh, indent=2, ensure_ascii=False)
        print(f"[claims-lint] wrote {allow_path} with {len(skel['allow'])} entries — fill in every "
              f"`evidence` field; blank ones fail.")
        return 0

    allow = {}
    if os.path.exists(allow_path):
        try:
            allow = json.load(open(allow_path, encoding="utf-8")).get("allow", {})
        except Exception as e:
            print(f"!! bad allow-list {allow_path}: {e}", file=sys.stderr)
            return 2

    unjustified, justified = [], 0
    for h in hits:
        entry = allow.get(key_of(h))
        if entry and str(entry.get("evidence", "")).strip():
            justified += 1
        else:
            h["_reason"] = ("allow-list entry has an EMPTY evidence field"
                            if entry else "no allow-list entry")
            unjustified.append(h)

    if not unjustified:
        print(f"[claims-lint] OK — {len(files)} file(s) scanned, {justified} claim(s) justified, "
              f"0 unjustified.")
        return 0

    by_cat = {}
    for h in unjustified:
        by_cat.setdefault(h["category"], []).append(h)

    print(f"[claims-lint] FAILED — {len(unjustified)} unjustified claim(s) across "
          f"{len({h['file'] for h in unjustified})} file(s).\n", file=sys.stderr)
    for cat, group in by_cat.items():
        why = next(w for c, _, w in FAMILIES if c == cat)
        print(f"── {cat} ─────────────────────────────────────────", file=sys.stderr)
        print(f"   {why}\n", file=sys.stderr)
        for h in group[:12]:
            tag = " [JSON-LD]" if h["where"] == "json-ld" else ""
            print(f"   {h['file']}:{h['line']}{tag}  →  {h['match']!r}   ({h['_reason']})",
                  file=sys.stderr)
        if len(group) > 12:
            print(f"   … and {len(group) - 12} more", file=sys.stderr)
        print(file=sys.stderr)
    print("Fix the page, or justify the claim in claims-allowlist.json with real evidence "
          "(file:line, or the live-ASC endpoint read). `--init` scaffolds it.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
