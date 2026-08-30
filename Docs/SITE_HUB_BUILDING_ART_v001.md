# Site hub building art — drop v001, received 2026-08-29

Commissioned from Claude Design against
`Docs/SITE_HUB_BUILDING_ART_PROMPT_v001.md`, delivered by the owner as a
single contact sheet. Preserved in the repo rather than left in an
uploads folder, per standing instruction.

- Source: `SourceAssets/Spacecraft/SiteHubBuildings_v001/site_hub_buildings_contact_sheet_v001.png`
- 1536 x 1024, RGBA, **background genuinely cut out** (47.8% of pixels
  fully transparent). What looks like a grey backdrop in a preview is
  the viewer compositing, not baked ground.
- Sliced into twelve separate assets by alpha connected-component
  labelling, not by eye — `T_LB_Hub_<Building>.png`. Hashes in
  `SHA256SUMS.txt` and `SHA256SUMS_slices.txt` beside them.

## Mapping

Twelve regions were found and fall in the brief's own order, three then
four then five across the sheet:

| Row | Left to right |
|---|---|
| 1 | Ship factory · Parts factory · Power plant |
| 2 | Receiving dock · Storage warehouse · Drone depot · Launch pad |
| 3 | Research lab · Test hall · Operations · Materials refinery · Heavy ship factory |

## What the drop gets right

Checked rather than admired: **no baked text, signage, numerals or fake
writing on any surface**, which is the rule that most often comes back
broken and would have made the set unusable in a translated game. No
stairs, handrails, walkways or person-sized doors; the vehicles read as
autonomous carts and the drones are present as scale anchors. One
consistent isometric angle and one light direction across all twelve, so
they composite as a single estate. The palette is the adopted one —
graphite structure, pale cladding, cool emissive trim — and the vivid
blue is legitimate under the governing rule, which permits hue in the
world precisely because the interface has none but refusal red.

## Two defects, one for art and one for code

**1. The heavy ship factory is the ship factory again.** Same
silhouette, same door, same gantry, same craft parked outside. The brief
asked for it to be unmistakably the largest thing on the site. There is
a real counter-argument — this project's own rule is that bigger *marks*
are bigger versions of one type rather than new designs, so one hall
drawn twice is arguably correct — but at a glance on a map the player
cannot tell them apart, and 220 m against 180 m is only a 1.2x
difference in footprint. Worth one variant pass: taller profile, twin
gantry, or a double-width end door.

**2. The set is not drawn to relative scale, and this is a code fix.**
Measured pixels per metre against the declared footprints:

| Building | Footprint | Pixels | px per metre |
|---|---|---|---|
| DroneDepot | 60 m | 280x212 | 4.67 |
| PowerPlant | 120 m | 500x324 | 4.17 |
| ReceivingDock | 80 m | 332x232 | 4.15 |
| StorageWarehouse | 100 m | 388x300 | 3.88 |
| TestHall | 100 m | 368x284 | 3.68 |
| ResearchLab | 80 m | 294x236 | 3.67 |
| PartsFactory | 120 m | 416x292 | 3.47 |
| OperationsBuilding | 60 m | 208x212 | 3.47 |
| LaunchPad | 120 m | 400x264 | 3.33 |
| MaterialsRefinery | 100 m | 316x328 | 3.16 |
| ShipFactory | 180 m | 532x380 | 2.96 |
| HeavyShipFactory | 220 m | 422x344 | 1.92 |

A 2.4x spread, and the worst case is the one that matters most: the
**heavy ship factory, the largest building in the game, is drawn at the
smallest scale of the twelve**. Dropped onto a map as delivered it would
be smaller than the power plant.

The fix belongs in the placer, not in a redraw. Each sprite is scaled to
a single common pixels-per-metre using its declared footprint, so the
map is dimensionally honest whatever size the artist happened to
compose at. Measured, not eyeballed.

## Superseded as a MAP source, kept as a building set

The owner corrected the approach on seeing these sliced up: *"I thought
it would just be a picture that you could click on."* The hub is one
painted scene of the whole site with clickable regions over it, not a
map assembled from these twelve. So the scale spread measured above
stops being a defect to work around — it never has to be reconciled,
because nothing gets composited.

These twelve remain worth keeping. They are the **style reference** the
site picture must match, and they suit anywhere a single building has to
appear on its own, such as a build-menu entry. The heavy-ship-factory
note still stands for the site picture: the two halls must be tellable
apart at a glance.
