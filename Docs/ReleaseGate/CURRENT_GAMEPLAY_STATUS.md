# Current gameplay status

> **Correction, 2026-08-16.** The table below is a 2026-08-12 snapshot and now
> understates the project in two places. Weld is recorded as *"Source candidate /
> planned gameplay ... No production Unreal station loop exists"*; in fact the
> runtime coordinator implements the full 57-station route with quality gates,
> rework and save/restore, and the whole `LineBoss` suite is **275/275 green**.
> The shell is also no longer console-only: `ALBOneFactoryGameMode` installs the
> production-flow HUD and a player controller, and the commission / order /
> speed / quality journey has been exercised in a real rendered session. See
> [the visible running factory](../OneFactory/ONE_FACTORY_VISIBLE_RUNNING_FACTORY_v001.md)
> and [the unattended session handover](../OneFactory/ONE_FACTORY_UNATTENDED_SESSION_HANDOVER_2026-08-16.md).
> Per this document's own rule that the strongest evidence wins, treat those as
> current for weld and the player shell. Everything remains **validation-only**
> until a packaged journey is proven.
>
> **Update, 2026-08-16 (evening).** Packaged journeys are now proven: the
> Development packages v002–v005 each ran the commission → order → 57-station →
> quality-hold → player-decision → dispatch journey headless and green, and the
> save round trip (`7/57`, cycle 25%) reproduced exactly in the package. The
> product direction is decided and committed: **one continuous building**, coils
> to finished car, at the restored press shop's detail standard. All four press
> trains stand on the reference 2200 cm row grid and the complete restored
> shop — every static-mesh component of every non-train actor, with authored
> per-slot materials — materialises around them from a read-only manifest:
> **2,804 instances, zero unresolved, proven from cooked content in the
> packaged `PlayableShell_v006`**. Trains B–D remain visual-only; making them
> playable is a separately scheduled versioned press-layout contract change.
> The six-dimension release audit and its fix execution are recorded in
> [the press release audit](../OneFactory/PRESS_SHOP_RELEASE_AUDIT_2026-08-16.md). See also
> [the continuous building decision](../OneFactory/ONE_FACTORY_CONTINUOUS_BUILDING_DECISION_2026-08-16.md)
> and [the shops release pass](../OneFactory/SHOPS_RELEASE_STANDARD_PASS_2026-08-16.md).

Snapshot: **2026-08-12**. Authoritative implementation is under
[`Source/LineBossCarFactory`](../../Source/LineBossCarFactory); the status below
is deliberately narrower than the design roadmap.

The overnight developer-capability and focused-regression handoff is recorded in
[the 2026-08-12 morning handoff](MORNING_HANDOFF_2026-08-12.md). The current
Editor evidence is also itemised in [Validation evidence](VALIDATION_EVIDENCE.md).
The product-position and comparator decision is recorded in the
[full gameplay and market audit](../../Saved/Audits/Gameplay/20260812_full_gameplay_market_audit/full_gameplay_market_audit.md).

## Player journey

The current playable direction is:

`inbound delivery -> coil inspection -> depack/preparation -> press train ->
inspection -> full panel stillage -> FLT delivery to weld intake`

Weld, paint, and assembly extend that chain; they do not replace the press-shop
simulation. Car Manufacture's readable “station + robot + next part” model is a
useful presentation baseline, while Line Boss differentiates itself with exact
stillage identity, physical logistics, buffers, takt, quality, maintenance, and
player-editable safety/logistics infrastructure.

## Evidence-backed status

| Area | Status | Current truth |
|---|---|---|
| Management camera, pan/rotate/zoom, rich build catalogue, order editor, actor selection and persistent alert strip | **Present in Shipping package `PlayerBuildable_v1031`; interactive package journey pending** | The exact current revision builds and launches as Shipping. Editor automation is green and the recognisable placement ghost/rich catalogue are source-present, but the fresh and populated packaged input journeys remain open. |
| Player-built press-shop machines, storage zones, connections, routes, floor markings and inbound/press logical flow | **Validation-only in current source** | Current live evidence proves valid placement, a named obstruction with corrective guidance, and immediate recovery without a stale warning. A new package must still prove the complete build-to-production journey. |
| Authored PR-004 through PR-010 and complete press train | **Validation-only in current source** | Operational/state authorities exist. The repaired live MCP gate passed all six press-train tests and the final campaign/material-flow selection passed both v17 campaign round trips; indexed and packaged proof is still pending. |
| Factory name and player-selected primary/secondary machine livery | **Present in Shipping package `PlayerBuildable_v1031`; journey pending** | The mandatory setup modal is visible in the Shipping launch and branding/livery tests are green. A stale Development firewall dialog prevented completing the clean input/capture journey; protected safety colours remain fixed. |
| Empty/full panel-stillage storage, equal treatment, three-high stacking and one starter stillage FLT | **Validation-only** | The repaired live MCP gate passed all four stillage-FLT tests plus `PhysicalStillageFLTExactHandoff` (11/11 across the six press, four FLT and physical-handoff selections). This supersedes the earlier live red diagnosis for current source, but no standalone indexed report or packaged end-to-end journey exists yet. |
| Coil AGV, routes and save/restore; coil FLT and rear-wheel steering | **Validation-only** | The final live MCP AGV/routes/save selection passed 9/9 with zero test warnings or errors, including natural route ownership, player placement/persistence, runtime motion and legacy restore. `AutomaticInboundRoute` passed after its test fixture and automatic connected-endpoint placement path were repaired. The separate `CoilFLTRearSteerCombined` directory still has no archived machine-readable `index.json`, so the current coil-FLT/rear-steer claim is not yet a release pass. |
| Cleaning and maintenance robots | **Packaged presence/telemetry only; full work loops validation-only** | Four docked support units were present in v1029 state capture. The final live MCP support-robot selection passed 6/6 with zero test warnings or errors for natural cornering, player-built envelope clearance, automatic charging, CR01/MR01 runtime and guarded dock restore. All light/beacon states, purchase/progression and maintenance consequences still need fresh package proof. |
| Deterministic finance, research, upgrades, quality, maintenance records and OEE calculations | **Validation-only in current source** | The latest broad live MCP selection passed all 24 `LineBoss.Management` tests. This includes responsive readability, save/load double confirmation, counter epochs across actor replacement and retry-safe failed-bucket evidence. The live result is not an indexed report or package proof. Management analytics still need retention/rollup. The authority deliberately invents no random faults. |
| Current UI/placement presentation | **Present in Shipping package, not visual-final** | Live Editor evidence proves readable livery/HUD, named obstruction guidance and recovery. Authorised first-build framing, recognisable hierarchy ghosts and rich decision cards are now source-present and tested; exact packaged interaction/visual acceptance and populated-factory lighting remain open. |
| ED/e-coat line | **Validation-only blockout** | A runtime actor, imported blockout modules, process bays, carriers, liquids, fans and beacons exist. The supplied Meshy tank/oven authorities still require the documented modular production rebuild, and no current packaged visual/operational pass exists. |
| Weld shop (MIG, spot welding, panel picking) | **Source candidate / planned gameplay** | Source audits exist. MIG remains a high-poly articulation review; the spot arm has a fused shoulder and should reuse the corrected shared arm with a new C-gun head. No production Unreal station loop exists. |
| General assembly (robots fitting parts at stations) | **Planned** | Required product direction is known: visually clear stations, robots fit ordered parts, buffers and material shortage stop the line. No completed assembly-shop runtime is proved. |
| Production car, BIW shell and individual Cairnwell 2040 panels | **Source candidate** | Lightweight panel FBXs and mappings exist, but the panel README explicitly records no Unreal promotion. |
| Final localization, accessibility and voice | **Planned** | Current HUD strings are hard-coded English and there is no voice acting. See the localization/audio gate. |

## Known limitations that currently block “finished”

1. The repaired live MCP gate is green for the former physical-stillage and FLT
   failures, but the latest standalone indexed physical-handoff report remains
   the older red run. A reproducible indexed green report and packaged
   inbound-to-weld journey are still required.
2. The latest indexed `WholeShopCampaignRoundTrip` report is the red v16 run.
   Both v17 topology tests succeeded again in the final live 5/5
   campaign/material-flow gate, but no standalone indexed report or packaged
   process-restart journey proves release compatibility.
3. All 24 current management tests and all 24 current FactoryBuilder tests passed
   through live MCP. This remains Editor evidence. Complete purchase, terminal
   revenue, maintenance-hold and recovery journeys still need packaged proof.
   The builder suite also emitted one RHI virtual-allocation warning and six
   synthetic-world no-context teardown warnings that require triage or formal
   acceptance.
4. The newest source revision has a successful Shipping build/archive and a
   listener-free runtime observation in `PlayerBuildable_v1031`, but no complete
   fresh/populated packaged journey, save/restart proof or performance capture.
5. Weld and assembly are not implemented production shops; paint is a blockout.
6. Several approved-looking meshes remain under `Candidates`; folder names are
   not promotion evidence.
7. Recognisable hierarchy-based placement ghosts, richer decision cards and
   first-build bay framing are source-present and covered by focused tests.
   Their packaged visual acceptance, populated-factory lighting, accessibility
   and performance QA remain pending.

## Next gates

1. Archive the now-live-green 24-test management, 24-test FactoryBuilder and
   exact-delivery/FLT/press selections as indexed reports, then archive coil
   rear-steering, both v17 topology and every v13-v16 migration result.
2. Prove the checked-in v17 preflight/restore path leaves the world unchanged on
   every rejected or mid-restore failure, not only invalid-management input.
3. Accept the source-present first-build framing, recognisable placement ghosts
   and rich catalogue cards in package; validate softened populated-factory
   lighting and repeat captures at 720p, 1080p and 4K with accessibility checks.
4. Prove the seven-page projection with mouse, keyboard and controller in package.
5. Promote only licensed, optimized, collision-safe assets; then complete the
   weld vertical slice before general assembly.
6. Run the v1031 Shipping finish checklist on new campaign, build, production,
   save/load, fault/recovery and performance journeys.
