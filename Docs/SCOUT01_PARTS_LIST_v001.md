# Scout-01 parts list — the model shopping list (v001, 2026-08-25)

Every physical item in the shipped Scout-01 production chain, extracted
from the live item catalogue (`LBSpacecraftInventoryAuthority.cpp`) and
crafting recipes (`LBSpacecraftCraftingAuthority.cpp`). One model each.
Sizes are PROVISIONAL carry/belt scale, not craft scale — a part must
read on a belt and under a drone at gameplay zoom.

> **THE MESHY LANE IN THIS DOCUMENT IS SUPERSEDED (2026-08-30).** This
> list was written when models were commissioned through Meshy (concept
> render → enhance → image-to-3D → intake). They are not any more:
> Meshy-sourced models are switched off in the game and stand as
> blockouts (`MESHY_BLOCKOUT_PUNCHLIST_v001.md`), and new models are
> commissioned through Claude Design.
>
> **The list of parts below is still correct** — it is extracted from
> the live catalogue, and what needs modelling has not changed. Only the
> *route* has. Any brief written from this list must carry the two rules
> the Scout commission proved necessary (`SCOUT_CRAFT_DESIGN_v001.md`):
> agree a **2D concept first**, and state dimensions as **measurements**
> plus how the **export must be structured**.

Style for all: clean futuristic industrial — pale panels, graphite,
brushed steel, blue-white indicators, warning-orange accents.

## Priority 1 — sub-parts (15): what drones visibly carry and fit

| Item | Made at | Used in | Size (m) | Meshy one-liner |
|---|---|---|---|---|
| Circuit Board | Circuit Fab | Electronics, Life-Support | 0.6×0.4 | sci-fi PCB tile, gold traces, blue status LEDs |
| Control Computer | Circuit Fab | Electronics comp. | 0.8×0.6 | avionics rack cube, front screen, heat fins |
| Wiring Loom | Electronics Stn | Electronics comp. | 0.7 coil | coiled cable harness on a spool, orange ties |
| Battery Cell | Power Cell Plant | Power comp. | 0.6×0.4 | cylindrical power cell, blue charge window |
| Power Regulator | Power Cell Plant | Power comp. | 0.6×0.5 | boxy converter, cooling ribs, gauge panel |
| Thruster Nozzle | Propulsion Stn | Propulsion comp. | 0.9 cone | machined titanium bell nozzle, orange rim |
| Combustion Chamber | Propulsion Stn | Propulsion comp. | 1.0×0.7 | steel chamber with injector dome and flanges |
| Fuel Pump | Propulsion Stn | Propulsion comp. | 0.5×0.5 | turbo-pump with volute and pipe stubs |
| Hull Section | Hull Fabricator | Hull comp. | 1.6×1.0 | curved hull skin panel on a carry frame |
| Canopy | Hull Fabricator | Hull comp. | 1.2×0.8 | tinted bubble canopy in a protective cradle |
| Landing Skid | Hull Fabricator | Hull comp. | 1.2×0.4 | sprung landing skid leg, wear pads |
| Nav Dish | Electronics Stn | Navigation comp. | 0.7 dish | small comms dish with gimbal base |
| Gyroscope | Electronics Stn | Navigation comp. | 0.5 sphere | gimballed gyro sphere in a mount ring |
| Seat Kit | Comp. Fabricator | Interior comp. | 1.0×0.8 | flight seat with harness, folded flat-pack |
| Life-Support Unit | Comp. Fabricator | Interior comp. | 0.9×0.7 | ECLSS box, filter drums, blue readout |

## Priority 2 — assembled components (6): pallet-scale, the big carries

Joined at the Sub-Assembly Robot; these are what the transport and winch
drones deliver to the assembly line. Each reads as a strapped pallet
assembly of its sub-parts.

| Item | Feeds stage | Size (m) | Meshy one-liner |
|---|---|---|---|
| Hull Component | Hull fit | 2.4×1.6 | palletized hull skin stack with canopy crate |
| Electronics Component | Systems fit | 1.4×1.0 | avionics crate, open top, racked boards |
| Power Component | Systems fit | 1.4×1.0 | battery bank pallet, cable bundles |
| Propulsion Component | Engine fit | 2.0×1.4 | engine assembly on a cradle, nozzle aft |
| Navigation Component | Systems fit | 1.2×1.0 | sensor cluster crate, dish folded |
| Interior Component | Outfitting | 1.8×1.2 | cabin kit pallet, seats and panels strapped |

## Priority 3 — processed stock (8): belt and store dressing

These flow on the conveyors between crafting stations. Simple readable
shapes; one model each, tinted per material.

| Item | Shape | Size (m) |
|---|---|---|
| Steel | ingot stack on skid | 1.0×0.7 |
| Titanium Alloy | ingot stack (darker, blue band) | 1.0×0.7 |
| Light Alloy | ingot stack (pale, orange band) | 1.0×0.7 |
| Copper Wire | wire coil drum | 0.8 drum |
| Composites | layered sheet bundle | 1.0×0.8 |
| Plate Stock | strapped plate stack | 1.4×1.0 |
| Frame Stock | strut/beam bundle | 1.6×0.5 |
| Fuel Mix | hazard-striped tank drum | 0.9 drum |

## Priority 4 — raw materials (6): shared container models

Raws arrive at the delivery dock and need only TWO shared models:
- **Ore crate** (open-top rugged crate, ore visible): Iron / Titanium /
  Copper ore, tinted per material.
- **Canister rack** (sealed drum rack): Silicon / Polymers / Chemicals,
  tinted per material.

## Count

15 sub-parts + 6 components + 8 stock + 2 shared containers =
**31 models** (moddable to fewer via shared bases where Meshy output
allows). Suggested order: Priority 1 first — they are what the fitting
drones hold under the craft, the most-watched objects in the game after
the ship itself.
