# Weld, paint and assembly — release-standard pass, 2026-08-16

Companion to the
[press release note](../PressShop/PRESS_SHOP_RELEASE_STANDARD_NOTE_2026-08-16.md),
worked against the same
[feature-finish checklist](../ReleaseGate/FEATURE_FINISH_CHECKLIST.md).
Captures: `Captures/20260816_13_Standard_*.png`.

## Body/weld

**The release content was already there.** The frozen 469-instance weld starter
presentation renders the real native robots — 36 seven-link arms and 16 C-guns
from `BodyShopRobotNative_v001` plus the support kit — under its exact-count
contract. The one defect was mine: the dev dressing had placed a second, pack
robot set on top of release content. Weld stations now carry only guarding,
cabinets, conveyor and the QA light ramp around the native presentation.

Save/reload is proven with a unit standing mid-weld — the exact round trip in
the press note saved and restored `OF_BODY_WELD_POS_01 / 7/57 / cycle 25%` — and
the packaged v004 journey held and released a car at the weld quality gate.

**Open:** the native robots read small and dark at management distance; the
recovery-style answer is a scale/readability review of the native presentation
itself, which is a frozen-contract change and must be versioned, not overlaid.

## Paint

Booth modules stand either side of each paint station with the cure oven at the
cure stage; the ED/painted body WIP renders the real Cairnwell shell with the
authored ED-coat and paint-tint materials. The paint starter presentation's
tracked ED contract renders alongside without duplication. The packaged v003/v004
journeys carried a car through `OF_PAINT_SPRAY_BOOTH_001` on a player decision.

**Open:** the booths are Factory-pack stand-ins, not the native paint kit; the
`PaintLineNativeKit_v001` modules are cooked and available, and swapping them in
is the same measured-placement exercise as the press chain.

## Assembly

Station + robot + next part, per the market-position readability model: one
fitting robot, an operator bench opposite, a parts rack behind, at each of the
24 positions; trim through dispatch WIP renders the painted body. The packaged
journeys completed 57/57 with dispatch counted exactly once.

**Open:** no marriage/rolling-chassis distinct visuals yet (the finished-car
family carries those stages), and the same native-kit swap question as paint
once `AssemblyLineNativeKit_v001` gets a measured pass.

## Shared position

- **Save/reliability:** exact round trip proven in editor and in package v004.
- **Verification:** full suite 275/275; packaged journeys green in v003/v004;
  v005 (this pass: press machine chain, weld dedupe) packaging at time of
  writing.
- **Open project-wide:** localization, controller parity, multi-resolution
  captures, performance budget — as recorded in the press note and the
  finish checklist's own blocker list.
