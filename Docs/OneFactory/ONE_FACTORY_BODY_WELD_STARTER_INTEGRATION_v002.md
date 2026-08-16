# Body/weld starter presentation — contracts v002 and v003

> **v003 (same evening).** The owner commissioned the missing weld models;
> the dress pack lands as its own versioned change on top of v002. Every
> robot now carries the PR004 dress trio (lower on the base stack, upper
> along the J2 link, wrist at J5) at a uniform 0.68 — the measured ratio at
> which the trio's 186 cm upper tube fits the weld robot's 125 cm links.
> Counts re-frozen: **29 batches, 597 instances** (489 + 3 × 36), the
> `Modular6Axis/Candidate_v020` root added to the validator windows and the
> cook list, tag `...Presentation.v003`, tests regenerated in the same
> commit (`ExactNativeFiveHundredNinetySevenInstanceContract`).

Supersedes the presentation section of
`ONE_FACTORY_BODY_WELD_STARTER_INTEGRATION_v001.md` (the layout/data contract
`MOORCROSS_BODY_WELD_STARTER_NATIVE_V001` — 18 positions, 18 programmes, 17
connections — is unchanged). One versioned change, tests regenerated in the
same commit, per the project's frozen-contract rule.

## What changed and why

The v001 presentation was frozen before a scale/readability review. The weld
audit quantified the consequences: the mirrored robots stood at station-local
Y = ±1240 cm — 10.7 m from a fixture their ~3 m arms could never address —
while the robot pack's own `Audit/contact_fk_validation_v001.json` validates
contact at ±300 cm (18/18 passes). Twenty of the 36 arms had no end-effector,
and the per-programme "fixture" was a flat engine-cube slab while the authored
fixtures sat token-forbidden in the validator.

## The v002 contract

- **Robots at the work**: pairs at station-local Y = ±300 cm, yaw ±35°, posed
  by the frozen PROCESS-phase contact FK angles from
  `contact_fk_validation_v001.json`, target selected by `LinePosition % 3`.
  The right side mirrors J1/J4/J6. `GetContactProcessPoseJointAngles` exposes
  the table; the contract test asserts it matches the JSON values.
- **A tool on every arm**: welding roles keep the 16 open C-guns; the other
  20 arms carry `SM_LB_BodyShopTool_PanelPick8Cup_v001`. The two tool batches
  always partition the 36 arms, so the canonical total is
  role-assignment-invariant.
- **Authored fixtures**: 15 framing programmes bind
  `SM_LB_BodyWeld_FramingFixture_v001` (BodyWeldLine/Runtime_v001, clean-room
  derivative with an Unreal promotion receipt); the 3 underbody programmes
  bind `SM_LB_BodyShop_UnderbodyFixture_v001` (BodyShopUnderbodySlice_v001,
  native Blender source, frozen roundtrip PASS). Both roots are deliberately
  unlocked in the validator; `Robots/WeldRobotRuntime` (Meshy-derived) is
  newly forbidden.
- **Counts re-frozen**: 26 batches (23 authored + 3 semantic engine cubes),
  **489 canonical instances** (469 + 20 tools). Per-batch expectations are in
  `GetExpectedInstanceCountForBatch`; fixtures split 15/3 by programme set.
- **Fail-closed visibility**: the builder pair validation and the save
  preflight reject a configured-but-hidden presentation; the tests assert
  hidden-on-spawn, visible-after-configure (per populated batch), and
  re-hidden-after-failed-configure.
- Tag: `LB.OneFactory.BodyWeldStarter.Presentation.v002`.

## Evidence

- Suite 275/275 with the regenerated contract
  (`ExactNativeFourHundredEightyNineInstanceContract`).
- Tour captures `Captures/20260816_26_WeldV002_*`: robot pairs stand against
  the framing fixtures with tools on every flange; the line reads as weld
  cells rather than scattered arms.
- Cook coverage: all three newly bound assets sit under already-cooked roots
  (BodyWeldLine/Runtime_v001, BodyShopUnderbodySlice_v001); the save
  preflight's `ResolveAll` now hard-loads them, giving a packaged check.
