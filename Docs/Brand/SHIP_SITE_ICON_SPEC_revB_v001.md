<!-- COMMISSIONED BRAND SPEC, PRESERVED VERBATIM.
     Extracted from the owner's design-tool export on 2026-08-29.
     The source zip keeps ONE filename and has already been
     overwritten three times, so the only durable copy is this one.
     This is the AUTHORITY for colour, layout and motion; it
     supersedes the 'brand is OPEN' note in CLAUDE.md. Text is the
     tool's own wording - do not edit it to fit the code; if the
     code disagrees, the code is what changes, or the disagreement
     goes back to the next revision as an amendment. -->

Implementation spec · rev B

 Liveries · outdoor site · icons

 Ships, the site, and an icon set with no colour

 All values are sRGB albedo unless marked emissive; HSV is given because the governing rule is written in it. Three places where this document amends rev A rather than working around it are collected at the end — read those before transcribing.

 01

 Ship liveries — a 27-slot wheel

 1A · THE WHEEL — 14 HUE ANCHORS × 2 TIERS, MINUS ONE = 27 SLOTS

 TIER A — DEEP · S 84–92% · V 74–82% · 14 SLOTS

 CANONICAL S 88 / V 78

 58°
C7C118
 80°
8DC718
 102°
4CC718
 124°
18C724
 146°
18C764
 168°
18C7A4
 190°
18AAC7
 212°
186AC7
 234°
182AC7
 256°
4718C7
 278°
8718C7
 300°
C718C7
 322°
C71887
 344°
C71847

 TIER B — BRIGHT · S 72–80% · V 88–96% · 13 SLOTS

 CANONICAL S 76 / V 92

 58°
VOID
 80°
AFEB38
 102°
6EEB38
 124°
38EB44
 146°
38EB86
 168°
38EBC7
 190°
38CDEB
 212°
388CEB
 234°
384AEB
 256°
6838EB
 278°
A938EB
 300°
EB38EB
 322°
EB38A9
 344°
EB3868

 STEP 22° between anchors, starting at 58°. Two arcs of the wheel are reserved for the factory and are illegal for liveries: 0–20° (Indicator.Fault and State.Refusal live at 9°) and 26–56° (Machine.Amber 33°, Crate.Tan 35°, Hazard 46°). The two reserved arcs are 21° and 31° wide, leaving 308° of usable wheel; the 14 anchors span 58°–344° (286°), leaving 22° of headroom against the reserved arcs. 

 THE VOID SLOT Anchor 58° exists in Tier A only. Its Tier B value (#EBE538) sits 12° from Hazard.Yellow at higher V and S, and a bright yellow-green hull crossing hazard striping loses its edge. Dropping it gives exactly 27 slots for 27 customers, with no spare — slot 28 onward extends the wheel to 11° half-steps (see growth rule below). 

 BAND FLOOR Never below S 72% or V 74%. What fails: at S < 72 a hull enters Crate.Tan / Machine.Amber chroma territory and at bay zoom reads as a machine part rather than a product; at V < 74 a deep livery collapses into Structure.Graphite wherever the hull is in its own shadow, and the ship disappears against the gantry it is standing in. 

 BAND CEILING S 92%, V 96%. Above that you are on the sRGB gamut edge and the launch bloom clips to white, which costs you the customer's colour in the one shot that sells the game. 

 ASSIGNMENT Customer → slot is a fixed data table, authored once, never randomised — returning players must recognise a customer by colour. Slot = (anchor index, tier). 

 SEPARATION This is what keeps two ships on one floor tellable apart, and it belongs to the contract offer generator , not the palette: concurrently active contracts must differ by ≥ 2 anchor steps (44°) , or by tier if they share an anchor. Re-roll offers that violate it. Cap 6 painted ships on the floor at once — beyond that, 44° of separation stops being enough at 30px. 

 GROWTH Past 27 customers, insert 11° half-steps (69°, 91°, …) rather than widening the bands or relaxing the reserved arcs. The bands are load-bearing; the step size is not. 

 1B · A LIVERY IS A SCHEME OF THREE, DERIVED

 BASE
≈75% The customer's slot colour, exactly. Top surfaces and the upper hull. 

 ACCENT
≈20% Same hue, opposite tier. Tier A base → accent is the Tier B value of that anchor; Tier B base → accent is the Tier A value. So the pair states the hue twice at two lightnesses, which is what survives shadow, bloom and 30px. Nose cap, engine housing, fin faces, spine stripe. 

 MARKING
≈5% Hue-free, one of two: Hull.Marking.Light #ECEAE6 or Hull.Marking.Dark #23211F . Pick by base value: V ≥ 85 takes dark, V < 85 takes light. Geometry only — stripes, chevrons, panel outlines. No numerals, no letters, no logos, ever, per the localisation rule. 

 FORBIDDEN A second hue anywhere on the hull. Two hues per ship halves the distinguishable set and destroys the 44° separation rule — the accent must never be a different colour, only a different tier. 

 SLOT 212°A
BASE 186AC7 · ACCENT 388CEB · MARK ECEAE6

 1C · BARE HULL — AND WHY IT IS COOL, NOT PALE

 Hull.Bare #8C9196 — 206° · 8% · 59%. Unpainted structure for the first half of the line.

 Hull.Bare.Dark #6A6F74 — 206° · 9% · 46%. Recesses, ribs, exposed frames, thruster bells.

 Two separations from Machine.Housing.Pale #D6D2CB (38° · 5% · 84%), and both are required:
 Value — 59 vs 84, a 25-point gap. Temperature — cool 206° vs warm 38°. Machinery is warm and light; product is cool and mid.

 Third cue, material: bare hull roughness 0.30–0.38 with a visible anisotropic mill direction; machine housing roughness 0.55–0.65, flat. From a fixed overhead camera the specular sweep across a bare hull is the fastest read that it is a ship.

 What fails if crossed: a warm or above-V70 bare hull reads as a machine housing, so on a busy line the player cannot tell how far along each of four hulls is — the core legibility failure of the genre.

 1D · SURVIVING 30 PIXELS — WHERE THE COLOUR GOES

 TOP-DOWN BUDGET The camera only ever sees the top. ≥ 60% of the projected top-down silhouette area must be Base. Flanks and underside may be anything legal; they are never seen at site zoom. 

 CONTIGUITY Base must present one unbroken patch of ≥ 12 × 12 px at 30px ship length — i.e. a dorsal panel at least 40% of hull length by 60% of hull width. Scattered painted panels totalling the same area do not pass; the eye needs one field. 

 ACCENT One spine stripe along the centreline, ≥ 8% of top area and ≥ 2px wide at 30px. Two-tone at distance is the tier cue. 

 MARKING Resolves above ~60px only, and never carries information — it is the customer's flavour, and its pattern is the colour-blind fallback (below). 

 TWO HULLS Scout 14 m and Cargo 21 m use the same percentages, not the same absolute panels, so a Scout is never under-painted. Re-check the 12 × 12 px rule per hull: at site zoom a Scout is ~30px and a Cargo ~45px. 

 CVD FALLBACK Each of the 14 anchors owns one hue-free marking pattern — solid, single stripe, double stripe, chevron, dashed spine, checker, half-split, quartered, ring, cross-band, dot trio, arrow, diagonal split, notch — drawn in the marking colour. Tier A uses the filled variant, Tier B the outlined one. Roughly 8% of your male players cannot use the wheel alone, and the pattern is also what identifies a customer in a screenshot. 

 WHAT FAILS Colour on flanks and fins only: from a fixed overhead camera every ship reads Hull.Bare gray at site zoom, the liveries only exist in cutscenes, and the entire saturation discipline buys you nothing. 

 1E · SHOWING A LIVERY IN A HUE-FREE PANEL

 CONTRACTS

 Halvorsen Freight

 18,400

 Kestrel Survey

 9,250

 Tallow Orbital

 31,900

 THE CHIP 12 × 12 px, 1px Panel.Rule #363433 keyline, split 135° with Base above and Accent below. Zero radius. Never larger, never a background, never behind text. 

 WHY THIS IS LEGAL 1g governs interface colour. The chip is not interface colour, it is a sample of a ship — the same relationship as a thumbnail. It is bounded: total livery-chip area ≤ 0.15% of screen, one chip per row, max two per card, chips only ever in contract lists, the ship inspector and the launch summary. 

 HARD LIMITS Livery colour may not tint row text, row background, borders, buttons, progress bars, icons or the minimap. Minimum 8px clear space from any State.Refusal element — a red chip 2px from a red banner makes the banner look like a livery and the refusal stops reading as a refusal. 

 SECOND CHANNEL The chip carries the customer's marking pattern as a 1px overlay at ≥ 16px chip size (inspector, launch summary). At 12px the pattern is dropped and the customer name carries it — the name is localised text, never baked. 

 02

 The outdoor site — 600 × 600 m

 TOKEN
 HEX
 HSV
 USE

 Ground.Prepared
 #C2BDB4
 40° · 8% · 76%
 Graded, compacted hardstand inside the claimed plot. Sits 0 points from Floor.Concrete in hue, 3 below in value, so interior and exterior read as one material family.

 Land.Unclaimed
 #9C9585
 44° · 15% · 61%
 Native ground beyond the built area. 15-point value drop from prepared ground is the boundary read from high altitude — the claimed rectangle must be obvious with no fence.

 Road.Apron
 #B6B2AB
 37° · 6% · 71%
 Roads, delivery aprons, dock forecourts. Distinguished from prepared ground by edge kerbs, not by tone.

 Runway.Surface
 #ADA9A3
 36° · 6% · 68%
 Runway and chicane. Slightly darker and cooler than the apron so the strip reads as a continuous band from the highest zoom.

 Runway.Marking
 #E8E5DF
 40° · 4% · 91%
 Centreline, thresholds, chicane gates, pad ring. The brightest non-emissive surface in the game — the runway is legible by value, never by hue. ΔV vs surface = 23; below 20 the strip vanishes at site zoom.

 Runway.Marking.Worn
 #CFCAC2
 36° · 6% · 81%
 Scuffed sections in the touchdown and chicane zones. Never applied to the centreline or the pad ring — those must stay at full value.

 Pad.Surface
 #4E5154
 206° · 7% · 33%
 Hover pad deck — Structure.Graphite family, so the pad reads as engineered equipment rather than ground. A dark deck is also the best backdrop a bright hull can hover over.

 Site.Kerb
 #8E8A84
 36° · 7% · 56%
 Kerbs, plot edging, drainage channels, survey stakes. The line-work that makes empty ground read as prepared.

 2B · PREPARED, NOT UNFINISHED

 Emptiness reads as capacity only if the ground is already organised. Every claimed plot ships with, at minimum: a 0.15 m kerb line at the plot boundary; a painted layout grid at 20 m pitch in Site.Kerb tone, 0.1 m wide; survey stakes at every grid intersection; a drainage channel down each 20 m lane; and one capped utility stub per 20 × 20 m cell.

 Forbidden on prepared ground: rubble, spoil heaps, construction cones, scaffolding, tarps, potholes, weeds. Those say abandoned . Weeds and scrub live outside the kerb line only, and are the main texture difference between Land.Unclaimed and Ground.Prepared.

 What fails: with no painted grid, a 600 × 600 m plot with two buildings on it reads as an unfinished level rather than a business at day one — and the grid is also how the player learns where things can go before they own a placement tool.

 2C · THE RUNWAY, AND THE ONE LIGHTING EXCEPTION

 GEOMETRY 24 m wide, 6 m shoulders in Ground.Prepared. Centreline dashes 30 m on 20 m gaps, 1.2 m wide. Threshold bars at both ends. Chicane gates marked by paired 1.2 m transverse bars; apex kerbs in Hazard striping at the fixed 200 mm pitch. Drama comes from geometry and speed, not from colour. 

 EXCEPTION Granted, bounded. Edge and approach lighting and pad strobes are emissive and allowed one hue: Indicator.Working #BFE4FF for steady fixtures, #FFFFFF for strobes. Same blue-white as the RCS plume, so ship and pad read as one event. 

 BOUNDS Each fixture ≤ 0.05 m² emissive area; total emissive ≤ 0.6% of frame at bay zoom; ground spill radius ≤ 1.5 m at ≤ 20% intensity; fixtures dim to 30% when no launch is sequenced. No red and no green anywhere on the pad — red is Fault, and aviation-convention greens would introduce a second world hue. 

 IF CROSSED Coloured wash on the deck, or emissive above ~1% of frame, makes the pad the most saturated region in the shot — and the departing ship stops being the subject at the exact second the game is trying to sell itself. 

 2D · LIGHT — FIXED DAYLIGHT, HIGH OVERCAST

 Daylight, and fixed — no cycle. Four reasons, in order of weight:

 1. The interior direction is already "a modern assembly hall with the lights on". A dusk or night site contradicts the building it surrounds.

 2. Dusk pushes every neutral warm-orange, which lands the whole world in Machine.Amber's hue arc and breaks the saturation test globally — you would have to re-tune the interior tokens to keep it.

 3. A hue-free UI needs a stable ground. With a day cycle, panel contrast against the floor changes hour to hour and the acceptance test only passes at certain times.

 4. It answers your real question: in daylight, emissive trim is decoration, not identity. Buildings must be recognisable by silhouette and value — which is also what the icon set relies on, so one decision serves both. If you ever want the night look, ship it as a photo-mode option, not as gameplay light.

 SUN Elevation 62°, azimuth fixed at 135° screen-relative, so shadows always fall down-right and shadow length ≈ 0.5 × object height. Never overhead — a 90° sun kills the silhouette read from above. 

 SKY FILL Sky.Ambient #DDE3E8 (205° · 8% · 91%), cool, against warm ground bounce from Ground.Prepared. That cool/warm pair is what keeps a pale hull separable from pale ground. 

 SHADOW FLOOR Deepest shadow no darker than 28% of lit value. Anything deeper and a Tier A hull in shadow drops under the V 74 floor, which is the failure the band exists to prevent. 

 EXPOSURE Locked. No auto-exposure, no eye adaptation — both would move UI contrast and invalidate the chroma test frame to frame. 

 EMISSIVE TRIM ≤ 0.08 m² per 10 m² of façade, Indicator family only, and never a building's primary identifier. A building recognised only by its glow is unrecognisable in daylight at site zoom. 

 03

 Icons — no colour, no letters, 25 things to tell apart

 THE CANVAS

 32 × 32 AUTHORED, SHOWN AT 8× · 4PX SUBGRID
2PX KEYLINE MARGIN (DASHED) · 28 × 28 LIVE AREA
EXAMPLE: SAW-TOOTH ROOF + WIDE PLAN = A WORKS BUILDING

 3A · SILHOUETTE SYSTEM

 GRID & STROKE Authored on 32 × 32 with a 2px keyline margin; every vertex snaps to the 4px subgrid. Stroke 2px at 32px (0.0625 × size), one weight only, square caps, zero corner radius. Four exports, each with a job: 16px = silhouette-only variant (minimap, compact list), 24px = detailed, build menu default , 32px = detailed, hovered tile and station picker , 48px = detailed, tooltip and inspector header . No other sizes ship. 

 MINIMUM SIZE 20px for the detailed icon. Below 20px only the 16px silhouette-only variant is used (solid mass, interior detail deleted) — hand-authored, never an auto-downscale of the detailed art. Interior detail: max 3 strokes ; a fourth is illegible at 24px and reads as noise at 20px. 

 CLASS SPLIT Buildings are solid masses with 2px cut lines. Stations are 2px outlines with open interiors. That single rule separates the two menus with no colour and no label — mass is a place, outline is a mechanism. 

 15 BUILDINGS Three axes: plan shape (square / wide rectangle / tall rectangle / L / round), roof profile (flat / saw-tooth / vaulted / stacked / stack-and-chimney), one aperture motif (door / roller gate / open bay / mast / vent). Rule: any two building icons must differ on ≥ 2 of the 3 axes . 5 × 5 × 5 gives ample room for 15 with that margin. 

 10 STATIONS Shared chassis, variable head: every station icon carries the same 28 × 6px base plate and 2px vertical mast, and differs only in the tool head — gripper, nozzle, roller, press, welder arc, drill, scanner sweep, clamp, fork, hose. Family first, identity second; the head occupies the top 14px and gets the full 3-stroke detail budget. 

 ACCEPTANCE Two tests, both cheap. Blur test: Gaussian at 25% of icon size — every icon must still be uniquely identifiable within its class. 8px test: downsample to 8px; the plan shape (buildings) or the head silhouette (stations) must still resolve. Failing either means redraw, not recolour. 

 NO TEXT — INCLUDING No letters, numerals, roman numerals, unit glyphs (kW, m³), currency marks or logos in any icon or texture. Where a count or tier is genuinely needed, draw 1–3 pip squares (4 × 4px, bottom-right cell) — geometry, not type. Tooltips and the panel carry all wording, in localised text. 

 3B · STATE WITHOUT HUE — EVERY STATE USES AT LEAST TWO CHANNELS

 BUILDABLE
Text.Body · 100%

 HOVER / FOCUS
Row.Hover + ring

 ARMED
Inverted on Positive

 TOO EXPENSIVE
Text.Dim + hatch band

 RESEARCH-LOCKED
Disabled + dashed + shackle

 REFUSED
Red keyline + marker

 TWO-CHANNEL RULE Every state above is signalled by at least two of {icon value, tile fill, keyline style, hatch, inversion}. None is colour-only, which is the only way this works for the ~8% of male players with CVD and the only way it works at 20px. 

 EXPENSIVE ≠ LOCKED Too expensive is a bottom hatch band (temporary, money-shaped); research-locked is a dashed tile keyline plus shackle (structural). Different geometry, so the player never confuses "come back with credits" and "come back after research". 

 REFUSED The only red in the menu, and only after the player tried . 2px State.Refusal keyline plus the 3px left marker; the glyph returns to full Text.Body so it stays readable. Never a red-filled icon — a red-filled 24px tile reads as a livery chip. Words live in the refusal banner, per rev A §2. 

 TILE METRICS 32 × 32 icon in a 48 × 48 tile, 4px gutter, 8px grid pitch. Icon never touches the tile keyline — the 2px margin is what lets the keyline carry state. 

 THREE PLACES THIS AMENDS REV A — DECIDE THESE BEFORE TRANSCRIBING

 1. The acceptance test needs a carve-out for hazard striping. Hazard.Yellow is S 86%, higher than any livery (ceiling S 92% but canonical 76–88%), so "the most saturated pixel in frame belongs to a hull" fails wherever a hull is parked next to striping. Amend the test to: excluding emissive fixtures and hazard striping, non-ship pixels above 60% saturation stay under 8% of frame and the most saturated pixel belongs to a hull. The alternative — pushing every livery above S 88% — would delete the bright tier and halve your customer set.

 2. Pad and approach lighting is a real exception to "no world surface may be both bright and saturated." It is granted deliberately and bounded in 2C (footprint, spill, dimming, no red or green). Emissive point sources at ≤ 0.6% of frame cannot win the chroma-area test, and the launch is the one moment worth an exception.

 3. The livery chip puts hue in a hue-free interface. Consistent with 1g's intent — colour belongs to the ships — but it is a literal exception, so it is bounded in 1E: 12 × 12px, ≤ 0.15% of screen area, contract lists / inspector / launch summary only, never behind or on text, and 8px minimum clear space from anything red.
