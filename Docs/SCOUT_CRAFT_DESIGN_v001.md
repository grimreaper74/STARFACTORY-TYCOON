# Scout craft — design chosen, 2026-08-30

## The decision

**Option 3** of four concepts, taken as drawn. Sheet preserved at
`SourceAssets/Spacecraft/ScoutConcepts_v001/`, with the chosen band
cropped as `scout_option3_chosen_v001.png`. Hashes beside them.

Sleek nose, swept wings, prominent exposed engines with glowing
nozzles. Chosen against the game's needs rather than on looks:

- **The engines are clearly separate from the hull**, so the
  Propulsion build stage visibly adds something. On the more elegant
  Option 1 the engines are integrated and that stage would barely read.
- **The glowing nozzles carry the departure**, which is the moment the
  whole game builds toward.
- **The silhouette survives being small** on a near-isometric camera.
  Option 4's ring cowl was more distinctive and would have read as a
  blob at 300 px.
- **Broad flank panels take customer livery**, since every craft leaves
  in its buyer's colours.

## Why there was a concept step at all

Two 3D rounds were commissioned before this and both were wrong. The
second hit its triangle budget almost exactly (55,236 against a 45-65k
ask) — the modelling was not the problem. The **shape** was, and no
amount of added detail fixes a silhouette nobody agreed. The owner
called it: *"its just not right, think we should get a desighn from gpt
first?"*

## The two failures the modelling brief must carry

**Size was never checked.** The first 3D Scout measured **22.00 x 14.00
x 3.02 m** against a brief that said 12 m long — nearly double the
length, very broad and very flat. That matters beyond looks: gantry
rail span, station widths and booth clearances are all sized against
craft dimensions. State dimensions as measurements and verify them on
arrival.

**The six assemblies did not survive export.** The design tool showed
six named assemblies with a stage toggle, which is exactly right. The
exported GLB contained **1,741 loose objects** — `access_hatch.007`,
`array_element_cell.019` — with nothing in the names saying which
assembly each belonged to. The grouping existed only in the viewer.
The staged build is the game's signature, so the export structure is a
requirement, not a preference.
