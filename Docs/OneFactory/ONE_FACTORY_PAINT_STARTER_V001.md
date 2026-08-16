# OneFactory native Paint starter v001

Status: isolated implementation complete; shared PlayerBuilder integration pending

## Player promise

Paint is intentionally readable and inexpensive to simulate. A body arrives on a
skid, follows one canonical process route, enters the spray booth in its current
state and leaves in the selected body colour. The line exposes colour/programme,
safe positioning and commissioning choices; it does not pretend that invisible
spray robots, booth internals or a second process simulation exist.

The eight responsibilities are:

1. body-skid receiving;
2. pretreatment/wash black box;
3. ED-coat logical process seam;
4. flash-off black box;
5. open-ended black-box spray booth (the colour state change);
6. reusable open-ended curing oven;
7. quality-light inspection tunnel;
8. painted-body dispatch.

Seven exact sequential routes preserve the material-state hand-off from body in
white to inspected painted body. There is no bypass, hidden branch or seeded WIP.

## Data authority

`ALBOneFactoryPaintStarterLayoutAuthority` owns only the versioned layout and
programme snapshot. Its constructor creates no machines, presentation or WIP.

- `CaptureLayout` and `RestoreLayout` form a lossless, mutation-free validation
  boundary.
- `SetStationPaintProgramme` may be invoked at ED coat, spray or quality, but
  commits one target colour/programme to all five downstream responsibilities.
- `MoveStation` commits only if every exact footprint stays inside the Paint bay,
  remains non-overlapping and keeps both adjacent routes in reach.
- programme change, movement and commissioning fail closed while any active or
  reserved unit ID exists anywhere in the snapshot.
- restore accepts a coherent active-WIP snapshot but rejects empty or duplicated
  unit ownership.
- commissioning is explicit, validated and idempotent.

The launch palette is Arctic white, Foundry graphite, Cairnwell teal, Signal red
and Aurora blue. Body-in-white and ED-primer grey are process states and cannot be
chosen as finished-body programmes.

## Exact native provenance boundary

The profile trusts two exact native-code classes and ten direct object paths. It
does not trust a broad `Candidates` directory.

| Direct dependency | Required LODs | Declared provenance |
|---|---:|---|
| curing oven tunnel v001 | 3 | native authored |
| pretreatment/wash tunnel v001 | 3 | native authored |
| flash-off tunnel v001 | 3 | native authored |
| quality-light tunnel v001 | 3 | native authored |
| body-skid carrier v001 | 3 | native authored |
| Paint service set v001 | 3 | native authored |
| air/extraction module v001 | 3 | native authored |
| spray booth runtime v002 | 2 | native authored from original procedural source |
| Engine Cube | 1 | native procedural |
| Engine BasicShapeMaterial | 0 | native procedural material |

The profile and presentation contract reject changed order, changed object path,
changed provenance, unknown assets under the same root, and Meshy/external-source
tokens.

## Visual-only presentation

`ALBOneFactoryPaintStarterPresentationActor` is non-ticking, non-replicated,
collision-free and navigation-neutral. It resolves all ten dependencies and the
exact `3/2/1` LOD contract before adding any instance. A failure clears the actor;
partial lines are never exposed.

The frozen presentation contains 11 HISM batches and 32 instances:

- eight principal process/logistics items (including exactly one spray booth);
- eight exterior support items;
- seven floor-route markers;
- eight semantic status markers;
- one selected-colour marker.

Status is amber before commissioning and green after commissioning. The colour
marker uses the authoritative body programme. Imported process shells retain
their authored materials and LODs. There are zero spray robots, windows, side
vehicle doors, modelled process internals or WIP proxies.

ED coat is deliberately represented by its logical responsibility, body skid and
exterior service/extraction dressing. No tank or hidden mechanism is invented.

## Shared PlayerBuilder seam (deferred until Assembly freezes)

No shared subsystem, HUD, map, Content, Config or save file was changed in this
milestone. The later single-owner integration should expose these operations:

- create/delete the Paint starter authority and paired presentation atomically;
- select colour through `SetStationPaintProgramme`;
- move a station through `MoveStation`;
- commission through `Commission`;
- rebuild presentation only from the committed captured snapshot;
- persist exactly one Paint layout snapshot and never presentation/WIP proxies.

The canonical spawn must remain opt-in from the empty OneFactory shell.

## Focused automation

Six new tests cover the exact provenance profile and paths, eight-stage/seven-route
topology, programme propagation, capture/restore, WIP fail-closed behavior,
transactional movement and commissioning, deterministic 11-batch/32-instance
inventory, fresh asset/LOD resolution, all-or-nothing HISM commit and rejection of
hidden-internal/WIP presentation claims.
