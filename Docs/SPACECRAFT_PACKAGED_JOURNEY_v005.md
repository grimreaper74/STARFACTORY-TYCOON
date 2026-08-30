# Spacecraft slice — packaged journey receipt v005

Date: 2026-08-30. Supersedes v004. Build:
`Builds/StarFactoryTycoon_v009/Windows/LineBossCarFactory.exe`,
BuildCookRun Development, exit 0.

## Why v009 exists, and why v008 must not be used

**v008 was packaged at 10:17; the Meshy gate correction landed at
10:39.** v008 therefore contains the over-broad asset gate that wrongly
blocked out the paint booth, the two already-remade drones, the lift
cradle and the parts carriers. It runs correctly but MISREPRESENTS how
the game looks. v009 is the same code with the corrected gate.

## Journey — Scout canonical, supply-fed (exit 0)

`BuildLine` -> `Place DeliveryDock` -> `BuildEconomy 2` -> `Start 2` ->
`Run 1800 1.0` -> `Status`, unattended `-NullRHI`:

    CONTRACT SC-CONTRACT-001 SCOUT-01 x2 dispatched=2 state=2  (Complete)
    revenue=30000000 pence  (300,000 cr)

Log: `C:\Temp\pkg009.log`.

## What this revision carries over v007

- **The six-assembly Scout-01 v002 craft**, commissioned through Claude
  Design and wired in: 12.00 x 7.00 x 2.54 m, 119,890 triangles across
  six named objects. Nanite disabled on `Navigation` at the asset,
  because it carries the `canopy_glass` slot and Nanite cannot render
  translucency.
- **The Meshy blockout**, and its same-day correction.

## Claim

**Packaged playable** for the named journey in THIS Development
packaged revision, dev-command-driven, headless `-NullRHI`.

**NOT covered:** the rendered path in this revision (the journey above
ran `-NullRHI`), mouse/keyboard build UI, Shipping configuration, audio
(none exists), onboarding (none exists), controller input (none).

**Visual state is deliberately incomplete.** Much of the factory's
machinery stands as blockouts pending replacement art — see
`Docs/MESHY_BLOCKOUT_PUNCHLIST_v001.md`. This build is honest about the
loop, not representative of finished visuals.

## Automation alongside

`LineBoss.Spacecraft`, 132 tests, 130 pass, **2 fail by design** -
`RunwayPaintAndStrobesFollowTheRig` and `StationAccentsReflectRealState`
assert behaviour that exists only when a real mesh is present, which is
false everywhere while the blockout flag is on. They recover when it
flips back; neither should be weakened.
`Saved/Automation/MeshyBlockoutCorrected_v001/index.json`.
