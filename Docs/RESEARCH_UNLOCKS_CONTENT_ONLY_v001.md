# Research unlocks CONTENT, never stat bonuses (v001, 2026-09-03)

## The rule

> A research node hands the player something that **exists to build or
> hire**. It never applies a multiplier to something they already own.

A node may open station families, bigger marks of them, storage, and
crew kinds. A node may **not** grant "+10% quality", "-15% cycle time",
"cheaper drones", or any other invisible modifier.

## Why this document exists

The rule was already being followed, but its only written trace was a
comment at the top of `LBSpacecraftResearchAuthority.h` asserting that
"the owner's plan is explicit about that" and citing
`Docs/SPACECRAFT_CONTENT_CATALOGUE_v001.md` — **a file that does not
exist in this repository**. No other document stated it.

That is thin provenance for a rule that shapes every future research
node, and on 2026-09-03 it nearly went the other way: a proposal to add
"faster cycle vs. better quality" trade-off nodes was drafted before the
header comment was noticed. The owner reviewed the question and kept the
rule. This document is that decision, written where it can be found.

## Why the rule is right, not merely inherited

**Content is self-documenting; modifiers are invisible.** When research
opens the ground sprayer, the player sees a new drone appear in the hire
menu, reads its quality weight, pays for it, and places it. When
research grants "+10% station quality", nothing on screen changes and
the player is asked to trust a number they cannot inspect. The second is
exactly the "multiplier applied behind their back" that the rule names.

**The constraint has not proved limiting.** The 2026-09-03 crew branch
is the test case. The obvious way to add crew progression was a quality
modifier; the content-only route instead gated the six specialist drone
kinds that already shipped (weights 0.6 to 1.7) and had been hireable
from the first minute, carrying no progression at all. The result is a
better feature than the modifier would have been — the player chooses
*who* works the station rather than watching a percentage rise — and it
was reached **because** the modifier was off the table.

**The benchmark agrees.** Production Line's research is largely content
too: new equipment and new fittable features. Its depth comes from what
the equipment enables and how the player arranges it, not from flat
percentages.

**Modifier trees are the lazy option.** They are quick to write and tend
toward "numbers go up" progression that is hard to balance and harder to
read. A content tree forces the harder, better question: *what new thing
should exist here?*

## What counts as content

| Allowed | Example |
|---|---|
| Station families | `RollingMill`, `PropulsionStation` |
| Bigger marks of a family | `AssemblyRobotMk2`, `SmelterMk2` |
| Storage and infrastructure marks | `StorageRackMk2` (2026-09-03) |
| Crew kinds | `Spray`, `GroundSprayer` |

The validator (`FLBSpacecraftResearchCatalogue::ValidateNodeTable`)
enforces the shape: every node must open at least one station class or
crew kind, each must exist in its catalogue, and none may re-lock
something that is free by default.

## The free floor, and why it cannot move

Some things can never sit behind research, because research points are
earned by **delivering craft** — gating what a delivery requires would
lock the game behind itself. The default set therefore keeps the five
slice families, the spray booth (no line commissions without one), the
delivery dock, the base storage rack, power, the halls, and the ship
factory.

Since 2026-09-03 the invariant is stated more precisely: **the base of
every infrastructure family is free; an optional bigger mark of it may
be researched.** `StorageRackMk2` is the first case — a player with a
working yard buying a larger one, which is a different situation from a
player with no yard at all.

## If this is ever revisited

The rule is the owner's to change. If it is relaxed, the thing to
preserve is the *reason*: whatever a node grants should be visible to
the player as a thing, not felt as a drift in numbers. A modifier that
is surfaced concretely (a named piece of equipment that does the
modifying, say) is much closer to the spirit of this rule than a bare
percentage attached to a node.
