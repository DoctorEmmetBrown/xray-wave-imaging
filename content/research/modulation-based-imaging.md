---
title: "Modulation-based imaging"
ptype: "axis"
short: "MoBI"
motif: "speckle"
weight: 10
blurb: "A random or spiral mask in the beam turns any source into a wavefront sensor. One reference image, one sample image, and the full wave-optical signal falls out."
lead: "Put a patterned absorber in the beam, photograph it twice — once alone, once with the sample — and the way its pattern moves, blurs and dims tells you everything the wave did on its way through."
---

## The idea

Conventional radiography measures one number per pixel: how much of the beam survived. A wavefront carries a great deal more than that. It is refracted by gradients in electron density, and it is scattered by structure too small for the detector to resolve. Both effects are invisible to a plain intensity measurement, because both conserve photons.

Modulation-based imaging makes them visible with a single cheap component. A mask — a random speckle membrane, or a Vogel spiral of absorbing dots — is placed in the beam, and its projected pattern is recorded with and without the sample. Locally, that pattern **shifts** where the sample refracts, **blurs** where the sample scatters, and **dims** where it absorbs. Recovering those three quantities from the two images is an inverse problem, and it is where most of our work goes.

## Why it matters

The technique needs no gratings, no interferometer, no alignment to sub-micron tolerances, and no coherent source. That is the whole argument: methods that only work at a synchrotron stay at the synchrotron. We develop ours so they survive the move to a laboratory X-ray tube, where they can be used by people who will never be granted beamtime.

Our laboratory platform is a Xenocs Xeuss 3.0 at 8.6 keV with a 75 µm pixel pitch, which doubles as a SAXS instrument — so we can validate what the dark-field channel claims against a direct scattering measurement on the same sample, in the same session.

## Current questions

- How should the mask be designed? Pattern statistics, feature size and material all trade against each other, and the optimum depends on the detector as much as the sample.
- How far can the *q*-range be extended by varying propagation distance and analysis-window size, rather than by changing hardware?
- What breaks when the source is a laboratory tube rather than a synchrotron beam — and how much of that is recoverable in software?

<span class="todo">To add: a figure of the membrane and a representative retrieved triplet, plus a short paragraph on the membrane fabrication work.</span>
