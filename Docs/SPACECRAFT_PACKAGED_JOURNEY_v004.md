# Spacecraft slice — packaged journey receipt v004

Date: 2026-08-29 (late). Supersedes v003. Build:
`Builds/StarFactoryTycoon_v007/Windows/LineBossCarFactory.exe`,
BuildCookRun Development, exit 0.

## Journey — Scout canonical, supply-fed (exit 0)

`BuildLine` → `Place DeliveryDock` → `BuildEconomy 2` → `Start 2` →
`Run 1800 1.0` → `Status`, unattended `-NullRHI`:

    CONTRACT SC-CONTRACT-001 SCOUT-01 x2 dispatched=2 state=2  (Complete)
    revenue=30000000 pence  (300,000 cr)

Log: `C:\Temp\pkg007.log`.

## What this revision carries over v006

- The **site hub**: the overview is one painted picture with twelve
  clickable places, replacing the 3D site view. Ship factory open,
  power plant buildable, the rest padlocked with named reasons.
- **The ship factory stands on the site from the start**, placed
  through the build authority rather than seeded into the map.
- **Bulk buying**: deliveries land as much as fits and keep the rest on
  the lorry, a dock with any room accepts an order of any size, and the
  panel has a BUY QUANTITY control (x1 / x5 / x20).
- **The hall shell and floor**: walls, roof grid, lights, and painted
  storage / staging / traffic zones with hazard bay divisions.
- **The interface graded to the adopted palette** — hue-free, with
  `#EC3013` reserved for refusal.

## Claim

**Packaged playable** for the named journey in THIS Development
packaged revision, dev-command-driven, headless `-NullRHI`.

**NOT covered:** the rendered path in this revision (captured in the
editor, not from this package), mouse/keyboard build UI, Shipping
configuration, audio (none exists), onboarding (none exists),
controller input (none exists).

## Automation alongside

`LineBoss.Spacecraft`, 132 tests, 0 failed (106 clean, 26 with
warnings) — `Saved/Automation/PanelPalette_v001/index.json`.
