# Site hub scene v004 — the parking apron, and one blocking defect

`SourceAssets/Spacecraft/SiteHubScene_v004/site_hub_scene_v004.png`,
1672 x 941, exactly 16:9. Hash in `SHA256SUMS.txt` beside it. Imported
as `/Game/LineBoss/UI/SiteHub/T_LB_SiteHub_v004`.

## What it fixed

- **The launch pad became a parking apron.** Finished craft fly out of
  the ship factory itself, so a launch facility was never right (owner:
  *"remember the ship flies out the building so want more of a parking
  lot than a launch pad"*). It is now marked bays on open hardstanding,
  with the blast apron, scorch staining and circular hazard ring
  removed. Bay markings are lines only — no numbers, because no artwork
  in this game may carry text.
- **The ground gained zoning** — darker working aprons, cleaner
  surfaces near research and operations — so buildings no longer float
  on one flat grey field.
- **The top-right corner is clear** of the objectives box.
- **Edges checked and clean.** Cropping and enlarging all four edges
  found no lettering, which is how the baked text in v001 was caught.

## Why it is NOT live

Recomposing to fill 16:9 filled the left edge. The **research lab is
entirely behind the build panel** and half the ship factory with it —
places the player cannot click at all. That is worse than an older
picture, so the live layout is held at v002 and the v004 rectangles
below wait for a recomposed picture.

`LineBoss.Spacecraft.SiteHub.EveryPlaceIsReachableAndUnambiguous` now
refuses this by name. It was written before this drop and failed on its
first run against it, which is the point: hotspots are numbers measured
off a picture, and every way they go wrong is otherwise something a
human has to spot by eye.

## The v004 rectangles, measured and verified

Read off the picture and checked by drawing them back over it. In
pixels of the 1672 x 941 artwork; the widget stores them normalised.

| # | Place | x0,y0 | x1,y1 |
|---|---|---|---|
| 1 | Ship factory | 200,245 | 475,445 |
| 2 | Parts factory | 585,265 | 885,460 |
| 3 | Power plant | 945,250 | 1220,460 |
| 4 | Receiving dock | 290,80 | 545,220 |
| 5 | Storage warehouse | 590,60 | 835,230 |
| 6 | Drone depot | 840,85 | 1035,235 |
| 7 | Parking apron | 1295,295 | 1625,545 |
| 8 | Research lab | 100,515 | 340,695 |
| 9 | Test hall | 395,475 | 645,665 |
| 10 | Operations | 610,575 | 795,765 |
| 11 | Materials refinery | 805,450 | 1015,715 |
| 12 | Heavy ship factory | 1055,485 | 1420,795 |

Swap the texture path and this table together when the recomposed
picture arrives, and re-measure — a recomposition moves everything.
