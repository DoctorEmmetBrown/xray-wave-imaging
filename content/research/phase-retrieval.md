---
title: "Phase retrieval and inverse problems"
ptype: "axis"
short: "Inverse problems"
motif: "grid"
weight: 30
blurb: "Single-shot joint retrieval of phase and attenuation, variational solvers with the right regularisation, and learned priors where they genuinely beat the analytic ones."
lead: "Every method on this site ends in the same place: an ill-posed inverse problem, a limited number of measurements, and a decision about what prior knowledge is legitimate to inject."
---

## The problem

A detector records intensity. What we want is the complex refractive index — its real part for phase, its imaginary part for attenuation. Recovering both from a single acquisition is underdetermined, and the standard escape route is to assume the sample is made of one material, which is exactly the assumption that fails on the biological tissue we care about.

We work on retrievals that relax that assumption: joint phase and attenuation recovery from a single image pair, posed as a variational problem with regularisation chosen for the structure actually present in the data rather than for analytical convenience. Directional weighting matters here — an isotropic regulariser will happily smooth away the fibre orientation you were trying to measure.

## Where learning helps, and where it does not

Learned priors are extremely good at the part of the problem that is genuinely statistical — denoising, filling aperture-starved components — and unreliable at the part that is physical. Our position is that the forward model should stay explicit and the prior should be the learned component, not the other way round. It also means being honest about small datasets: a network trained on a dozen samples is a prior with an opinion, and it should be evaluated as one.

Self-supervised approaches are of particular interest because ground truth in this field is usually unavailable, expensive, or subtly wrong.

## Practical consequences

- Regularisation that respects local orientation rather than fighting it.
- Solvers that stay stable when one component of the measurement is poorly conditioned.
- Uncertainty that is reported rather than hidden, because a reconstruction without an error bar is a picture, not a measurement.

<span class="todo">To add: the GdTV joint retrieval result and a pointer to the corresponding paper once it is out.</span>
