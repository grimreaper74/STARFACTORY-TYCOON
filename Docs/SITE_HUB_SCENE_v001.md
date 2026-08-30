# Site hub scene — drop v001, received 2026-08-29

The overview screen itself: one wide painted site the player clicks into,
replacing both the 3D map and the earlier plan to composite twelve
separate building sprites.

- Source: `SourceAssets/Spacecraft/SiteHubScene_v001/site_hub_scene_v001.png`
- 1672 x 941, RGB. Hash in `SHA256SUMS.txt` beside it.
- Commissioned against `Docs/SITE_HUB_BUILDING_ART_PROMPT_v001.md` plus
  the single-scene brief, with the twelve-building sheet attached as the
  style reference.

## What landed

All twelve buildings are present and laid out as a working plant, four
across the top, three through the middle, five along the bottom, linked
by roads and hardstanding with drones in flight and carts on the roads.
Two specific notes from the previous drop were taken:

- **The heavy ship factory is now distinguishable** from the standard
  hall — larger, taller, its own door treatment. On a screen where the
  player clicks buildings, two identical halls was a usability fault,
  and it is fixed.
- **The left fifth is open ground**, so the build panel covers no
  building.

## Three things to remove, all in one revision

**1. The spacecraft are not ours.** Owner: *"should take ships out as
there not our ships."* Three placeholder craft stand outside the two
assembly halls and on the launch pad. This game's whole pitch is that
the product is the star; showing someone else's ships on the front
screen is worse than showing none. The ground under them becomes clean
empty hardstanding — empty is correct, not a substitute craft.

**2. An interface frame is painted into the edges.** A blue
technological border with bracket shapes and glowing nodes runs along
the top edge and down the left. The game draws its own interface over
this picture; a painted frame fights it and locks the art to one screen
shape. The scene must run clean to all four edges.

**3. There is baked text.** A small glowing panel at top centre contains
lettering. This is the rule that most reliably makes art unusable — the
game ships translated and text baked into a texture cannot be localised
— and it was stated in the brief. Found by cropping and enlarging the
edges rather than by looking at the whole image, which is the only way
small lettering ever gets caught.
