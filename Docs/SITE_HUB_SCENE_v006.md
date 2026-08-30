# Site hub scene v006 — live, and sharp

`SourceAssets/Spacecraft/SiteHubScene_v006/site_hub_scene_v006.png`,
1672 x 941, imported as `/Game/LineBoss/UI/SiteHub/T_LB_SiteHub_v006`.
Hash in `SHA256SUMS.txt`.

## What changed

The same dimensions as v005 but **941 real scanlines instead of 470
stretched to 941**. v005 arrived with two frames stacked in one 16:9
canvas, which halved each one's height; this one is a single frame.
That was the whole of the request.

## But it is a different picture, and that matters

What came back was not the same frame re-exported — it is a **fresh
generation**, with the site sitting higher and further left. Every
hotspot moved. Reusing the v005 rectangles would have put the research
lab's click region on bare ground.

**A picture that is "the same but sharper" still has to be measured
again.** Verified the usual way: rectangles drawn back over the new
picture with the interface keep-out zones marked, so occlusion is seen
rather than assumed. The left quarter, top strip, top-right corner and
bottom strip are all clear of buildings.

## Getting the file at all

Two sends arrived as images with no file on disk, so they could be seen
but not imported. The third was found in `~/Downloads`, saved by hand.
It was identified by **opening it and comparing it to the picture in
the conversation**, not by its filename — the same rule the project
already applies to model drops.
