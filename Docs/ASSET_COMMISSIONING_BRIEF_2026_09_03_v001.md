# Asset commissioning brief (v001, 2026-09-03)

Written the night before an 8,000-credit Meshy top-up, to answer one
question: **what should those credits actually buy?**

## The headline: do not start by spending

The factory's art is far more complete than "blockouts everywhere"
suggests. **1,045 `.uasset` files under `Content/LineBoss`** plus 45
under `Content/Spacecraft`; roughly **74 mesh keys registered, ~60 of
them resolving to a real, always-cooked asset.**

Already done, and not to be re-commissioned: the 7 drone crews, the 5
parts carriers, the 20 kit-dolly pallet loads, the 4 station-dress
props, the 3 track pieces, the 6-part Scout-01, the Cargo-01 v002 hull
and its 6 cargo parts, the paint booth, the lift cradle, the kit dolly
v003, the site kit, the runway furniture, and 67 UI icons.

The biggest immediate wins are not purchases. They are **wiring faults
hiding art that is already paid for.**

## 1. Free wins — art exists, code hides it

**(a) Mk2 crafting stations drew as grey cubes. FIXED 2026-09-03.**
The four *line* families passed the promotion gate with `StartsWith`,
so their Mk2s inherited approval. The nine *crafting* families tested
for an exact name, so `RollingMillMk2`, `SmelterMk2`, `CircuitFabMk2`,
`ElectronicsStationMk2`, `PowerCellPlantMk2`, `PropulsionStationMk2`,
`SubAssemblyRobotMk2`, `StructureFabMk2` and `FitOutFabMk2` all failed
it and drew as blocks — with their Mk1's approved mesh sitting unused.
Nothing about a bigger mark makes its art less promoted. Now `StartsWith`
on all of them.

**(b) Ten keys with real assets on disk are still blocked.**
`SubAssemblyHall` (`SM_LB_ST_SubAssemblyHall_v003` exists),
`Canopy.Scout`, `Canopy.Cargo`, `Gear.Leg`, and all six `Component.*`
meshes render as engine cubes because they are absent from the
promoted-source allowlist. **This one needs the owner's call, not a
code fix:** the blockout switch encodes the 2026-08-30 decision to keep
Meshy-era content off screen until Design replaces it
(`Docs/MESHY_BLOCKOUT_PUNCHLIST_v001.md`). If those assets are the ones
that decision was about, they stay blocked and get *replaced* — which
is a legitimate use of credits. If they are not, they are free wins.

**(c) A registration-order bug.** The `DroneBatch_v001` loop re-adds
`Drone.CargoLift.Body`, `Drone.Assembly.Body` and
`Drone.GroundLifter.Body` *after* the ConceptDress block registered
them to the TRELLIS joined props; `TMap::Add` overwrites, so the later
registration silently wins. Same class as the documented
`charging_dock_v001` bug. Worth confirming which mesh is actually
wanted before spending anything on drones.

## 2. What the camera actually sees

Measured, not guessed. Camera is fixed: **pitch −35°, FOV 48**, no
pitch control, so *every object is seen from one angle forever and its
top surfaces are always the largest visible face.*

Player zoom clamps to **2,500–16,000 cm**; the game's own framings
converge on **5,900–7,700 cm**, and the boot framing is 6,500 cm. That
band is where the player lives. At 6,500 cm the scale is **0.332 px/cm**
(1920 wide):

| Object | On screen at 6,500 cm |
|---|---|
| Station pad Mk1 (1800×1400) | 597 × 266 px |
| Station pad Mk2 (2700×2100) | 896 × 400 px |
| Spray booth | 862 × 342 px |
| Cargo-01 hull (21 m) | 697 × 213 px |
| Scout hull (14 m) | 464 × 133 px |
| Storage rack Mk1 | 199 × 190 px |
| Drone (~3 m) | 100 × 57 px |
| Kit dolly bay | 113 × 51 px |
| Kit crate | 35 × 20 px |
| Charge pad | 46 × 27 px (flat — a decal in practice) |

**The detail gate that falls out of this:** 1 cm of geometry is ⅓ of a
pixel. A surface feature needs ~15 cm of relief to read as a 5-px mark;
a 5 cm bolt is 4 px even at maximum zoom-in. **Silhouette and large
form are everything; panel lines, fasteners and greebles are wasted
spend.** Brief for bold shapes and strong top surfaces.

## 3. Where credits genuinely belong

Three things are pure blockout with **no mesh path at all** — meaning
they need code as well as a model, and they are the largest untouched
things on screen:

1. **The line station work-station square** — ~36 cubes per station, on
   screen at every station for the entire game, 597×266 px each. The
   single biggest visual return available.
2. **The conveyor / track belt** — ~45–110 cubes per belt plus a cube
   spline track. The file's own comments call the line "the picture's
   spine", and it is currently the darkest, plainest thing in frame.
3. **The launch-tube runway** — ~78–108 cubes. This is the payoff shot
   of the whole loop.

Second tier: the **tool tower** and **kit dolly** (mesh paths exist but
do not resolve in some builds — check before buying), and the **hall
floor paint** (~62 cubes that should be decals or a floor texture, not
geometry — a material job, not a model job).

## 4. Process, per the owner's own rules

- **Concept before 3D.** Two 3D rounds were wasted in August iterating
  a shape nobody had agreed. Every item above gets a 2D concept pass
  and an owner pick before any refine credit is spent.
- **Geometry from Meshy, materials in Unreal.** Standing direction.
- **Don't chase the count.** Replace what a camera lands on. By the
  table above, anything under ~50 px at play distance is not worth a
  model.

## Suggested order for tomorrow

1. Settle the §1(b) question — are those ten blocked keys the ones the
   blockout decision was about? That answer alone may unlock a
   screenful of finished art for nothing.
2. Look at a frame with the Mk2 gate fix in, to see what the factory
   actually looks like now before deciding it needs anything.
3. Concept passes for the three §3 items, owner picks, then refine and
   import only the picks.
