# OneFactory weld vertical slice — running in the real map

Snapshot: **2026-08-16**. First observation of the Body/Weld line, and the whole
57-station route, running in `LB_MoorcrossWorks_OneFactory_v001` rather than in a
synthetic automation world.

## What was already true, and mis-stated

`CURRENT_GAMEPLAY_STATUS.md` (2026-08-12) records weld as *"Source candidate /
planned gameplay … No production Unreal station loop exists."* That is stale. On
the current source:

- `LineBoss.BodyWeld.*` and `LineBoss.OneFactory.*` are **53/53 green**,
  including `ActualPlayer.NativeUMGFull57StationQualityReworkLoop`.
- `ALBOneFactoryRuntimeCoordinator` already implements the full 57-position
  route, quality holds, rework, pause/fault and save/restore.
- The map opens clean with `LBOneFactoryGameMode` reporting
  `EXACTLY ONE PRODUCTION FLOW AUTHORITY AND ONE RUNTIME COORDINATOR READY`.

The genuine gap was narrower than the gate implies: all of that evidence came
from synthetic worlds, and nothing had ever driven the shipped builder through a
whole factory in the real map. `ALBOneFactoryGameMode::SeedsProductionStations()`
returns false and the bootstrap contract *requires* it to, so the map correctly
opens ready but empty and the coordinator refuses to run.

## What was added

`ULBOneFactoryDevFactory` ([`LBOneFactoryDevFactoryCommands.h`](../../Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.h))
drives the existing public API and adds no authority of its own:

| Command | Effect |
|---|---|
| `LB.OneFactory.BuildWholeFactory` | Creates and commissions Press, Body/Weld, Paint, Assembly, then audits the route |
| `LB.OneFactory.StartProduction [n]` | Creates and starts build orders |
| `LB.OneFactory.Run [iters] [step] [autoQA]` | Deterministic stepping of the whole line |
| `LB.OneFactory.BodyWeld` | The 18 weld positions, their duties and occupants |
| `LB.OneFactory.Status` | Route summary and per-unit progress |

Registered as console commands, not exec functions, so they behave identically
in the editor, in `-game`, and under `-ExecCmds` in an unattended run. Vehicle
model and paint programme are read from the committed layouts, so a reassigned
programme is honoured automatically.

## Result

Five orders staggered onto the line, deterministic stepping, no errors. Mid-run
the weld line held four cars at once, at four different stages:

```
09 OF_BODY_WELD_POS_03  BODY_PROGRAMME_02  CAIRNWELL_2040-000005  (BodyFraming)
14 OF_BODY_WELD_POS_08  BODY_PROGRAMME_07  CAIRNWELL_2040-000004  (BodyInWhite)
18 OF_BODY_WELD_POS_12  BODY_PROGRAMME_11  CAIRNWELL_2040-000003  (BodyInWhite)
23 OF_BODY_WELD_POS_17  BODY_PROGRAMME_16  CAIRNWELL_2040-000002  (BodyQualityInspection)
```

All five reached `Assembly/Dispatched` at 57/57 stations. Every quality gate held
and released for every car: five passes each at `OF_BODY_WELD_POS_16`,
`OF_PAINT_QUALITY_LIGHT_001`, `OF_ASSEMBLY_POS_23` and `OF_ASSEMBLY_POS_24`.

Route topology `OF_RUNTIME_TOPOLOGY_V001_C9F61F4B`, 57 stations, 18 Body/Weld.

## Status under the release vocabulary

This is **validation-only**, deliberately. It is a real map in a real game
session, which is stronger than the previous synthetic-world evidence, but it is
a `-game` run driven by developer console commands with `-NullRHI`. It is not a
packaged build, there is no player input journey, and nothing was rendered.

It does **not** claim: packaged playable, visual acceptance, HUD/UMG interaction,
performance, or that a player can reach any of this through the interface.

## Incidental fix

Adding one `.cpp` reshuffled the unity-build grouping and exposed a latent ODR
collision: `IsFiniteVector` was defined in an anonymous namespace in both
`LBCoilAGVController.cpp` and `LBCompactStillageFLT.cpp`. The former is renamed
`IsFiniteCoilAGVVector`. This was pre-existing and would have broken any future
file addition that landed those two in the same translation unit.

## Next

1. Drive the same sequence through the native UMG surface instead of console
   commands, so a player can build and run the factory from the interface.
2. Bind the WIP presentation layer so the cars are visible on the line, not only
   in the ledger.
3. Prove it in a packaged build, which is what the release gate actually needs.
4. Correct the weld and assembly rows in `CURRENT_GAMEPLAY_STATUS.md`.
