#!/usr/bin/env python3
"""
Regenerate data/publications.yaml from the ORCID records of the whole group.

    python3 tools/orcid_to_yaml.py                    # every ORCID in data/people.yaml
    python3 tools/orcid_to_yaml.py 0000-0002-... ...  # only the ids given

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
KEEP = ("takeaway", "code", "data", "axes", "featured", "hidden")
ORCID_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
ORCID_URL = re.compile(r"^https?://(?:www\.)?orcid\.org/", re.I)


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
            found.append((oid, "site owner")); seen.add(oid)

    if PEOPLE.exists():
        for p in yaml.safe_load(PEOPLE.read_text(encoding="utf-8")) or []:
            oid = clean_orcid(p.get("orcid"))
            if not oid or oid in seen or p.get("pubs") is False:
                continue
            if not ORCID_RE.match(oid):
                print(f"  ! skipping malformed ORCID for {p.get('name')}: {p.get('orcid')!r}")
                continue
            found.append((oid, p.get("name") or oid)); seen.add(oid)
    return found


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def norm(title):
    return re.sub(r"[^a-z0-9]+", "", (title or "").lower())


def extract(summary):
    title = (summary.get("title") or {}).get("title", {}).get("value", "").strip()
    venue = (summary.get("journal-title") or {}).get("value", "") or ""
    year = ((summary.get("publication-date") or {}).get("year") or {}).get("value")
    doi = ""
    for eid in ((summary.get("external-ids") or {}).get("external-id") or []):
        if eid.get("external-id-type") == "doi":
            doi = (eid.get("external-id-value") or "").strip()
            break
    return {
        "title": title,
        "venue": venue,
        "year": int(year) if year and str(year).isdigit() else 0,
        "type": (summary.get("type") or "article").lower().replace("journal-article", "article"),
        "doi": doi,
        "authors": "",
    }


def richness(rec):
    """Which of two records for the same paper to keep."""
    return (bool(rec.get("venue")), bool(rec.get("doi")), rec.get("type") == "article")


def fetch_records(orcid, who):
    """Every usable work in one ORCID record, already de-duplicated internally."""
    works = get(f"{API}/{orcid}/works")
    groups = works.get("group", [])
    out, by_key = [], {}
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
        rec["sources"] = [who]
        key = rec["doi"].lower() or norm(rec["title"])
        if key in by_key:
            kept = by_key[key]
            if richness(rec) > richness(kept):
                out[out.index(kept)] = rec
                by_key[key] = rec
            continue
        by_key[key] = rec
        out.append(rec)
    print(f"  {who:28} {len(groups):4} groups -> {len(out)} works")
    return out


def merge(all_records):
    """One entry per paper across every ORCID, remembering who contributed it."""
    merged, by_doi, by_title = [], {}, {}
    for rec in all_records:
        doi = rec["doi"].lower()
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
            continue
        merged.append(rec)
        if doi:
            by_doi[doi] = rec
        by_title[norm(rec["title"])] = rec
    return merged


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    sources = [(clean_orcid(a), a) for a in args] if args else orcid_sources()
    if not sources:
        sys.exit("No ORCID ids found — add them to data/people.yaml or pass them as arguments.")

    existing = []
    if OUT.exists():
        existing = yaml.safe_load(OUT.read_text(encoding="utf-8")) or []
    by_doi = {e["doi"].lower(): e for e in existing if e.get("doi")}
    by_title = {norm(e.get("title")): e for e in existing}

    print(f"Reading {len(sources)} ORCID record(s) …")
    collected, failed = [], []
    for i, (oid, who) in enumerate(sources):
        try:
            collected.extend(fetch_records(oid, who))
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as exc:
            print(f"  ! {who} ({oid}) failed: {exc}")
            failed.append(who)
        if i < len(sources) - 1:
            time.sleep(0.5)                              # be polite to the API

    if failed and len(failed) == len(sources):
        sys.exit("Every ORCID request failed — not overwriting publications.yaml.")

    records = merge(collected)

    # carry the hand-written fields across
    seen = set()
    for rec in records:
        prior = by_doi.get(rec["doi"].lower()) if rec["doi"] else None
        if prior is None:
            prior = by_title.get(norm(rec["title"]))
        if prior:
            for k in KEEP:
                if prior.get(k):
                    rec[k] = prior[k]
            if not rec["authors"] and prior.get("authors"):
                rec["authors"] = prior["authors"]
            seen.add(id(prior))

    orphans = [e for e in existing if id(e) not in seen]
    for e in orphans:
        e["orcid"] = False
        records.append(e)
    if orphans:
        print(f"  kept {len(orphans)} local-only entr{'y' if len(orphans) == 1 else 'ies'}")

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
