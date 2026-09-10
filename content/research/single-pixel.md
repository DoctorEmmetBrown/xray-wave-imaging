---
title: "Single-pixel sensing for fluorescence and scattering"
ptype: "axis"
short: "Single-pixel"
motif: "grid"
weight: 25
blurb: "A detector with no spatial resolution at all, plus a patterned beam, plus reconstruction — and you get a fluorescence or scattering map anyway. It is how we reach contrasts that no camera can image directly."
lead: "Some of the most informative X-ray signals — element-resolved fluorescence, angle-resolved scattering — arrive at detectors that cannot form an image. Structure the illumination instead of the detection, and the image comes back in software."
---

## The problem with the good contrasts

The two richest X-ray contrasts are the two hardest to photograph.

**Fluorescence** tells you which element sits where, at trace concentration, with a specificity no
absorption measurement approaches. But a fluorescence photon leaves the sample in a random
direction and carries no information about where it came from. The usual answer is to raster-scan a
focused beam: exquisite maps, one pixel at a time, and a full tomogram that takes days of beamtime
nobody has.

**Small-angle scattering** tells you about structure far below the resolution of the detector.
Measuring it properly means a point-scanning SAXS instrument, and a full tensor tomogram — the
orientation of that sub-pixel structure in three dimensions — is a heroic experiment.

## Structure the illumination, not the detection

Single-pixel imaging inverts the problem. Rather than asking the detector to resolve position, we
pattern the beam and record a sequence of total intensities on a detector with no spatial resolution
whatsoever. Each measurement is one projection of the sample onto one known pattern; the image is
recovered by solving the resulting inverse problem. Choose the patterns well — and choose the
regulariser well — and far fewer measurements are needed than the number of pixels you recover.

This is the same intellectual move as everything else in the group. In
[modulation-based imaging](../modulation-based-imaging/) a mask encodes the wavefront so a camera
can read phase; here a patterned beam encodes position so a bucket detector can read chemistry. In
both cases the physics is put in the forward model and the pixels are recovered by inversion.

## What we are building

**XRF ghost tomography** — element-specific three-dimensional maps from structured illumination and
a single-element fluorescence detector, replacing the raster scan with a compressive acquisition.

**SAXS tensor tomography** — full reconstruction of the orientation of sub-pixel structure in a
volume, from projections that mix scattering directions together.

Both run under the [MIAI FANFARES chair](../projects/fanfares/), held jointly with Nicolas Ducros
at CREATIS — whose group built much of the single-pixel imaging methodology — and Nicola Viganò at
CEA IRIG. Two doctoral contracts run on these questions until 2029.

<span class="todo">To add: a figure of the pattern sequence and a reconstructed elemental map, and a
sentence on which beamlines this runs at.</span>
