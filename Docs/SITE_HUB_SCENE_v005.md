# Site hub scene v005 — live

`SourceAssets/Spacecraft/SiteHubScene_v005/`, imported as
`/Game/LineBoss/UI/SiteHub/T_LB_SiteHub_v005`. This is the picture the
game shows. Hashes in `SHA256SUMS.txt`.

## What it fixed

The left quarter, the top strip and the top-right corner are now clear
of buildings, so nothing hides behind the build panel or the objectives
box. That was the defect that held v004 back: the research lab was
drawn **entirely** behind the panel and half the ship factory with it.
It also keeps everything v004 got right — the parking apron instead of
a launch pad, and real tonal zoning in the ground.

## The delivery was squashed, and that was recoverable

Both versions arrived packed into one 16:9 canvas, one above the other,
making each half 1672 x 470 — a 3.55:1 strip. The buildings in it
looked wrong, and the reason was arithmetic rather than art: two 16:9
frames stacked and then resized to 16:9 leaves each **squashed to half
height**. Doubling each half's height restores the true geometry, which
is what `site_hub_scene_v005.png` is.

**Cost of that: the live picture carries 470 real scanlines stretched
to 941.** It holds up at the sizes tested and is much better than the
alternative, but it is soft against a 1080p screen, so it is worth
asking for the two frames as separate full-size files rather than
stacked. Nothing about the composition needs to change.

## Hotspots

Measured on the recovered image and verified by drawing the rectangles
back over it **with the interface keep-out zones drawn as well**, so
occlusion is seen rather than assumed. The table lives in
`ULBSpacecraftSiteHubWidget::Places()` and is checked by
`LineBoss.Spacecraft.SiteHub.EveryPlaceIsReachableAndUnambiguous`.

The two zones the test enforces are the ones that actually bit: the
build panel down the left, and the objectives box top-right. A place
drawn entirely under either is unclickable, and that is invisible in
the artwork — it only appears with the interface over the picture.
