# Interface direction, v001 (2026-09-02)

The owner, after the packaged-frame audits and a first text-led redesign:
"the whole ui needs a lot of work to get peoples attention", then "its
just a wall of text, car manufacture is more pictures?", then "dont
accept everything i say, you know what works", then "have a look at a
few more games then its up to you". This is the direction I settled on,
and why.

## The references, and what each one is for

| Game | Take | Leave |
|---|---|---|
| Car Manufacture | Picture tiles for everything buildable; part pictures | Its cramped panels and dated chrome |
| Arms Trade Tycoon: Tanks | The product in the middle of the screen; contracts as a market with a visible success score | A cluttered UI, loading between screens, a shallow designer |
| Two Point Hospital | Everything readable at a glance; rooms identifiable at distance without garishness | Nothing in particular |
| Little Big Workshop | Warmth; a blueprint view that shows the work as a picture flow | Ambiguous linking labels |
| Production Line | Per-station stockpiles fed by deliveries (already ours) | Buttons "from the previous decade", right-click demolishing the line |
| Planet Coaster 2, Anno 1800 | Nothing new | Both were marked down for interface despite their budgets |

Reviewers punish the same things everywhere: cramped panels, unexplained
systems, loading between screens. So the rule is **fewer, bigger,
pictured elements, readable at a glance, the craft in the middle**.

## The rules

1. **Pictures first, words as captions.** Buildings, stations, parts,
   contracts and steps are picture tiles or cards. A number and a verb
   ride under the picture; a paragraph never does.
2. **The pictures come from the project's own meshes.** The presenter's
   tile studio renders each definition once, from one fixed
   three-quarter camera on a plain backdrop, into a cached render
   target. Art changes flow through automatically. No stock icons
   standing in for machines; no text baked into images.
3. **The chrome stays hue-free.** Colour belongs to the ships and the
   pictures (livery on ship thumbnails, amber trims and blue lights in
   the renders). `#EC3013` stays the only interface hue, for refusal.
   No accent colour on buttons - that offer was withdrawn.
4. **Bigger, fewer.** Two tiles per row in a 400 px panel, not four.
   Car Manufacture's density is the thing to avoid, not copy.
5. **The hero is the craft.** Entering the hall lands the camera on the
   line and the craft under the cranes, not on a 160 m box.
6. **Real buttons.** Accept, Order, Order the set, Remove: bordered chips
   with a verb, the one primary action per screen filled.
7. **State has a shape.** Working / waiting for the pulse / idle read as
   a bar and a chip before they read as words; done steps wear a tick.

## The mockup

`scratchpad/stranger/star_factory_hud_proposal.html` (published as an
artifact the same day): two screens over live frames, tiles and ship
cards, cut from real captures.

## Order of work

1. Tile studio and BUILD-tab tiles - **done 2026-09-02** (this commit).
2. The line as a filmstrip of station thumbnails with bars and chips;
   the same tags over the floor.
3. Contracts as ship cards with the customer, one big number, a
   parts-to-buy line and an Accept button; the six parts as picture
   tiles with "order the missing parts".
4. Top bar as labelled gauges (word, number, meter; speed as buttons).
5. Camera lands on the craft on entering the hall.
6. Kenney CC0 glyphs (in `SourceAssets/UI/Kenney`) for the few places a
   glyph beats a render: tabs, session, land.

Every step is judged on a rendered frame before it is called done.
