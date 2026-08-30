# Autonomous night, 2026-08-26 into 2026-08-27 — v001

Greg handed over an overnight run: *"set a goal to keep working on the game
to get it finished, use blockouts for any models you dont have till we get
them, use research or anything at your disposal."*

This is what happened, what it is worth, and what it is **not** proof of.

## The disk was full - it was Codex, and it is fixed

`C:` had **0.27 GB free** of 2 TB, falling to 0.00 during the night. That
was not a nuisance, it was the cause of what looked like flaky tests:
Unreal could not write `Intermediate/CachedAssetRegistry`, and several
suite runs failed on a different unrelated test each time with an I/O
error that, read properly, said "there is not enough space on the disk".

The culprit was `~\.codexrchived_sessions`: **313 archived Codex chat
transcripts totalling 672.8 GB**, averaging 2 GB each, the largest a
single 8 GB conversation. One folder held a third of the drive - more
than three times the entire game project. For scale, the whole of
`Projects\` is 287 GB, this project's `Builds\` 90 GB and its
`SourceAssets\` 60 GB.

Greg cleared it on 2026-08-27 and free space went **0.16 GB to 673.1 GB**.
With room to work the suite runs clean: **78 passed, 0 failed, 0
warnings** against a freshly built binary
(`Saved/Automation/SpacecraftCleanDisk_v001`). That closes the one honest
gap the night ended on, where the final commit had to report 77/1 with
the 1 being the disk rather than a code fault.

During the night I cleared only my own scratch (0.98 GB across two
passes) and deleted nothing of Greg's.

## How the work was chosen

Rather than guess, the game was audited against its own early-access scope by
six independent read-only passes — money loop, contracts and reputation,
logistics, progression, runtime appearance, and whether a player can actually
play it with mouse and keyboard. Every claimed gap that mattered was then
handed to a separate adversarial pass told to **refute** it against the
source. That second pass earned its keep: it threw out a claim that the loop
has no running costs, showing with citations that materials, power and the
starter plant are all genuinely paid for.

What survived was a short list of things that were really broken, several of
which three separate auditors found independently.

## Fixed tonight

**A failed craft would have deadlocked the line forever.** The hover test
could never fail — the coordinator called it with a hard-coded pass — so the
defect penalty already sitting in the settlement code was unreachable. Had a
failure ever been recorded, nothing could clear it and the craft would have
sat at the gate permanently. Workmanship is now earned: a craft collects
defects from the crew that worked it (nominal is two drones, a lone drone
rushes a fit, an empty station bodges both), the hover test judges that load,
and a failure opens rework **in the same act**, so the deadlock cannot exist
by construction. The craft is delivered late and 10% cheaper.

**Buying a third drone made the game unsaveable.** The drone snapshot
validator capped the drone index at 1 — a relic of when every station carried
exactly two. Line stations have held eight slots for days, so the moment a
player bought a third drone anywhere, quick-save refused the entire save with
no warning. The cap now comes from the catalogue.

**Accepting a Cargo contract was a silent softlock.** The line took the
oldest accepted contract and stopped there. The craft-size law rightly refuses
a 21 m Cargo hull on Mk1 stations, but with no cancel and no expiry, every
later contract queued behind it forever and all income ended. The line now
skips what it cannot build and gets on with what it can; the law is untouched.

**Research could not be earned.** Points had two sources, both dev-only, so
the entire tree — six crafting families, the Mk2 marks, and with them the
second craft tier — was content the player could see priced and never afford.
Delivering craft now banks points on the value delivered. A Scout teaches
exactly Basic Fabrication, so the first delivery opens the chain.

**A craft cost nothing to build.** Marginal cost was zero and margin was
100%, because component allocation defaulted to empty and consumption is
fail-open on an empty allocation. Commissioning now fits out the line, so a
craft costs the six components it is made of. A full imported set is 13,050 cr
against a 50,000 cr Scout — so buying your way through the first contract is
affordable, fabricating is cheaper, and make-vs-buy becomes the decision the
29-recipe chain exists for.

**An idle factory earned money.** The starter plant exported its full cap
into an empty floor from the first frame, paying 200 cr a sim-minute to leave
the game running. Generators throttle to load now: a working factory still
sells its surplus, an idle one sells nothing.

**The packaged build never reached this game.** GameDefaultMap still pointed
at the car-era factory. It now opens the spacecraft map, and the bay-paint
decal materials — loaded by path at runtime, so nothing referenced them — are
in the cook set.

**The missing floor markings are explained.** They were never invisible: they
were rendering underneath the line-station pad, a slab that sits exactly where
the paint projects and refused decals. This supersedes my earlier claim that
the materials were at fault, which was wrong and which I had already
disproved with a probe.

**Shadows.** Station meshes, structural blocks, drone bodies and the craft's
fittings all had cast-shadow switched off, so nothing in the factory cast
anything. They cast now; emissive and translucent parts deliberately do not.

**A reputation was worth nothing.** It was a flat two points for any
contract — a Scout and a Cargo built your name equally — and a tier bought
nothing except permission to click the Cargo button. Both halves now scale
with value delivered, and customers pay a trusted builder 5% a tier above the
first, fixed when the contract is taken. A Scout still earns exactly the two
points it always did, so nothing regresses.

**A stalled machine stopped in silence.** Build a crafting machine with no
storage rack and it fills its six-item buffer and stops forever — haulers
exist only per rack — while reporting "awaiting drone pickup", a pickup that
could never come. And nobody read it: the refusal went into a local and was
dropped. Refusals raised by the *running* factory now reach the player's
toast, repeats suppressed, and the message names the cure ("BUILD A STORAGE
RACK") instead of promising a hauler.

**Supporting work.** A `LB.Spacecraft.Install` console command (moving
machines indoors had left the dev journey with no way to reach one); one
shared ledger-credit path, because the console journey had quietly stopped
crediting the same things the game does; the HUD now shows reputation and
workmanship, and the Contracts tab shows the contracts you actually hold —
so none of the above is invisible; `LB.Spacecraft.Status` prints cash; and
the dev showcase stocks its own component crate.

## What the evidence covers

Every change above landed with the `LineBoss.Spacecraft` suite green against a
binary built in the same command — **74 tests, 0 failures** at the end of the
night, 77 by the end — plus headless `-game` journeys that confirm the
behaviours in the
actual game rather than only in rigs. Reports are under `Saved/Automation/`.

Two runs hit a transient I/O error writing `Intermediate/CachedAssetRegistry`
on unrelated tests; neither reproduced. Twice a suite reported green off a
**stale binary** after a compile failure — both are called out in the commits
that superseded them, because a green run off an old binary is not evidence.

**This is validation-only.** No packaged build was produced or played
tonight. No visual claim here has been confirmed by eye: shadows and floor
markings are code changes that an automation suite cannot see. One rendered
capture was taken; it looked at bare floor, for the reason below.

## The economy was soaked, not just unit-tested

Thirteen commits of economy change deserve a system check. A long
headless journey ran five Scouts across two contracts, buying its
component sets on the open market:

| | cash (cr) | revenue | research | reputation |
|---|---|---|---|---|
| line built | 485,000 | 0 | 0 | 0 |
| 36 components bought | 406,700 | 0 | 0 | 0 |
| 3 delivered | 556,786 | 150,000 | 30 | 6 |
| 5 delivered | 656,841 | 250,000 | 50 | **tier 2** |

Everything reconciles: cash tracks revenue minus the real component
spend, research pays exactly ten a Scout, reputation pays two, and tier
2 arrives on the fifth delivery as the thresholds say it should. No
stalls, no alerts raised, no runaway. `LB.Spacecraft.Status` now prints
cash, which is how this was read.

The player still gets richer every delivery, which is correct for a
factory game and is a tuning question, not a broken one - the numbers
are yours to set.

## What needs Greg

- **Eyeball the visuals.** Shadows, the floor markings now that they are out
  from under the pad, and whether the factory reads as more than greybox.
- **Economy tuning.** Research pacing, the rework time, the defect tolerance
  and the component prices are all marked PROVISIONAL and are mine, not yours.
- **The dev showcase is not framed.** The player's boot framing is fine -
  it centres the starter spine at (-6800, -1500) with a 65 m arm - but
  -LineBossAutoShow builds its canonical line 68 m away at x=0, so a
  capture taken with the showcase looks at empty floor. That is why the one
  render taken tonight showed nothing useful: a capture problem, not a
  player-facing one.
- ~~Free some disk~~ - done, see the top.
- **The offer board is in but shallow.** Three standing offers with varied
  quantity and price, gated by reputation. Deadlines were deliberately not
  started: an expiring contract would strand a finished craft with nothing
  to settle against, which needs a "built to stock" path first - a new
  stall, and removing stalls is what most of tonight went on.
- **Logistics is the biggest piece still standing**, and it is your stated
  early-access feature: storage racks register stores nothing ever reads,
  and the whole item economy runs through one hard-coded floor store. The
  heavy drone hauling dock to storage to stations is the shape you
  described; it is a real feature, not a fix, and wants your input first.
