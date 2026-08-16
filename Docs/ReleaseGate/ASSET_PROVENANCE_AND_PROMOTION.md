# Asset provenance and promotion

## Promotion states

| State | Required meaning |
|---|---|
| **Authority preserved** | Original download/generation is immutable, hashed and linked to source/rights evidence. |
| **Source candidate** | Editable derivative/export exists and passes source-level dimensional/topology checks. |
| **Unreal candidate** | Imported below `/Game/LineBoss/Candidates`; import success alone is not approval. |
| **Runtime selected** | Gameplay code/Blueprint references the exact asset and uses authored collision, pivots, LOD/material masks and sockets. |
| **Packaged verified** | The exact runtime asset is visually, functionally and performance-checked in a named package. Only this state supports a “finished” claim. |

Folder names such as `Approved`, `Production`, `Final` or `Runtime` do not bypass
these states.

## Current high-value families

| Family | Current state | Evidence / blocker |
|---|---|---|
| Press-shop hero machinery and press train | Unreal/runtime candidates; latest integration **validation-only** | Numerous candidate imports and station authorities exist. Current package proof predates the latest press/stillage work. |
| Powered conveyor modular kit v001 | **Source candidate** | [README](../../SourceAssets/Candidate/FactoryLogistics/PoweredConveyor_v001/README.md) and manifest record source round-trip PASS, lightweight modules and `NOT_IMPORTED__ROOT_CLEARANCE_REQUIRED`. |
| Compact forklift AGV v003 | **Source candidate**; runtime uses a procedural fallback | [README](../../SourceAssets/Candidate/Logistics/CompactForkliftAGV/README.md) defines mast movers. [`LBCompactStillageFLT.cpp`](../../Source/LineBossCarFactory/LBCompactStillageFLT.cpp) currently builds cube/cylinder fallback visuals. The repaired live MCP gate passed all four FLT tests and the exact physical handoff; indexed and packaged proof remains open. |
| Finished-panel stillage v004 | **Source candidate** | [README](../../SourceAssets/Candidate/PressShop/FinishedPanelStillage/README.md) records modular guides and an unresolved 1901.737 x 1075.198 x 1388.613 mm source-versus-3000 x 1400 x 1800 mm concept dimension gate. |
| Cairnwell 2040 WIP panels | **Source candidate** | [README](../../SourceAssets/Candidate/Vehicles/Cairnwell2040/PanelRuntime_v001/README.md) explicitly says no Unreal package/promotion. Bumpers must not become press recipes. |
| MIG robot v001 | **High-poly source review only** | [README](../../SourceAssets/Candidate/WeldShop/MIGRobot_v001/README.md): J4 locked; about 1.52M triangles; retopology, flange and collision gates remain. |
| Spot-weld robot v001 | **Source reference / planned derivative** | [README](../../SourceAssets/Candidate/WeldShop/SpotRobot_v001/README.md): fused J2 shoulder; reuse the corrected shared arm and optimize only the C-gun head. |
| ED tank, oven and combined line | Source authorities plus imported **blockout Unreal candidates** | [Tank](../../SourceAssets/Candidate/PaintShop/EDTreatmentTank/README.md), [oven](../../SourceAssets/Candidate/PaintShop/EDCuringOven/README.md), and [combined line](../../SourceAssets/Candidate/PaintShop/EDLineAssembly/README.md) all require modular production work. The combined source is a validated 135 m blockout, not a finished mesh. |
| Cleaning/maintenance AMRs | Unreal/runtime candidates; packaged presence only | V1029 proves four docked actors/telemetry, not every task, beacon, work light, collision, LOD or service loop. |
| Factory Environment Collection | Curated support kit | [Vendor audit](../VENDOR_ASSET_AUDIT_2026-08-01.md) limits it to background/support geometry. Attach purchase/EULA evidence to the release archive. |
| RayB2 vehicle pack | Provenance-only CC0 evaluation | [Source and licence record](../../SourceAssets/ThirdParty/CC0/OpenGameArt_RayB2_Vehicles_2019/SOURCE_AND_LICENSE.md); inclusion does not mean promotion. |

## Private Meshy generations and rights record

The user has confirmed that the Meshy generations are **private**. Record that
fact in each family manifest, but do not infer or state that a paid tier was used.
Before any Meshy-derived asset ships, retain:

- generation/project/task ID and date;
- immutable original file and SHA-256;
- prompt and every reference input;
- proof that each reference input is owned or licensed for this use;
- Meshy account/subscription invoice or plan evidence covering the generation;
- a PDF/screenshot of the applicable terms and commercial-use grant, with date;
- derivative edit history and final shipped asset hash;
- reviewer decision that no trademark, recognizable third-party design, embedded
  watermark or unlicensed texture remains.

Private generation improves provenance; it is not by itself a commercial-rights
grant. Reference screenshots may guide proportion or function only when their
licence permits it. Do not bake third-party logos, pixels, distinctive vehicle
designs or proprietary CAD into a shipping derivative without permission.

## Steam generative-AI disclosure

Steam's current Content Survey distinguishes AI-assisted content that ships with
the game and is consumed by players from general productivity gains during
development. See the official
[Steamworks Content Survey](https://partner.steamgames.com/doc/gettingstarted/contentsurvey?l=english).

Use this as a **draft**, not as a quote from Valve, and update it against the
actual release manifest:

> Line Boss contains pre-generated 3D geometry and texture/material source art
> created with Meshy during development. These private outputs were selected,
> edited, optimized, retopologized, rigged and integrated by the developer. No
> generative AI service runs while the game is being played, and players cannot
> submit prompts or generate content in the product. Reference inputs and shipped
> derivatives are reviewed for ownership, licensing and infringement before
> release.

The disclosure applies only if Meshy-derived work is in the shipped build. AI
used for development-only planning, code assistance, audits, documentation or
automation is tracked internally as productivity assistance; it is not silently
relabelled as player-consumed art. If AI-assisted code, UI text, localization,
audio, narrative or art becomes shipped player-facing content, add it to the
release inventory and reassess the Steam answer. When uncertain, disclose more
and ask Steamworks/legal review rather than omit a material use.

## Per-asset promotion gate

- [ ] Authority file, hash, source URL/task ID and rights evidence are attached.
- [ ] Reference inputs are owned/licensed and documented.
- [ ] Dimensions, axes, pivot, sockets and semantic mover roots match gameplay.
- [ ] Topology, UVs, materials, livery masks and texture channels are audited.
- [ ] Triangle/draw-call/texture budgets and LOD/HLOD/Nanite policy are measured.
- [ ] Simple collision and maintenance/player/logistics envelopes are verified.
- [ ] Safety colours, labels, tools, cables and emissives are excluded from player tint.
- [ ] Lights/beacons/VFX/SFX follow authoritative runtime state.
- [ ] The asset is selected by runtime code/Blueprint without hidden fallback.
- [ ] A fresh package proves appearance, motion, interaction and performance.
- [ ] The exact shipped hash and AI-disclosure classification are archived.
