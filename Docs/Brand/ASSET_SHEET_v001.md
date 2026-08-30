<!-- COMMISSIONED ASSET SHEET, PRESERVED VERBATIM.
     Extracted 2026-08-29 from the owner's design-tool export.
     The artwork it describes is in Assets_v001/, with hashes
     and a usability assessment in MANIFEST_v001.md. Tool's own
     wording - do not edit it to match the code. -->

Asset sheet · 93 SVGs

 assets/icons · assets/patterns · assets/decals · assets/overlays

 The drawn set — icons, markings, decals, overlays

 Every file is pure black on transparent with a viewBox and no gradient, shadow or baked anti-aliasing, so tint in-engine from the palette tokens and export at any size. No letter, numeral or logo appears in any of the 93 files. Icons are shown inverted here because the art is black and the menu ground is not — the files themselves are black.

 01

 15 buildings — solid masses, 32 × 32, with 16px silhouettes

 Ship factory
 wide / vaulted / open bay

 Power plant
 square / stack / vent

 Storage warehouse
 wide / flat / roller gate

 Delivery dock
 L / flat / open bay

 Sub-assembly works
 wide / saw-tooth / door

 Foundry
 tall / stack / open bay

 Electronics shop
 square / flat / windows

 Propulsion shop
 wide / mast / vent

 Research lab
 round / dome / door

 Drone depot
 square / saw-tooth / open bay

 Maintenance shed
 tall / saw-tooth / roller gate

 Staff block
 tall / mast / windows

 Launch control
 square / mast / door

 Fuel store
 round / flat / vent

 Land office
 L / vaulted / windows

 Axis triples are printed under each icon: plan / roof / aperture. All 105 pairs were checked in generation and every pair differs on at least two axes — the rev B rule holds with no exceptions. Each mass also carries exactly one 2px panel-joint cut 2px below its roofline, which keeps interior detail at aperture + 1 cut, inside the 3-stroke budget.

 02

 10 stations — outlined chassis, variable head

 Gripper

 Nozzle

 Roller

 Press

 Welder arc

 Drill

 Scanner sweep

 Clamp

 Fork

 Hose

 Chassis is now a 2px outline — a stroked 26 × 4 base plate plus the 2px mast — so the mass-versus-outline split that separates the two menus in rev B 3A holds literally: no station file contains a filled shape. Only the head above y16 changes between the ten. The 16px silhouettes stay solid masses by definition.

 03

 14 livery markings — Tier A filled, Tier B outlined

 Solid 58° 

 Single stripe 80° 

 Double stripe 102° 

 Chevron 124° 

 Dashed spine 146° 

 Checker 168° 

 Half split 190° 

 Quartered 212° 

 Ring 234° 

 Cross band 256° 

 Dot trio 278° 

 Arrow 300° 

 Diagonal split 322° 

 Notch 344° 

 Each tile is 32 units = 2 × 2 m of dorsal panel ; set the UV scale from that. Shown white-on-livery for legibility — the files are black, so tint them to Hull.Marking.Light #ECEAE6 or Hull.Marking.Dark #23211F per rev B 1B. The anchor degree beside each name is the 1:1 pattern-to-hue mapping; since the pattern is the colour-blind channel it must never be swapped between customers.

 04

 Floor and runway decals — 1 unit = 10 mm

 Hazard striping
 200 × 200 mm tile · 100 mm band + 100 mm gap = 200 mm pitch · rotate 45° in the material

 Lane edge line
 100 × 1000 mm tile · continuous 100 mm line, tiles along its length

 Keep-clear hatching
 1000 × 1000 mm tile · 50 mm lines at 250 mm pitch · rotate 45° in the material

 Walkway edging
 250 × 1000 mm tile · 150 mm band, 50 mm gap, 50 mm line

 Survey grid, 20 m
 20 × 20 m tile · 100 mm lines on two edges · 600 mm stake pad · export ≥ 2048 px or bake into the ground material

 Runway centreline
 1.2 × 50 m tile · 30 m dash, 20 m gap

 Threshold bars
 24 × 9 m · eight 1.2 m bars at 2.7 m pitch · single asset, not tiled

 Chicane gate bars
 24 × 3.6 m · paired 1.2 m transverse bars, 1.2 m apart · single asset

 Hover pad ring
 20 m · 600 mm ring at 18 m dia + eight 1.2 m radial ticks · single asset

 05

 State overlays — 48 × 48, composited over a tile

 Too expensive
 bottom 12px band · 2px hatch at 8px pitch · tint Text.Dim

 Research-locked
 2px dashed keyline 4/4 + 10 × 8 shackle · tint Text.Disabled

 Refused
 2px keyline + 3px left marker · tint State.Refusal

 Tier pip · 1
 4 × 4 square, bottom-right cell

 Tier pip · 2
 two squares at 6px pitch, growing left

 Tier pip · 3
 three squares at 6px pitch

 Overlays are geometry only and carry no colour of their own. The gripper icon underneath is there only to show composition.

 WHERE THE SPEC WAS AMBIGUOUS — FIVE CHOICES, AND ONE THING THAT CANNOT BE DRAWN AS WRITTEN

 1. 45° decals are authored straight and rotated in the material. A true 45° tile at an exact 200 mm perpendicular pitch needs a tile edge of 200 × √2 = 283 mm, which is not a round world number and makes the UV scale unreadable. Both hazard striping and keep-clear hatching therefore ship as straight-line tiles at the exact stated pitch, with a 45° rotation in the material — rotation is free and the pitch stays exact. If you would rather have the rotation baked, say so and I will re-author at 283 mm tiles.

 2. Cut lines. Rev B said "solid masses with 2px cut lines" without a count or a position. Choice: exactly one horizontal cut, 2px tall, 2px below the roofline, inset 2px each side. It reads as a panel joint, keeps every icon inside the 3-stroke detail budget, and is identical across all fifteen so it never becomes an identifying feature.

 3. Round plan. Read as a cylinder in near-elevation — research lab takes the dome, fuel store the flat cap — because a literal circular footprint at 32px is a disc, and a disc reads as a button.

 4. Pattern tile size. Rev B never set one. Chosen: 2 × 2 m of dorsal panel per tile, so a 14 m Scout carries about seven tiles down its spine and a marking still resolves at the ~60px zoom the spec gives it.

 5. Pip position. Bottom-right cell, 4 × 4 squares at a 6px pitch growing leftward, so 1–3 pips never collide with the refusal left marker.

 What cannot be drawn as written: the 20 m survey grid's 100 mm painted lines. At any icon-like authoring size the line is sub-pixel, so the tile is authored at 2000 units and must be exported at 2048 px or larger — or baked into the ground material rather than used as a decal texture. At 512 px the line lands at 2.5 px and aliases into a dashed grey mess from the site camera. Everything else in the set is resolution-independent.

 These are constructed to the spec's grid, not artist-finished: every vertex is on the 4px subgrid and every stroke is 2px, which is what makes them consistent, but a pass for optical balance — a couple of the station heads and the saw-tooth roofs especially — will improve them. Tell me which ones read wrong at 24px and I will redraw those files.
