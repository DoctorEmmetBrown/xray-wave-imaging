# X-ray Wave Imaging Group — website

Static site for the X-ray Wave Imaging Group, a group within the Translational
Theranostics team (3T) at the Institute for Advanced Biosciences, Grenoble.

Built with [Hugo](https://gohugo.io) (extended, v0.140+). No theme, no submodules,
no JavaScript framework — the templates and one stylesheet are all in this repo.

---

## Run it locally

```bash
# macOS
brew install hugo
# Debian/Ubuntu
sudo snap install hugo

hugo server -D          # http://localhost:1313, live reload
hugo                    # one-off build into public/
```

## Deploy

Pushing to `main` triggers `.github/workflows/deploy.yml`, which builds and
publishes to GitHub Pages. Enable it once, under **Settings → Pages → Source →
GitHub Actions**.

For a custom domain: add the domain under Settings → Pages, put the same name in
`static/CNAME`, and update `baseURL` in `hugo.toml`.

---

## Adding things

Everything routine is a data file or one Markdown file. You should not need to
touch `layouts/` to keep the site current.

### A publication

Don't add it by hand — resync from ORCID, then commit the result:

```bash
pip install pyyaml                # once
python3 tools/orcid_to_yaml.py    # rewrites data/publications.yaml locally
git add -A && git commit -m "Resync publications"
git push                          # one push, one CI build
```

Resync first, push second. The script reads your working copy and never talks
to GitHub, so pushing beforehand gains nothing and costs a wasted build that
publishes the old list. If a resync goes wrong, `git checkout
data/publications.yaml` undoes it — nothing has left your machine yet.

The list is built from **every ORCID in `data/people.yaml`**, not just one
person's. Fill in a member's `orcid` and their publications join the page,
including papers no one else in the group co-authored; clear it and they leave
again. To show someone's ORCID link without pulling in their bibliography, add
`pubs: false` under it. The `orcid` value can be the bare identifier or the
full `https://orcid.org/…` URL; both are accepted.

For a member whose bibliography is mostly outside the group's subject, `pubs:
xray` keeps only the work where an X-ray image was involved, judged on the
title and journal. The vocabulary is one regular expression at the top of
`tools/orcid_to_yaml.py` — widen it there if it holds something back. Audit it
with:

```bash
python3 tools/orcid_to_yaml.py --show-dropped
```

A keyword filter cannot read a paper, so some genuinely X-ray work has a title
that never says so. List those DOIs under `pubs_also:` next to the person and
they are kept whatever the filter decides.

Papers appearing in more than one member's record are merged into a single
entry and the fuller metadata wins. Matching is on the DOI, normalised first —
members deposit through different tools, so the same paper arrives as
`10.1038/x`, `https://doi.org/10.1038/X` or `doi:10.1038/x`, and comparing the
raw strings would leave visible duplicates. Where a DOI is missing or differs
between deposits, a normalised title is the fallback. Each entry keeps a
`sources` field naming whose records it came from, which is how you find out
why something is on the list, and the run prints how many duplicates it merged
so you can see it working.

The script **preserves** everything written by hand — `takeaway`, `featured`,
`hidden`, `axes`, `code`, `data` — matching on DOI, so resyncing is always safe.
Entries that exist locally but in nobody's ORCID (a paper submitted but not yet
deposited) are kept and flagged `orcid: false`.

Then write a takeaway for anything new worth featuring — that one plain-language
sentence is the reason someone reads the list instead of skimming Google
Scholar. The run prints how many visible papers still lack one.

### A funded project

Copy an existing file in `content/research/projects/`. The front matter drives
both the project page and the summary rows on the home and Research pages:

```yaml
---
title: "ACRONYM"
ptype: "project"          # required, do not rename
weight: 60                # ordering, low first
funder: "ANR"
role: "Coordinator"
grantId: "ANR-XX-CEXX-XXXX"
period: "2027 – 2031"
partnersShort: "CREATIS · CEA"     # the compact right-hand column
partners: ["Full name — institution"]
axes: ["directional-dark-field"]   # filenames from content/research/
blurb: "The paragraph shown in the list."
lead: "One line under the page title."
---
```

### A research axis

Same idea, `ptype: "axis"` in `content/research/`. `motif` picks the generated
figure plate: `speckle`, `waves`, `grid` or `tissue`. Replace these with real
images as soon as you have them — they exist so the site is not full of grey
boxes on day one.

### Illustrations

Put image files under `assets/img/`, in whatever sub-folders you like. Hugo
resizes them and converts to webp at build time, so commit the full-resolution
export straight from the beamline — do not hand-optimise first.

Three places take an image:

**1 — the plate on a research axis or project card.** Add to that page's front
matter:

```yaml
image: "research/dentin-ddf.jpg"     # path relative to assets/img/
imageAlt: "orientation map of dentinal tubules"
imageCaption: "Directional dark-field of human dentin, hue is fibre orientation."
```

The generated motif disappears the moment `image:` is set — on the card, and as
a wide plate under the page title.

**2 — anywhere in the body text**, with the figure shortcode:

```markdown
{{< figure src="research/membrane-sem.jpg"
           caption="SEM of the Vogel-spiral membrane. Dots are 30 µm across."
           alt="scanning electron micrograph of a patterned absorber" >}}
```

Add `wide="true"` to let a figure break out of the reading column on wide
screens. A `src` starting with `/` is used verbatim, for anything you would
rather keep in `static/`.

**3 — member photographs.** Put them in `static/img/people/` and reference them
in `data/people.yaml` (or `data/alumni.yaml`) as `photo: "/img/people/brun.jpg"`.
Square crops on a **white** background — a PNG with transparency composites to
black. The card shows the person's initial until a file is there.

If a referenced file is missing, the build fails with the path and the page
name rather than shipping a broken image.

### People

Two files, both under `data/`, both plain lists in page order:

- **`data/people.yaml`** — current members, down to doctoral level. Per person:
  `name`, `role` (the public job title, not the grade), `topic` (one line on
  what they work on), `photo`, `linkedin`, `scholar`, `orcid` (bare identifier,
  no URL) and `email`. Leave any field as `""` and the card simply omits it —
  except that a person with no link at all shows a coral marker, so the gaps
  stay visible.
- **`data/alumni.yaml`** — former members. Same idea plus `role`, which must be
  `postdoc`, `phd` or `med`; that is what groups them on the page. `now` is
  where they went next; `linkedin` turns the name into a link and is the easy
  way to answer the same question.

### Software, datasets, openings

`data/software.yaml`, `data/datasets.yaml`, `data/openings.yaml`. The comments
in each file document the fields. The **We're hiring** link in the navigation
appears only while at least one opening has `status: open`.

---

## Things deliberately left unfinished

Anything still to be written is wrapped in `<span class="todo">…</span>` and
renders in coral with a dashed underline, so unfinished text is impossible to
miss on the live site. Search for it before launch:

```bash
grep -rn 'class="todo"' content/ data/
grep -rn 'TODO' data/
```

Known gaps, in rough order of how much they matter:

1. **MUSITOX** — the whole page. Programme, period, partners, subject.
2. **Repository URLs and licences** in `data/software.yaml` — the `pip install`
   lines are plausible placeholders, not real package names.
3. **Images.** Every figure on the site is generated by code. Six to ten real
   ones — dark-field maps, tomographic renders, membrane SEM, a beamline shot —
   would change the site more than any other single change.
4. **The hero viewer** runs on a simulated phantom (`assets/js/channels.js`).
   Swapping in four pre-computed PNGs from a real dentin or lung dataset is a
   contained change: replace `buildFields()`, keep the tab logic.
5. **People**, beyond the single seeded entry.
6. **Dataset DOIs** in `data/datasets.yaml`, currently empty.

---

## Design notes

The site commits to a single warm dark theme rather than following the reader's
light/dark preference. That is a choice, not an omission: the subject is images
made in a dark hutch, and dark grounds show them best. All colours are painted
explicitly in `assets/css/main.css` — nothing is inherited from the browser.

Typefaces are loaded from Google Fonts: Fraunces (display, variable, with the
`SOFT` and `WONK` axes actually in use), IBM Plex Sans and Mono, and Caveat for
the handwritten margin notes. Each has one job.
