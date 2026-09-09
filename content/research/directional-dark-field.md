---
title: "Directional dark-field"
ptype: "axis"
short: "DDF"
motif: "waves"
weight: 20
blurb: "Unresolved structure scatters anisotropically. We recover its orientation and spread per pixel — and we are pushing past the rank-2 tensor model that everyone currently assumes."
lead: "Fibres, pores and lamellae far below the pixel still leave a signature: they scatter the beam more in one direction than another. Read that signature and you can map microstructural orientation over a whole field of view in one shot."
---

## What the signal is

The dark-field channel measures how much a pixel's worth of sample blurs the wavefront. When the underlying structure is anisotropic — aligned collagen, dentinal tubules, a carbon-fibre bundle — the blurring is anisotropic too, and its principal direction is perpendicular to the structure. Measuring that direction and its strength at every pixel gives an orientation map of features the detector could never resolve directly.

This is, in effect, full-field small-angle scattering. A point-scanning SAXS measurement gives you the same information with better *q*-resolution and a beam-limited spatial resolution of about a millimetre, one point at a time. Dark-field gives it at the pixel, across the field, in a single acquisition.

## Beyond the tensor

Nearly all published work describes the anisotropy with a symmetric rank-2 diffusion tensor — three numbers per pixel. That description is exactly equivalent to truncating the angular scattering profile at harmonic order two, and it fails in ways that matter:

- **crossing fibres** average to a spurious single orientation, or to none;
- **dispersion and multimodality** are indistinguishable from each other;
- orientation becomes **unstable near degeneracy**, where the two eigenvalues meet;
- the tensor is tied to a Fokker–Planck picture that Pawula's theorem forbids truncating cleanly;
- the recovered magnitude depends on **correlation length**, so numbers are not comparable between setups.

Our current work recovers higher angular harmonics directly, without ever assembling a tensor — a band-resolved inversion that reaches harmonic order four and can separate crossed-fibre configurations where the tensor is structurally blind.

## Methods we maintain

**SerPy** performs the retrieval statistically, with no forward model of the scattering profile at all. Model-based Fokker–Planck inversions give a complementary answer; comparing the two — agreement in orientation, controlled disagreement in magnitude — is itself a result we are writing up.

<span class="todo">To add: the harmonic decomposition figure, and a sentence on the ALBA / FaXToR campaign lifting the 8 keV ceiling.</span>
