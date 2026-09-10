---
title: "FANFARES"
ptype: "project"
weight: 5
funder: "MIAI Grenoble Alpes chair"
role: "Co-holder"
grantId: ""
period: "2026 – 2029"
partnersShort: "CREATIS · CEA IRIG"
partners:
  - "Nicolas Ducros — CREATIS, INSA Lyon"
  - "Nicola Viganò — CEA IRIG MEM"
axes: ["single-pixel", "directional-dark-field", "phase-retrieval"]
blurb: "A MIAI Grenoble Alpes chair, held with Nicolas Ducros (CREATIS) and Nicola Viganò (CEA IRIG), on single-pixel and structured-illumination sensing: recovering element-resolved fluorescence maps and full scattering tensors from detectors that cannot form an image. It funds two doctoral contracts to 2029 and anchors the group's whole computational-imaging programme."
lead: "A MIAI Grenoble Alpes chair on single-pixel sensing for X-ray fluorescence and small-angle scattering — the group's main computational imaging effort."
---

## Objective

The chair takes on the two X-ray contrasts that carry the most information and resist imaging the
hardest: **fluorescence**, which identifies elements at trace concentration but arrives at a
detector with no positional information, and **small-angle scattering**, which describes structure
far below the pixel but requires point-by-point acquisition to measure properly.

Both are usually addressed by scanning — a focused beam, one position at a time, days of beamtime
for a single tomogram. FANFARES replaces the scan with **structured illumination and
reconstruction**: pattern the beam, record a sequence of total intensities, and recover the map by
solving an inverse problem. Done well, the number of measurements needed is far smaller than the
number of pixels recovered.

That combination is why the chair sits where it does. Nicolas Ducros' group at CREATIS built much
of the single-pixel imaging methodology and its learned reconstruction; Nicola Viganò at CEA IRIG
works on tensor tomography and the inversion of scattering data; this group brings the X-ray
wave-optics and the experimental platforms. The method work is described on the
[single-pixel sensing](../../single-pixel/) page.

## Doctoral contracts

Two three-year contracts run from October 2026 to September 2029:

- **SAXS tensor tomography** — reconstructing the three-dimensional orientation of sub-pixel
  structure from projections that mix scattering directions. Based at IAB in Grenoble.
- **XRF ghost tomography** — element-specific three-dimensional maps from a compressive acquisition
  and a single-element fluorescence detector. Hosted at CREATIS in Lyon.

Both students appear on the [people](/people/) page.

## Why it matters beyond the chair

MIAI is Grenoble's artificial-intelligence institute, and the chair is explicit that the learning
belongs in the reconstruction rather than in place of the physics. A learned prior that fills in
what a compressive acquisition could not measure is doing legitimate work; a network that replaces
the forward model is not. Keeping that line clear is part of the scientific programme, not a
caveat to it.

<span class="todo">To add once the first results are in: a figure of the pattern sequence and a
reconstructed elemental map.</span>
