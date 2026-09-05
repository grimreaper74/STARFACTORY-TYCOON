# The transporter pass: heavy drones that carry, charge and are seen doing it

**Date:** 2026-09-02, evening. **Status:** validation-only (PIE frames and
the indexed suite; no fresh packaged journey). **Owner direction:** "car
manufacturer has men constantly carrying parts to the line and stock
areas, think they're called transporters, we have the heavy drones that's
supposed to do that", then "perfect, but ours will go to their dock and
charge", then "ok do it".

## What was wrong

Car Manufacture's floor reads busy because its transporters never stop.
Ours had the plumbing - the drone fleet authority runs haul jobs between a
rack or dock and a station, and the presenter mirrors those flights - but
four things made the traffic invisible or wrong:

1. **Four items per trip.** With six components per ship a hauler flew
   about twice per station per ship and was parked the rest of the time.
2. **The delivery was animated backwards.** Both legs were named for the
   collect job: the drone flew out empty, flew home "loaded", and the part
   landed in the station's store when the drone was back at its rack.
3. **Idle haulers vanished.** Between jobs the body was hidden ("the crew
   visuals cover it" - a rack has no crew).
4. **A straight line at 5.6 m** from rack to station, through whatever
   stood between, with a plain tan cube as the load.

And the haulers never charged, unlike every crew drone.

## What changed

**Sim (`LBSpacecraftDroneFleetAuthority`)**

- `HaulLoadFor(Category, Capacity)`: an ASSEMBLED COMPONENT goes one per
  trip. Raw stock, processed stock and sub-parts still ride in crates of
  up to the capacity, so the fabrication chain keeps the pace its
  integration tests were tuned to (sub-parts feed the fabricator cells,
  not the line - see the owner's line-length decision the same evening).
- A delivery has three legs when the goods are not at home: `ToSource`
  (empty, home to the dock or rack that holds them), `ToMachine` (loaded),
  `ToStore` (empty, home). The drop - re-clamped against the shelf as it
  is now, transferred source to shelf in one call - happens on ARRIVAL at
  the station (`SpacecraftHaulDropDelivery`). Goods still move only at the
  drop, so a save taken mid-flight loses nothing. `SourceStationId`
  records which station the goods came from so the picture can fly there.
- `HaulIsLoaded(Haul)`: the one rule for when the hook carries (delivery
  out, collection home), shared with the presenter.
- Urgent first: pass 0 of the want scan serves shelves below one cycle's
  need, pass 1 the top-ups. With one part per trip the old scan filled the
  first shelf's first item to target before the head station's kit was
  complete.
- The battery: `Charge01`/`bCharging` on the haul state, the crews'
  numbers (180 s flight per charge, 60 s to refill, reserve 0.15, launch
  at 0.9). A run in progress always finishes; a hauler under reserve sits
  on its pad until fit to launch; charging connects a `HaulCharge.<rack>`
  grid load through the power authority when one is present (both game
  mode tick paths pass it) and charges freely in a rig without a grid.

**Presenter (`LBSpacecraftWIPPresentationActor`, sub-assembly logistics
tick)**

- A pad beside every rack and dock (status disc, the charging-dock model
  when it loads); it pulses in the working blue while the fleet says the
  hauler is charging and sits in the idle tone otherwise.
- The hauler sits on its pad when idle. Every leg lifts to a 5.2 m lane,
  cruises, and settles; a delivery lands at a line station's kit dolly on
  the far flank, at a machine's buffer spot off its +X end.
- The load is the real component mesh when one exists (the six line
  components do), a crate otherwise, and only while `HaulIsLoaded`.
- Every hauler cache is a `UPROPERTY` now (the packaged GC purge lesson).

## Evidence

- Suite `LineBoss.Spacecraft`: 141 of 141 Success, indexed at
  `Saved/Automation/Haulers1_2026_09_02/index.json`, including the two new
  tests `Drones.ADeliveryDropsWhereTheHaulerIsAndBigPartsGoOneAtATime`
  (own-store two-leg delivery, dock-sourced three-leg delivery, the drop
  on arrival, the load rule, the loaded-hook rule) and
  `Drones.AHaulerChargesBetweenTripsAndKeepsHauling` (900 s of endless
  demand: deliveries before the first charge, a charging episode, the
  battery floor near the reserve, deliveries after).
- PIE frames (`Saved/Audits/Transporters_2026_09_02/`), dev line plus a
  console-placed dock, parts ordered through the real Contracts tab:
  `hero_hull_lift.png` - the cargo drone lifting the hull nose pallet off
  its pad beside the dock, the pad's charging-dock model under it, the
  dock's two crew docks alongside; `r18_2_zoom.png` / `r18_5_zoom.png` -
  the drone at lane height over the pad with its shadow on the floor
  (outbound and return); `r9_1_zoom.png` - the first proven flight, over
  the dock roof at the old framing; `r16_pan.png` - the pad's side of the
  dock. `run6.log` - the first ship of the run fed entirely by
  one-part-per-trip hauls: station shelves filling and emptying in order,
  the dock draining, the craft dispatched and credited.
- The hauler's world position was read from the live PIE presenter
  through the editor's Python (the dev toolset's capture cannot project
  world points): pad (-2000,-380) -> lane height 520 -> the head station's
  dolly at (490,-4000) -> back, four seconds a leg, exactly the fleet's
  phases.

## Not proven

- A close-up of the DROP at a station's kit dolly with the pallet under
  the drone: the head-station capture window missed the flights (they had
  finished), and the cruise frames show the drone but not the pallet
  clearly enough to call it proven on the loaded leg away from the pad.

- No packaged build of this pass yet.
- Throughput with one component per trip on a full five-station line over
  many ships (the integration tests cover the fabrication chain, and the
  runtime coordinator's stranded-craft deadline test still passes, but no
  long PIE soak was run tonight).
- Purchased cargo-lift crew drones do not add haulers; a hauler comes with
  each rack or dock, which is the lever for now.
