# The look, judged against the competition, and the plan (v001, 2026-09-02)

The owner, after a day of interface and line work: "ok its the look of the
game" and then "judge it against the other factory build games and suggest a
plan". This is the judgement, made on two frames captured the same hour
(`Saved/Audits/LineLook_2026_09_02/judgement_*.png`), and the plan that
follows from it. It is written to be disagreed with.

## The verdict in one line

The simulation is ahead of the picture. Put the entry frame beside a Car
Manufacture or Production Line screenshot and ours reads as a whiteboard
sketch of a factory: pale on pale, mostly empty, the ship a thumbnail.

## What the competition does that we do not

| | Car Manufacture | Production Line | Little Big Workshop | Ours today |
|---|---|---|---|---|
| Floor | Dark, with yellow lanes and bays painted on | Flat coloured tiles per zone | Warm wood and paint | Pale concrete, faint grid, nothing painted on it |
| Machines | Warm saturated housings, tall, arms that move | Distinct colour per machine type | Chunky, characterful, readable at distance | A flat dark slab with four small blocks; no silhouette since the portals went |
| Product | Cars in colour, big in frame, visibly built up | Cars in colour on a coloured line | The work in hand is the picture | A pale craft, smaller than a pallet, mostly out of frame |
| Frame fill | Walls, racks, lights, signage, robots, workers | Every tile means something | Dense, warm, alive | Roughly four fifths of the frame is bare floor |
| Lighting | Strong warm key, deep contact shadows | Flat but saturated | Warm, soft, coloured bounce | Overexposed, cool, low contrast; everything the same value |
| Motion | Arms welding, sparks, cars rolling | Belts moving, vehicles arriving | Workers walking, tools moving | Crane trips and drone sorties exist but are hard to see |

Every reviewer of every one of those games mentions the same things: readable
at a glance, warm, busy. Ours is none of the three yet, and that is the gap
to close before anything is filmed.

## What is wrong, in the order it hurts

1. **No value contrast.** Floor, station, pallet, hull section, hall wall:
   all within a narrow band of pale grey. The eye has nowhere to land. This
   is the single biggest fault and the cheapest to fix.
2. **No colour.** The palette adoption put the hue in the machinery and the
   ships; neither carries any yet. The amber trims and blue indicators are
   too small to register; the craft is graphite or a white livery.
3. **The station has no presence.** With the portal gone it is a circuit
   board on the floor. The decision to drop the portal stands (the drones
   fit, the cranes move), but a station needs a silhouette: tool towers on
   the flanks, a raised cradle under the craft.
4. **The hero does not read.** The craft is the smallest thing at its own
   station and the camera lands too far away. Car Manufacture puts the car
   in the middle third of the screen.
5. **Empty metres.** The hall interior is far bigger than the line; the
   camera framing shows the emptiness. Walls, columns, racks, lights and
   floor markings are absent from the entry frame.
6. **Scale confusion.** A pallet of hull tube is bigger than the station's
   tools. Stock should be crates and racked sections at a size that sits
   under the machine, not beside it as a rival.

## The plan

Six phases, each judged on a rendered frame side by side with a reference
screenshot before it is called done, each committed with its frame under
`Saved/Audits/LineLook_*`. Phases A and B are the whole game visually; the
rest is compounding.

**A. Contrast and warmth (first, and cheapest).** Floor to the graphite
end of the world spec with hazard lanes and bay outlines painted on; station
pads in Structure.Graphite with the working/idle strip wide enough to read;
exposure down, key light warmer, contact shadows on. Crates in Crate.Tan.
One evening of material parameters and a lighting pass. Codex can do the
parameter plumbing from a written spec; the judgement is done on the frame.

**B. Colour where the palette allows it.** The primer coat verified in a
strong livery (yellow is accepted in the live session); machine housings
pale with amber arm segments and edge strips at a width that registers at
the player's zoom; blue work lights on drones and stations that actually
light something. Ships and machines carry the hue, the interface stays
hue-free.

**C. Station presence.** A station is a machine, not a slab: two tool towers
on the flanks (the drone docks already sit there), a raised cradle the craft
sits in, a tool gantry low over the work. Blockout first, in the world spec
colours, then commission the model through the concept-then-3D route the
owner set.

**D. The hero.** Camera lands closer on entry (the line's bounds are framed
today; frame the nearest occupied station instead), the craft sits raised on
its cradle, its parts visibly arrive (the drone sortie carries the actual
part mesh rather than a crate, and the fitted part appears on the hull).

**E. Fill the frame.** Hall walls and columns visible in the entry frame,
ceiling lights in rows, racks along the walls, painted walkways, drone
traffic between dock and line. Either shrink the interior to the line or
frame the line so the hall's edges are on screen.

**F. Motion, then film.** Crane trips, sortie flights, sparks and light
flashes at the fitting point, the departure. The owner is the only one who
sees the game move, so his frame-with-a-note reports are the gate here.

## Phase A, first pass (same day)

The HDR visualiser found the real fault under "no value contrast": the map
locks exposure at EV100 0.0 while the lit scene averages EV100 4.45, so
every surface sat four stops over and even a dark floor clipped to white
(`phaseA_hdr_readout_before.png`). The player camera now locks exposure at
the scene's level (linear multiplier 21, read back as EV 4.4 -
`phaseA_hdr_readout_after.png`), the interior slab and zones drop to a dark
concrete with the traffic lanes painted pale, and the sun casts contact
shadows. Frames: `phaseA_entry_exposure_locked.png`,
`phaseA_station1_exposure_locked.png`. The floor reads as concrete with
texture, the stations and hazard edges stand off it, hull sections read pale
on mid, shadows have depth. Still cool-blue overall: the plan's "warmer key"
is deliberately NOT done yet - the palette adoption rejected a warm sun on
measured grounds (it pushes every albedo toward the amber arc). A mild warm
sun is the next frame to judge, against that evidence.

**Second pass, same day.** The floor sample had not moved when the slab
tone changed because the site's outdoor paving tiles stand proud of the
hall's slab; the hall now lifts the 468 tiles under its footprint and its
own floor shows. That first read as a void (82/82/83), so the tone came up a
step and a 10 m lane grid is painted on it (`phaseA_entry_lane_grid.png`,
`phaseA_station1_lane_grid.png`, floor now 95/96/99). Phase A stops here:
contrast and scale are on the floor; warmth is still short, and that is
now a phase B question of what carries colour rather than a lighting one.

## Phase B, first item (same day)

The primer coat verified in a strong livery: a Coastal Rescue craft on
station 5 in muted pink from the first station
(`phaseB_primer_coat_pink_livery_station5.png`). Amber and blue: the tool
tower below carries the amber cap and arm and the blue strip at a width
that registers at the player's zoom.

## Phase C, blockout (same day)

One TOOL TOWER per station on the far flank - pale housing, amber cap, a
blue strip facing the work, an amber arm low over it. The first blockout
put a tower on both flanks and the near one stood between the camera and
the craft (`phaseC_first_blockout_near_tower_hid_craft.png`); far flank
only now (`phaseC_empty_line_tower_blockout.png`). Four models commissioned
through the Meshy API from these proportions
(`SourceAssets/Candidate/Spacecraft/StationDress_v010`, 80 credits: tower,
wall rack, ceiling light bar, low tool cabinet) - previews only until
their renders are judged and their size imposed at export.

## Phase D, first pass (same day)

Entering the hall lands on the first OCCUPIED station, expanded 9 m for
its tower and crew, instead of the whole line's bounds
(`phaseCD_hero_framing_tower_blockout.png`: the craft on its rams in the
middle third of the free picture, the tower behind it). The sortie now
carries the station's actual part mesh at a third of its size rather
than a crate; not yet seen on a frame.

## What not to do

- Do not chase asset count. One good station model beats six variants.
- Do not add hue to the interface to make the game "more colourful".
- Do not switch the camera to orthographic or change the FOV; every framing
  formula assumes 48.
- Do not re-add the portal frame to give the station a silhouette; give it
  the silhouette some other way.

## Evidence

- `Saved/Audits/LineLook_2026_09_02/judgement_entry_frame.png`
- `Saved/Audits/LineLook_2026_09_02/judgement_station1_frame.png`
- `Saved/Audits/UITiles_2026_09_02/contracts_cards_livery.png`
