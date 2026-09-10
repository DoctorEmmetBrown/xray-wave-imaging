#!/usr/bin/env python3
"""
Regenerate data/publications.yaml from the ORCID records of the whole group.

    python3 tools/orcid_to_yaml.py                    # every ORCID in data/people.yaml
    python3 tools/orcid_to_yaml.py 0000-0002-... ...  # only the ids given
    python3 tools/orcid_to_yaml.py --show-dropped     # list what a filter removed
    python3 tools/orcid_to_yaml.py --no-authors       # skip the Crossref author lookup

Where the ids come from
-----------------------
Every entry in `data/people.yaml` that has a non-empty `orcid`. Either form
works — the bare 0000-0002-1234-5678 or the full https://orcid.org/… URL. Put a member's
ORCID there and their publications appear on the site — including papers no one
else in the group co-authored. Remove it (or add `pubs: false` next to it) and
they drop out again. The id in hugo.toml is always included, as the group's
default record.

What it protects
----------------
`takeaway`, `featured`, `axes`, `hidden`, `code` and `data` are written by hand
and are the whole point of the publications page. They are matched to the
incoming records by DOI, falling back to a normalised title, and carried over.
Nothing you wrote is lost.

Entries that exist locally but in nobody's ORCID — a paper submitted but not yet
deposited, say — are kept and marked `orcid: false`.

Each record also carries `sources`: the members whose ORCID it came from. That
is what tells you why a paper is on the list.
"""

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Needs PyYAML:  pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "publications.yaml"
PEOPLE = ROOT / "data" / "people.yaml"
API = "https://pub.orcid.org/v3.0"
KEEP = ("takeaway", "code", "data", "axes", "featured", "hidden", "image", "authors")
CROSSREF = "https://api.crossref.org/works/"
ORCID_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
ORCID_URL = re.compile(r"^https?://(?:www\.)?orcid\.org/", re.I)

# ---------------------------------------------------------------------------
# Per-person publication filters, chosen with `pubs:` in data/people.yaml.
#
#   pubs: true    (or absent)  every work in that ORCID record
#   pubs: false                none — keeps the ORCID link, drops the papers
#   pubs: xray                 only works whose title or journal shows that an
#                              X-ray image was involved
#
# A keyword filter cannot read a paper. Some genuinely X-ray work has a title
# that never says so — list those DOIs under `pubs_also:` and they are kept
# regardless of the filter.
#
# Useful for a member whose bibliography is mostly outside the group's subject:
# their X-ray work belongs on the page, the rest does not. Edit the vocabulary
# below if it lets something through or holds something back.
# ---------------------------------------------------------------------------
PUBS_FILTERS = {
    "xray": re.compile(
        r"x[-\s]?ray|xray|radiograph|tomograph|tomosynth"
        r"|micro[-\s]?ct|µct|\bct\b|\bdect\b|\bhrct\b|\bcbct\b|dual[-\s]?energy"
        r"|\bkes\b|k[-\s]?edge"
        r"|synchrotron|phase[-\s]?contrast|dark[-\s]?field|speckle"
        r"|angiograph|fluoroscop|densitometr|\bsaxs\b|ptychograph",
        re.I,
    ),
}


def clean_orcid(value):
    """Accept 0000-0002-… or https://orcid.org/0000-0002-… ; return the bare id."""
    return ORCID_URL.sub("", (value or "").strip()).strip("/")


def orcid_sources():
    """[(orcid, display name)] — the site owner first, then data/people.yaml."""
    found, seen = [], set()

    text = (ROOT / "hugo.toml").read_text(encoding="utf-8")
    m = re.search(r"orcid\s*=\s*['\"]([^'\"]+)['\"]", text)
    if m:
        oid = clean_orcid(m.group(1))
        if oid:
            found.append((oid, "site owner", True, [])); seen.add(oid)

    if PEOPLE.exists():
        for p in yaml.safe_load(PEOPLE.read_text(encoding="utf-8")) or []:
            oid = clean_orcid(p.get("orcid"))
            if not oid or oid in seen or p.get("pubs") is False:
                continue
            if not ORCID_RE.match(oid):
                print(f"  ! skipping malformed ORCID for {p.get('name')}: {p.get('orcid')!r}")
                continue
            pubs = p.get("pubs", True)
            if isinstance(pubs, str) and pubs not in PUBS_FILTERS:
                print(f"  ! unknown pubs filter {pubs!r} for {p.get('name')} — using all works")
                pubs = True
            found.append((oid, p.get("name") or oid, pubs, p.get("pubs_also") or []))
            seen.add(oid)
    return found


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def norm(title):
    return re.sub(r"[^a-z0-9]+", "", (title or "").lower())


def norm_doi(value):
    """A DOI, however it was deposited, reduced to a comparable key.

    Different members deposit through different tools, so the same paper turns
    up as 10.1038/x, https://doi.org/10.1038/X, doi:10.1038/x, or with trailing
    punctuation. Comparing the raw strings would leave duplicates on the page.
    """
    d = (value or "").strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:\s*", "", d)
    return d.strip().rstrip(".,;")


def extract(summary):
    title = (summary.get("title") or {}).get("title", {}).get("value", "").strip()
    venue = (summary.get("journal-title") or {}).get("value", "") or ""
    year = ((summary.get("publication-date") or {}).get("year") or {}).get("value")
    doi = ""
    for eid in ((summary.get("external-ids") or {}).get("external-id") or []):
        if eid.get("external-id-type") == "doi":
            doi = norm_doi(eid.get("external-id-value"))
            break
    return {
        "title": title,
        "venue": venue,
        "year": int(year) if year and str(year).isdigit() else 0,
        "type": (summary.get("type") or "article").lower().replace("journal-article", "article"),
        "doi": doi,
        "authors": "",
    }


def fetch_authors(doi, mailto=""):
    """First author + 'et al.' from Crossref. ORCID's works endpoint has no
    author list, so the names have to come from somewhere else."""
    url = CROSSREF + urllib.parse.quote(doi, safe="")
    ua = f"xray-wave-imaging-site/1.0 (mailto:{mailto})" if mailto else "xray-wave-imaging-site/1.0"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": ua})
    with urllib.request.urlopen(req, timeout=20) as r:
        msg = json.load(r).get("message", {})
    authors = msg.get("author") or []
    if not authors:
        return ""
    first = authors[0]
    name = (first.get("family") or first.get("name") or "").strip()
    if not name:
        return ""
    return f"{name} et al." if len(authors) > 1 else name


def enrich_authors(records, mailto=""):
    """Fill in `authors` wherever it is missing. Cached by being preserved
    across runs, so this only costs a request the first time a paper appears."""
    todo = [r for r in records if r.get("doi") and not r.get("authors")]
    if not todo:
        return
    print(f"\nLooking up first authors for {len(todo)} paper(s) on Crossref …")
    ok = failed = 0
    for i, rec in enumerate(todo, 1):
        try:
            name = fetch_authors(rec["doi"], mailto)
            if name:
                rec["authors"] = name
                ok += 1
        except Exception:
            failed += 1
        if i % 25 == 0 or i == len(todo):
            print(f"  {i}/{len(todo)} …")
        time.sleep(0.12)                 # stay inside Crossref's polite rate
    print(f"  {ok} found, {failed} not available")


def richness(rec):
    """Which of two records for the same paper to keep."""
    return (bool(rec.get("venue")), bool(rec.get("doi")), rec.get("type") == "article")


def fetch_records(orcid, who, pubs=True, always=()):
    """Every usable work in one ORCID record, already de-duplicated internally."""
    keep_re = PUBS_FILTERS.get(pubs) if isinstance(pubs, str) else None
    always = {norm_doi(d) for d in (always or ())}
    works = get(f"{API}/{orcid}/works")
    groups = works.get("group", [])
    out, by_key, dropped = [], {}, []
    for g in groups:
        summaries = g.get("work-summary") or []
        if not summaries:
            continue
        rec = extract(summaries[0])
        if not rec["title"]:
            continue
        # OpenAlex mirrors every paper a second time with a junk DOI; skip those.
        if rec["venue"].strip().lower() == "openalex":
            continue
        if (keep_re and norm_doi(rec["doi"]) not in always
                and not keep_re.search(f"{rec['title']} {rec['venue']}")):
            dropped.append(rec)
            continue
        rec["sources"] = [who]
        key = norm_doi(rec["doi"]) or norm(rec["title"])
        if key in by_key:
            kept = by_key[key]
            if richness(rec) > richness(kept):
                out[out.index(kept)] = rec
                by_key[key] = rec
            continue
        by_key[key] = rec
        out.append(rec)
    note = f" ({len(dropped)} filtered out by pubs: {pubs})" if dropped else ""
    print(f"  {who:28} {len(groups):4} groups -> {len(out)} works{note}")
    if dropped and "--show-dropped" in sys.argv:
        for d in sorted(dropped, key=lambda r: -(r["year"] or 0)):
            print(f"        dropped  {d['year']}  {d['title'][:82]}")
    return out


def merge(all_records):
    """One entry per paper across every ORCID, remembering who contributed it."""
    merged, by_doi, by_title, dupes = [], {}, {}, [0]
    for rec in all_records:
        doi = norm_doi(rec["doi"])
        kept = by_doi.get(doi) if doi else None
        if kept is None:
            kept = by_title.get(norm(rec["title"]))
        if kept is not None:
            for s in rec["sources"]:
                if s not in kept["sources"]:
                    kept["sources"].append(s)
            if richness(rec) > richness(kept):          # upgrade the metadata in place
                sources = kept["sources"]
                kept.clear(); kept.update(rec); kept["sources"] = sources
            # index the alternative spellings too, so a third copy also lands here
            if doi and doi not in by_doi:
                by_doi[doi] = kept
            by_title.setdefault(norm(rec["title"]), kept)
            dupes[0] += 1
            continue
        merged.append(rec)
        if doi:
            by_doi[doi] = rec
        by_title[norm(rec["title"])] = rec
    return merged, dupes[0]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    sources = [(clean_orcid(a), a, True, []) for a in args] if args else orcid_sources()
    if not sources:
        sys.exit("No ORCID ids found — add them to data/people.yaml or pass them as arguments.")

    existing = []
    if OUT.exists():
        existing = yaml.safe_load(OUT.read_text(encoding="utf-8")) or []
    by_doi = {norm_doi(e["doi"]): e for e in existing if e.get("doi")}
    by_title = {norm(e.get("title")): e for e in existing}

    print(f"Reading {len(sources)} ORCID record(s) …")
    collected, failed = [], []
    for i, (oid, who, pubs, always) in enumerate(sources):
        if pubs is False:
            print(f"  {who:28} skipped (pubs: false)")
            continue
        try:
            collected.extend(fetch_records(oid, who, pubs, always))
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as exc:
            print(f"  ! {who} ({oid}) failed: {exc}")
            failed.append(who)
        if i < len(sources) - 1:
            time.sleep(0.5)                              # be polite to the API

    if failed and len(failed) == len(sources):
        sys.exit("Every ORCID request failed — not overwriting publications.yaml.")

    records, dupes = merge(collected)
    print(f"\n  {len(collected)} works collected -> {len(records)} distinct "
          f"({dupes} duplicate{'' if dupes == 1 else 's'} merged)")

    # carry the hand-written fields across
    seen = set()
    for rec in records:
        prior = by_doi.get(norm_doi(rec["doi"])) if rec["doi"] else None
        if prior is None:
            prior = by_title.get(norm(rec["title"]))
        if prior:
            for k in KEEP:
                if prior.get(k):
                    rec[k] = prior[k]
            seen.add(id(prior))

    hand_written = ("takeaway", "code", "data", "featured", "hidden")
    orphans = [e for e in existing if id(e) not in seen
               and (e.get("orcid") is False or any(e.get(k) for k in hand_written))]
    forgotten = sum(1 for e in existing if id(e) not in seen) - len(orphans)
    for e in orphans:
        e["orcid"] = False
        records.append(e)
    if forgotten:
        print(f"  dropped {forgotten} entr{'y' if forgotten == 1 else 'ies'} "
              f"no longer in anyone's ORCID")
    if orphans:
        print(f"  kept {len(orphans)} local-only entr{'y' if len(orphans) == 1 else 'ies'}")

    if "--no-authors" not in sys.argv:
        m = re.search(r"email\s*=\s*['\"]([^'\"]+)['\"]", (ROOT / "hugo.toml").read_text(encoding="utf-8"))
        enrich_authors([r for r in records if not r.get("hidden")], m.group(1) if m else "")

    records.sort(key=lambda r: (-(r.get("year") or 0), r.get("title", "")))

    header = (
        "# Generated by tools/orcid_to_yaml.py from the ORCID records listed in\n"
        "# data/people.yaml. Do not hand-edit the bibliographic fields — they are\n"
        "# overwritten on the next run.\n"
        "#\n"
        "# DO hand-edit these; they are preserved across runs, matched on DOI:\n"
        "#   takeaway  the plain-language sentence shown under a featured entry\n"
        "#   featured  true promotes the entry to Selected work at the top of the page\n"
        "#   hidden    true keeps it off the site entirely\n"
        "#   axes      research axes it belongs to\n"
        "#   code/data links to the repository or dataset it produced\n"
        "#\n"
        "# `sources` says which group member's ORCID an entry came from.\n\n"
    )
    OUT.write_text(
        header + yaml.safe_dump(records, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    shown = [r for r in records if not r.get("hidden") and r.get("type") not in ("data-set", "other")]
    print(f"\nWrote {OUT.relative_to(ROOT)}")
    print(f"  {len(records)} entries total, {len(shown)} papers visible on the site")
    print(f"  {sum(1 for r in shown if not r.get('takeaway'))} visible papers without a takeaway")
    if failed:
        print(f"  ! {len(failed)} record(s) could not be read: {', '.join(failed)}")


if __name__ == "__main__":
    main()
