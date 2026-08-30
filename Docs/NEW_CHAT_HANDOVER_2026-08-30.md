# New chat handover — 2026-08-30

Where the project stands at the end of a long day's work, what is
trustworthy, and what is not. Read `CLAUDE.md` first for the standing
rules; this covers only what changed today and what a new session needs
to know before touching anything.

## The one-line state

The core loop is proven end-to-end and packaged. **Most of the factory's
machinery is deliberately grey blockouts** pending replacement art, so
the game currently looks *less* finished than it did yesterday — that is
an intentional decision made today, not a regression.

## What happened today, in order

1. **Site hub picture went sharp** (v006). It arrived as a *fresh
   generation* rather than a re-export, so every hotspot moved and had
   to be re-measured. Lesson recorded: a picture asked for as "the same
   but sharper" is a new picture until measured.
2. **The Scout craft was commissioned and landed** — five rounds. Two 3D
   attempts failed before anyone had agreed a shape; a 2D concept sheet
   then settled it in one attempt. Final model: six named assemblies,
   12.00 x 7.00 x 2.54 m, 119,890 triangles, imported and wired in.
3. **Meshy content was switched off** at the owner's instruction, to
   stand as blockouts until Claude Design replaces it.
4. **That switch was then corrected** — it wrongly caught five things
   that were never Meshy. See the warning below.
5. **Docs index brought up to date.**

## READ THIS BEFORE TOUCHING ASSET CLASSIFICATION

The blockout switch (`bBlockoutMeshyContent`, currently `true`, in
`LBSpacecraftWIPPresentationActor.cpp`) originally classified assets by
their Unreal content path — anything under `Candidates/Spacecraft/` was
treated as Meshy.

**That was wrong.** `Candidates/` is this project's word for *"not yet
promoted"*, not for *"came from Meshy"*. Finished, vetted work sits in
the same folder as raw intake. The owner caught it within the hour: a
paint booth he had already had made correctly the day before was showing
as a blockout.

The corrected signal is **whether a promoted source exists at
`SourceAssets/Spacecraft/<Folder>`**, as opposed to only
`SourceAssets/Candidate/Spacecraft/<Name>_MeshyIntake_v001`. Five things
were wrongly gated and are now excluded: the paint booth, the two
already-remade drones (CargoLift, Assembly), the lift cradle, and the
five parts carriers.

A near-miss is recorded in the same commit: `Components_v001` in the
promoted tree *looked* like a match for the six per-component fitting
props by name, and is not — it uses an unrelated `LB_Part_*` convention
the game never loads. Checked before shipping, not after.

## The packaged builds — IMPORTANT

- `Builds/StarFactoryTycoon_v008` — packaged **10:17**, before the gate
  correction at **10:39**. It therefore contains the KNOWN-WRONG
  blockout, with the booth and drones wrongly greyed. Do not use it to
  judge how the game looks.
- `Builds/StarFactoryTycoon_v009` — packaged after the correction.
  Use this one.

## Test state, honestly

`LineBoss.Spacecraft`: **132 tests, 130 pass, 2 fail.**

The two failures are **expected and correct**:
`RunwayPaintAndStrobesFollowTheRig` and
`StationAccentsReflectRealState` both assert behaviour that only exists
*when a real mesh is present*, which is now false everywhere on purpose.
They will pass again the moment the blockout flag flips back. **Do not
weaken either test to make them green** — they are doing their job.

## What is a blockout right now

`Docs/MESHY_BLOCKOUT_PUNCHLIST_v001.md` is the authoritative list, built
from what the code actually gates rather than from memory. In summary:
the 27 core station machine bodies, three ground drones, two still-old
flying drones (Spray, Winch), landing gear, both craft canopies, the six
per-component fitting props, the old Scout/Cargo build ladders, some
site scenery, and four hall interior pieces.

**Not blocked out** (verified): the new Scout, the paint booth, the two
remade drones, the lift cradle, the parts carriers, this project's own
procedural work (hall shell, gantry portal), and the bought background
kit under `/Game/Meshes/`.

## One correction to an earlier priority claim

Earlier in the session I said the station machine bodies were the
biggest visual loss. That overstated it. **The line stations the player
actually watches during a build are procedural blocks, not loaded
meshes** — marked squares, hazard bands, dock pads — so the gate never
touched them. The 27 gated station bodies belong to the parts factory,
which is behind a two-delivery unlock, so a reviewer's first ten minutes
never sees them. The drone fleet is the higher priority.

## Where models come from now

Claude Design, not Meshy. Every brief must carry the two rules the Scout
commission proved necessary (`Docs/SCOUT_CRAFT_DESIGN_v001.md`):

1. **Agree a 2D concept first.** Two 3D rounds were wasted adding detail
   to a silhouette nobody had approved.
2. **State dimensions as measurements, and state how the export must be
   structured.** A model promised as six named assemblies arrived as
   1,741 loose objects; the grouping existed only in the design tool's
   viewer.

Useful tooling written today, all in `Scripts/`:
`render_craft_views_v001.py` (renders any GLB from three angles and
prints its part list and measured extents),
`inspect_mesh_health_v001.py`, `check_symmetry_span_v001.py`,
`inspect_blend_v001.py`. A drop can be measured and judged in about a
minute rather than eyeballed.

## What is blocked on the owner

- **Audio.** Roughly eight sounds. The game is silent apart from a
  placeholder rotor loop. This is the one plan item that has never moved
  and cannot move without him.
- **Replacement art** for the punch-list, commissioned through Claude
  Design. Next up: the five remaining drones (Spray, Winch, and the
  three ground drones), matching the two already delivered.

## Not started

**Onboarding.** Nothing exists. A stranger cannot currently work out
what to do without the reviewer notes. This is the last big item that
needs no input from the owner.

## A pattern worth knowing about

Three times today I stated something confidently about *where* something
was or *what* it was, without checking, and was wrong: the folder-name
classification above; a report of "16 broken index links" that was
really a check run in the wrong checkout (the worktree holds the
branch's docs, the main checkout does not); and overwriting a fresh edit
by copying between the two checkouts in the wrong direction.

All three were caught, but the pattern is the same. **Verify location
and existence before acting on them**, and push back when a confident
claim about what exists has not been checked.
