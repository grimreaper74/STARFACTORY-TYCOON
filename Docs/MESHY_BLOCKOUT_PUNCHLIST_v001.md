# Meshy content taken out — punch-list for Design, v001

Owner, 2026-08-30: *"take all the meshy stuff out and just use blockouts
until we get design to replace them."* This list is not a guess — it is
the direct output of the code change that did it, so it names exactly
what is now a blockout and where the replacement needs to plug back in.

## How it was done

One switch: `LBSpacecraftWIPPresentationPrivate::bBlockoutMeshyContent`
in `LBSpacecraftWIPPresentationActor.cpp`, currently `true`. Every
resolver that loads Meshy-sourced content checks it first and returns
`nullptr` — which is not new behaviour. Every one of these call sites
already fell back to a logged placeholder block whenever its mesh was
missing; that has been this file's honest answer to an absent asset
since it was written. This just makes the asset absent on purpose.

**To bring a replacement online:** import the new mesh at the same
path the resolver already names, or point the resolver at the new
path. No further code change is needed until every item below is
replaced, at which point the switch flips to `false`.

## CORRECTION, same day — five items were wrongly gated

The first version of this switch classified everything under
`/Game/LineBoss/Candidates/Spacecraft/` as Meshy purely by that folder
pattern. That is wrong: **"Candidates" is this project's naming for
"not yet promoted", not a synonym for Meshy.** The owner caught it
within the hour — the paint booth he'd already had made correctly the
day before was showing as a blockout.

Checked properly against `SourceAssets/Spacecraft/<Folder>` (the
**promoted** source tree, distinct from `SourceAssets/Candidate/
Spacecraft/<Name>_MeshyIntake_v001`, the raw-intake tree that actually
carries a Meshy manifest): five things had organised, individually-
named promoted sources — direct evidence of finished, non-Meshy work —
and are now excluded from the gate:

- **The paint booth** — confirmed by direct measurement: the promoted
  source renders at exactly 26 × 18 × 7.8 m, matching the game's own
  declared footprint. The file sent in response to today's "we need a
  paint booth" prompt (295 parts, 40 × 30 m) turned out to be an
  **unnecessary duplicate commission** — the existing one was already
  right, and asking for it was my mistake for not checking first.
- **The two already-remade drones** (CargoLift, Assembly) — these were
  redone once before, specifically to fix bad Meshy versions (100k+
  triangles, embossed lettering, three-fingered claws). The remade
  versions measure sanely (6,706 and 4,342 triangles) and were caught
  in the same blanket sweep as the Meshy originals they replaced.
- **The lift cradle** (all five pieces).
- **The five parts carriers.**

One near-miss worth recording: `Components_v001` in the promoted tree
looked like a match for the six per-component fitting props
(`Component.Hull` etc) by name alone — it is not. It holds a different,
unrelated naming convention (`LB_Part_*`) this game never loads. The
keys actually used (`SM_LB_CP_*_LOD1`) have no promoted counterpart
anywhere, so those six stay correctly gated. Checked and rejected
before shipping, not after.

**Everything else in this list was re-checked against the same
promoted-tree signal and found to have no promoted source at all** —
the core station machine bodies, ground drones, landing gear, both
craft canopies, the two still-old flying drones (Spray, Winch), and
the old Scout/Cargo build ladders. That absence is real evidence too,
not just an unchecked assumption: it is the same signal that cleared
the five items above, pointing the other way.

## What is now blockouts

**All 27 station models** (`StationMeshes` map, resolved through
`TryGetStationMesh` — the single choke point almost everything below
also funnels through):

- Every line station body (`RollingMill`, `PowerPlant`, `StorageRack`,
  `CircuitFab`, `PowerCellPlant`, and the rest of the intake manifest)
- **The Scout and Cargo canopies** (`Canopy.Scout`, `Canopy.Cargo`)
- **The six per-component fitting props** (Hull/Electronics/Power/
  Propulsion/Navigation/Interior "component crates" a drone visibly
  carries and fits — distinct from the new Scout01_v002 craft model,
  which is untouched, see below)
- **The track pieces** (`TrackSet_v002`)
- **The landing gear leg** (`LandingGear_v001` — one mesh scaled for
  all three legs)
- **Three drone bodies**: GroundLifter, GroundAssembly, GroundSprayer
  (ground crew), plus the two still-old flying drones, **Spray and
  Winch** — genuinely no promoted source for any of these five.
  CargoLift and Assembly (the other two fliers) are corrected above;
  they are NOT blockouts.
- **The drone charging dock** dressing

**The old Scout v1 and Cargo build ladders** (`SpacecraftTestBay_v001`
— chassis / airframe-open / fitted / finished-craft forms, four
resolvers each for Scout and Cargo). The Scout's FINISHED form is
superseded today by the new six-part `Scout01_v002` model regardless;
what is newly a blockout here is the Scout's **mid-build WIP forms**
(chassis/airframe/fitted — the ship still uses a coarse placeholder
while under construction) and **the entire Cargo craft**, which has no
Design replacement of any kind yet.

**Site scenery made "with the meshy api"** (`SiteScenery_v001` — cargo
containers, light masts, fence panels on the player's own plot). Named
"our own stuff" in its own code comment, but the owner's original brief
for it explicitly said "with the meshy api" — Meshy-sourced regardless
of the friendly name, so it is included.

**Four pieces of the hall interior**: the stockpile rack, hall column,
gantry crane (old block-crane fallback, superseded already by the
commissioned portal), and dispatch door — all pre-existing Candidate
imports, in `ShipFactoryInterior_v001`.

## What was deliberately NOT touched, and why

- **`Scout01_v002`** — today's Claude Design six-part craft. Lives in
  a different pipeline entirely (`SpacecraftFactory_v001/Meshes/
  Scout01_v002/`), commissioned and verified today, not Meshy.
- **The hall shell** (walls, roof trusses, hanging lights) and **the
  gantry portal** (rails, portal, trolley, hoist) — both generated
  procedurally in Blender by this project (`Scripts/
  build_hall_interior_v001.py`, `Scripts/build_gantry_portal.py`), not
  commissioned from anyone. They share a folder with some blocked-out
  content (`ShipFactoryInterior_v001`, `Gantry_v002`) but load through
  their own separate lambdas, so they were excluded by function, not
  by a folder-wide sweep — a blanket path-prefix gate would have
  wrongly blocked out this project's own work.
- **The bought background kit** under `/Game/Meshes/` — district
  towers, hangars, pipes seen beyond the fence. A different, legitimate
  purchased source this file already keeps deliberately apart from the
  site's own art (background only, present-day industrial look, never
  on the player's own plot). Not Meshy.
- **Two flame/plume materials** (`SpacecraftPlumeMaterialPath`,
  `SpacecraftSoftFlameMaterialPath`) — left alone as a deliberate scope
  boundary. This pass covers meshes; these are materials tinting an
  already-blockout-capable flame cone, used at four scattered sites for
  a comparatively small visual effect. Flagged here rather than silently
  skipped, in case the answer is "these too."

## What this is not

**Not a claim that a Design replacement exists or is even commissioned
yet for any of the above.** Every line in "what is now blockouts" is a
gap to fill, not a status report on progress toward filling it. Priority
is the owner's call; the biggest single visual loss is almost certainly
the 27 core station machine bodies — the paint booth is now restored,
and two of the four flying drones ("co-stars" in this project's own
standing direction) are as well, so what remains hits the factory floor
itself hardest: every station body, the ground crew, and the two
still-old flying drones (Spray, Winch).

## Evidence

`LineBoss.Spacecraft`, 132 tests: 130 pass, 2 fail exactly as expected —
`RunwayPaintAndStrobesFollowTheRig` and `StationAccentsReflectRealState`
both assert behaviour that only exists **when a real mesh is present**,
which is now false everywhere on purpose. Both will pass again the
moment `bBlockoutMeshyContent` flips back to `false`; nothing else
should be weakened to make them pass sooner.
