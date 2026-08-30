# Brand palette adoption — v001

**Date:** 2026-08-29
**Status:** Validation-only — source and automation evidence, no packaged journey.
**Supersedes:** the standing note in `CLAUDE.md` that brand and colour are OPEN.

## What changed

The game had no colour authority. `LBSpacecraftWIPPresentationActor.cpp`
carried **64 ad-hoc `FLinearColor` literals**, every one chosen by eye against
Car Manufacture screenshots. That is how two of them — machine amber and
warning orange — drifted close enough to be mistaken for each other on screen,
and it is why no review caught it: each literal was individually plausible.

The owner commissioned a brand identity and two implementation specs
(rev A, then rev B). Palette **1g** and type **1i** are chosen. The wordmark
(**1a** plant signage vs **1b** works plate) remains the owner's call and is
not blocked by anything here.

`Source/LineBossCarFactory/LBSpacecraftPalette.h` is now the single place
every colour is decided.

## The governing rule

> No world surface may be both **bright** and **saturated**, and only one of
> the interface and the machinery is allowed to carry a hue at all.

The purpose is one promise: **colour belongs to the ships.** A craft wears its
customer's livery and can only be the most colourful thing on screen if
nothing else competes.

## What the measurement found

The spec's most useful contribution was a corrected diagnosis. The amber
collision had been treated as a **hue** problem, and every attempted fix moved
hues — which introduced a new factory-owned colour each time and broke the
"colour belongs to the ships" rule.

Measured, the amber actually running in the game is:

| | linear | sRGB | S | V |
|---|---|---|---|---|
| shipped | `(0.86, 0.47, 0.10)` | `#EEB459` | 0.63 | **0.94** |
| spec | `(0.392, 0.171, 0.034)` | `#A87334` | 0.69 | **0.66** |

Saturation was already inside the ceiling. **Brightness was 28 points over
it.** The fault was never the hue.

## Enforcement, not convention

Four automation tests under `LineBoss.Spacecraft.Palette` hold the rules:

- `BakedValuesMatchAuthoredHex` — the header stores linear values with the
  authored sRGB hex in a comment, because converting during static
  initialisation would depend on engine table ordering. This test re-derives
  every token from its hex so the comment cannot silently go stale.
- `NoWorldSurfaceIsBrightAndSaturated` — the governing rule.
- `MachineAmberRespectsItsCeiling` — plus the 20-point saturation gap that
  keeps crates from merging with machinery when seen from above.
- `InterfaceCarriesExactlyOneHue` — every panel token hue-free; refusal red
  the sole exception; **warning explicitly not orange**, which is the
  assertion that prevents the original collision recurring.

`Tools/chroma_acceptance_v001.py` runs the spec's frame test on a screenshot:
excluding hazard striping, non-ship pixels above 60% saturation must stay
under 8% of frame, and the most saturated pixel must belong to a hull.

## Two findings the tests produced on their first run

**1. The spec's stated ceilings are rounded percentages of its own tokens.**
`#A87334` measures S 0.6905, written as "69%". A hard comparison fails the
canonical value for being itself. The tests allow half a point of rounding
headroom — enough for the rounding, far too little to admit a real change.

**2. `Machine.Amber.Trim #C08A3C` is V 0.75, nine points above the ceiling
the spec states for amber.** The spec's own trim token exceeds its own limit.

The reading taken is that the ceiling governs *surfaces* and trim is not one:
the spec restricts amber to "arm segments, fitting heads and edge strips" and
puts every machine surface over 0.5 m² on pale housing instead, so trim is by
definition a thin bright edge — the same shape of exemption hazard striping
already gets. The saturation ceiling is still enforced on it; only the
brightness half is relaxed.

**This is an inference, not something the spec says, and it is flagged for the
next revision.** Inferring a rule is how the original collision was made.

## What this does not cover

- **No packaged journey has been run against these values.** Validation-only.
- The 64 presenter literals are **not yet migrated** — the header and its
  tests exist; the floor is still painted by hand at time of writing.
- The spec's rule that every machine surface over 0.5 m² takes
  `Machine.Housing.Pale` is **not yet applied**. Station placeholder blocks
  are currently graphite `(0.16, 0.17, 0.18)`; the rule implies they should be
  pale. That is a large visual change and wants a rendered frame and the
  owner's eye before it is claimed as an improvement.
- Liveries, the outdoor site and icons are specified in rev B but unbuilt.
