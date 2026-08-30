# Conveyors, scale and playability — six-game research (v001, 2026-08-25)

Owner directives this session: (a) conveyor belts that AUTO-connect,
(b) "the factory needs to be a lot bigger" (implemented same day: floor
240 m, buildable 220 m — supersedes the earlier "bigger maps: not
doing" line in the vision memory), (c) "a handful of stations isn't
enough", (d) "proper playability", (e) every station hosts drones.

Method: eight-agent research workflow — one analyst per game (Factorio,
Satisfactory, Dyson Sphere Program, shapez 2, Captain of Industry,
Production Line), a synthesis, and an adversarial critique. Raw agent
returns live in the session workflow journal; this doc is the curated
result. EDITORIAL NOTE: the critique correctly demands re-baselining
onto the spacecraft-era authorities (`ALBSpacecraft*`) — the shipped
v001 belt visual already follows that (it reads the spacecraft stage
table); the synthesis' car-era subsystem references are historical and
must not be implemented. Where the critique defends older recorded
decisions against tonight's directives, TONIGHT'S OWNER WORDS WIN
(bigger floor, belts requested by name).

## Shipped tonight (v001)
- Auto-connected belt VISUALS: the belt path IS the stage table; belts
  redraw on any placement change; chevron trains flow toward the next
  stage. Presenter-only — no second logistics simulation yet.
- 240 m floor / 220 m buildable, walls, dock apron, sky.

## The strongest cross-game lessons (full set below)
1. Transport vs transfer: keep the handoff VISIBLE (Factorio's
   inserter lesson) — our fitting drones are the transfer layer.
2. Auto-connect means auto-ROUTED with player-owned endpoints and
   ghost-before-commit; never silently guess (Factorio 2.0 backlash,
   CoI port-snap praise).
3. One belt family with research marks; no connector zoo (DSP's
   single sorter is the genre's most-praised connector).
4. Items on belts individually visible, never batched (shapez 2 train
   complaint); with one ship in flight every stall must be readable.
5. Bounded dense floor beats infinite sprawl for product-is-the-star;
   growth = bay/floor unlocks per craft tier, not horizontal sprawl.
6. Time-to-first-automation under 45 min; freeplay after a working
   starter spine (CoI trucks-first onboarding = our drones).
7. Research gates that visibly change the floor beat stat bumps.

## Proposed v002 belt SIMULATION (needs owner sign-off)
Port-to-port click-connect: click output, click input, the transport
authority pathfinds on the 100 cm grid, ghost renders before spend,
fail-closed plain-words refusal when no route exists. Belts carry chain
items only — the craft NEVER rides a belt (its cradle path is the hero
path). Drones remain the ambient fallback carrier so a missing belt
degrades to slower, never to broken. Belt Mk.II via research.

---
## Appendix A — synthesis (verbatim agent output)

# Line Boss — Belts, Scale, Catalogue, First Two Hours

Recommendations grounded in the six-game research and the existing codebase (`ULBFactoryConnectionSubsystem` already has `CanConnect`/`Connect`/`AutoConnectNewMachine` over `ULBFactoryProcessPortComponent`, and `ALBBodyShopBuildAuthority` already has 100 cm-snapped cell definitions with typed `FLBBodyShopPortAddress` ports and connection legality — the belt system should be built on these, not beside them).

---

## 1. Belt design: parts flow on belts, the ship never does

**The hard rule first: belts carry chain items (materials and parts), never the craft.** Production Line's most transferable finding is the two-layer split — a readable, narratable product path versus a separate parts-supply layer — and its loudest complaints all live where the automatic layer became opaque. The ship keeps its own hero path (cradle/tug moves between assembly stations, drones fitting parts), and belts are the circulatory system feeding the stations. This is also what protects "product is the star": the camera reads one big object moving slowly through a line, fed by many small objects moving fast.

**Auto-connect means auto-ROUTED, player-owned endpoints.** The genre verdict is unambiguous: Captain of Industry's port-snap + point-to-point pathfinder "totally changed how transport building felt"; Factorio took real backlash the one time it force-enabled an assist that guessed endpoints. So:

- **Verb:** click an output port, click an input port; the transport authority pathfinds a route on the existing 100 cm grid; a key cycles equally-legal alternative routes; the ghost renders **before** any credit is spent, with illegality shown in the ghost (Satisfactory's worst sin is validating after the first click — do not repeat it in a fixed-camera game where depth aiming is harder).
- **Placement assist:** when a machine is placed, `AutoConnectNewMachine` may *propose* routes to compatible nearby ports as ghosts with a one-key accept — never silently commit. A wrong guess undone is a minor annoyance; a wrong guess unnoticed poisons trust in the whole system.
- **Failure:** no legal route → fail-closed refusal with a plain-words reason ("No clear path: Hull Fab 2 output blocked by Paint Bay wall, row 12"). This is the existing toast philosophy applied to logistics, and it directly answers Production Line's "no route to stockpile" opacity complaint and shapez 2's starved-station complaint.

**One belt family, upgrade marks, visible handoff, no inserter zoo.** DSP's single filtered upgradeable sorter is the most-praised connector design in the genre; Factorio's six inserters are the least. Ship one `LBConveyor` with marks (Mk.I → Mk.II by research). The belt-to-station handoff is a visible animated intake arm that is *part of the station's port*, not a separate purchasable — you keep Factorio's "make the transfer watchable" lesson without spending one of your ~15 EA building slots on it. Items on belts are individually visible and continuous — **never batch/packetized delivery** (shapez 2's train complaint: batches starve stations unpredictably; with one ship in flight, every stall is a story the player must be able to read).

**Drones stay the ambient fallback layer.** CoI's decisive onboarding trick is that trucks make everything work before the player knows how to route anything. Line Boss already has this: transport drones are the default carrier from minute one; belts arrive by research as the throughput/cost optimization for bulk chain items. Drones keep the irregular jobs forever (ship-fitting, one-off hauls, rework returns).

**Authority fit (this is where the codebase makes it cheap):**

- A single-owner **transport authority** (extend `ULBFactoryConnectionSubsystem` or a sibling `LBFactoryTransportAuthority`) owns the route graph and every item-in-transit record. Belt meshes/rollers/items are presentation, reconstructed from route state — the same pattern as `ProductionFlowAuthority` owning genealogy while presentation reconstructs visuals. No second logical record, ever.
- Stations **pull** through ports; an uncommissioned/faulted/unpowered station's port rejects intake (fail-closed, matching department behavior).
- Save/restore validates the entire route graph — endpoints exist, ports match direction and item type, no orphaned in-transit items — *before* a single mutation, exactly like the existing snapshot validators (`RestoreConnections` already returns `OutReason`; keep that shape).
- **Editing never destroys work:** demolishing a belt refunds the belt 100% and returns in-transit items to the nearest storage (Production Line's destroyed-WIP pain is the one to design against; DSP proves full-refund demolition is why experimentation stays fun under an honest economy).

**v001 vs later:**

| v001 (prove the verb) | v002 (research-gated) | Explicitly later / never |
|---|---|---|
| Port-to-port auto-routed ground belts, one mark | Mk.II speed; elevated crossing piece (one, clean — DSP's "goofy slopes" complaint) | Smart per-item routing junctions (Production Line got them late; a one-ship line likely never needs them) |
| Ghost validation before spend; route alternatives on a key | Implicit splitter/merger spawned by dragging into an existing belt (shapez 2 pattern) | Belt variant zoo, separate inserter entities |
| Full-refund demolish, WIP preserved | Port filters; blueprint-copy of a proven feed segment | Force-enabled placement guessing |

---

## 2. Scale: one site, purchasable bays, spectacle on the edge

**Do not copy any of the big maps.** Factorio/Satisfactory/shapez 2 sprawl exists to serve anonymous-throughput games where the camera abandons individual items. Every "lessons" column converges on the same instruction for Line Boss: bounded, dense, readable, unity of place (CoI's island, DSP's planet). The factory's footprint is the trophy; the launch apron is the stage.

**Concrete numbers** (craft 14–21 m, stations 10–20 m, so a station pitch with clearance is ~25 m):

- **Site: 512 × 384 m fixed plot** (~10× today's 140×140 area — this is the "A LOT bigger" the owner asked for, while staying frameable at max zoom for the FOV-48 camera; beyond ~500 m a side the floor stops reading as one place).
- **Divided into 64 × 64 m bays** on the existing grid — a bay comfortably holds a Cargo-01 (21 m) station with full clearance envelope, or a 4–6 machine fabrication cluster. Size bays against the *largest future craft*, not the Scout — shapez 2's "platforms too small" thread is the warning; the Scout is the smallest ship ever.
- **Start: 6 bays open (3×2, 192×128 m)** — holds the prebuilt starter line plus room for the first two expansions. **Ceiling: 8×6 = 48 bays.**
- **Expansion is purchased with credits, bay by bay** (Production Line's lot pattern, which fits contracts-as-income), but **no rent** — power draw and maintenance are the honest standing costs; recurring rent punishes the deliberate pace of a one-ship game.
- **The launch runway + apron is permanent site furniture on the eastern edge**, never buildable over. The chicane-and-sprint camera framing is protected land; the space budget is spent on clearance and spectacle, not machine density.
- **Craft-tier growth is vertical, not horizontal:** the Cargo tier unlocks a *bigger assembly hall structure* (taller doors, Mk.II station envelopes per the fail-closed capacity-envelope rule) placed across multiple bays — CoI's Blast Furnace → II mark pattern applied to the building that stages the star.

One hall identity, multiple functional zones within it: receiving dock (west edge), fabrication field (belts), the assembly line (hero path, center), test pad, runway (east). The ship's journey literally crosses the factory left-to-right — the floor plan is the narrative.

---

## 3. Catalogue: the next 10, each buying a decision

Currently ~12 station types; EA target ~15 buildings + marks. The genre's gating spine to steal: Satisfactory gates on *delivering the product*, Production Line's breadth comes from *subdividing the line you have*, CoI makes *research itself a production chain*, and CoI reaches ~100 "types" via marks of ~30 bases. Priority order:

1. **Conveyor + station ports** (the entire Section 1 system) — decision: layout and routing. This is the multiplier for everything below.
2. **Storage rack / buffer depot** — decision: where to buffer, which chains to decouple. Visible stock levels double as the bottleneck display.
3. **Component Fabricator family (start with Hull Panel Press and Wiring/Avionics Fab)** — decision: **make vs buy**, per part. Production Line's "Make slots" are the single best mechanic to import: every part can be imported at the dock for a price or fabricated on-site for capex + inputs. This is what turns 30 chain items into gameplay instead of a list.
4. **Cargo receiving dock Mk.II (scheduled deliveries)** — decision: supply cadence and dock throughput vs storage depth. Feeds the transport-drone logistics EA item.
5. **Power substation + battery bank** — decision: spatial power routing and peak-load management (the grid exists; give it buildings, and make brownouts *visible* — stations dim and refuse, CoI's smoking-machine heartbeat).
6. **Drone hub / charging bay** — decision: fleet size vs battery honesty vs belt investment. The tension between layers 1 and 2 of logistics is a real ongoing choice.
7. **QA inspection gantry** — decision: where to inspect, speed vs defect risk. Directly feeds contract defect penalties and reputation (priority 2 of the endorsed vision). Pass → next station; fail → 8.
8. **Rework bay** — decision: rework capacity vs penalty acceptance. The fail path made physical and watchable, not a stat.
9. **Research lab consuming manufactured lab equipment** — decision: research throughput is itself a chain (CoI/DSP). Fills the research tree's empty API and gives the factory a second output besides ships.
10. **Coating & livery cell** — decision: contract-specific finish requirements (premium contracts demand it), and it's the most camera-friendly transformation on the line — a spectacle feeder between assembly and test.

Plus **Mk.II marks** of existing assembly stations (bigger craft envelopes for the Cargo tier) — breadth via marks, not new designs. **Do not build:** belt/inserter variants, cosmetic-only decor buildings, parallel duplicate factories. Gate 1–2 by the first contract, 3–6 by research paid from deliveries, 7–10 by reputation tier — every unlock must visibly change what the floor looks like.

---

## 4. Playability: first two hours

**Design constants** (the research is unanimous): first fully-automated moment inside 45 minutes; **first ship delivered and launched inside the first session (target: minute 30–40)**; no modal tutorial — a rewarded objectives panel (CoI) plus the fail-closed toasts as the in-situ teaching voice; current contract's target craft pinned permanently on screen (shapez 2's hub shape); forgiving economy — no instant bankruptcy, a bailout contract exists at low balance (Production Line's $0-game-over is the anti-pattern).

**Minute 0–10 — the prebuilt line with one designed gap.** Player lands on the 6-bay site with the owner-approved bare-bones starter line: dock → storage → two assembly stations → cradle → test pad → runway, powered, with contract Scout-01 pre-accepted and pinned. Press start. The ship begins building — and stalls, loudly and legibly: one station is missing its connection (a toast says exactly why). The player performs the port-click connect verb once, guided by the objectives panel, and flow resumes. Satisfactory's tedium-then-relief compressed: you fix by hand exactly once before automation carries it.

**Minute 10–35 — watch, starve, fix, launch.** The minute-to-minute verb is the Factorio cadence inverted onto one product: read the ship's build progress → see which station is starving it (idle drones, empty feed rack, plain-words reason on the station card) → fix (order parts at the dock, add a drone, nudge a route) → watch the ship visibly advance. Ship #1 completes: full launch spectacle — hover test on RCS flames, strobes arm, chicane, sprint out. **This is minute ~35 and it is the hook; nothing may delay it.**

**Minute 35–120 — contracts are the milestones (Satisfactory's HUB pattern, but the terminal is the launch pad).** Each delivery pays credits *and* is the unlock event:

- **Contract 2** (~20 min): two more part types required → unlocks **belts**. The objective: replace the drone haul from dock to Station 1 with your first routed belt. The relief is visible — drones freed for fitting work.
- **Contract 3** (~25 min): part import prices rise in the contract terms → unlocks the **Hull Panel Fabricator**; player makes their first make-vs-buy call and builds their first belt-fed machine cluster in an empty bay.
- **Contract 4** (~25 min): first **defect penalty** contract → unlocks QA gantry + rework bay; the player places inspection into the hero path and watches a failed panel take the rework detour.
- Between contracts, **small payouts every 3–5 minutes** (shapez 2's two-tier cadence): side objectives — deliver defect-free, keep peak power under X, first belt over 20 m — paying research points toward the lab unlock.

**Hour-2 exit state:** 4–5 ships launched, a working belt network, one fabricator chain, QA in the line, research started, and the player has bought bay #7 with contract income — expansion purchased with money the launches earned, closing the loop the vision names: every system feeds the launch.

**Implementation note:** milestone/unlock state gets its own single-owner progression authority (fail-closed, snapshot-validated before mutation, like everything else), and the starter line must be captured through the same build authorities the player uses — the existing `SeedsProductionStations()==false` bootstrap contract already mandates exactly this; the prebuilt starter is a saved player-built layout, not map-package seeding.
## Appendix B — adversarial critique (verbatim)

1. **The proposal is grounded in the wrong codebase.** It opens claiming to be built on `ULBFactoryConnectionSubsystem` and `ALBBodyShopBuildAuthority` — the car-era OneFactory stack — and never mentions that a spacecraft-era slice already exists in `Source/LineBossCarFactory/`: `ALBSpacecraftBuildAuthority` (100 cm grid, marks via `StageClassId`, fail-closed craft-capacity envelopes, snapshot-validated save/restore), `LBSpacecraftPowerAuthority` (`ConnectLoad`/`GetTotalDrawKw`, PowerPlant family with `PowerSupplyKw`), `LBSpacecraftDroneFleetAuthority` (charging draws real grid power, per test `LineBoss.Spacecraft.Drones.ChargingDrawsRealGridPower`), `LBSpacecraftInventoryAuthority`, storage racks (`StorageCapacityUnits`), and `LBSpacecraftSaveGame`. Several catalogue entries (storage rack, power buildings, drone hub, Mk.II marks, capacity envelopes) recommend building things that are partially or fully shipped, and the flagship belt system is proposed as an extension of the car-era connection subsystem — coupling the EA centrepiece to the stack the pivot supersedes. Required amendment: re-baseline every section against the spacecraft slice; any transport authority attaches to the `LBSpacecraftProductionTypes` stage table, not the four-car-department legality model.

2. **Section 2's site plan contradicts two recorded owner decisions and misstates the current facts.** (a) The endorsed vision explicitly lists "bigger maps" under NOT doing. (b) The owner already sized the floor: `LBSpacecraftBuildAuthority.h` carries the receipt — *Owner 2026-08-25: "the factory needs to be a lot bigger" — 220 × 220 m buildable inside the 240 m floor*. The proposal calls today's site "140×140", attributes an "A LOT bigger" ask to the owner as if unspent, and unilaterally proposes 512×384 m / 48 bays — ~3.6× the area the owner just chose. It also hand-waves "frameable at max zoom" against `LBManagementPawn`'s tested FOV-48 framing contracts, and a 512 m floor makes a 14 m ship read as a speck — the opposite of product-is-the-star. Required amendment: strike all the site numbers; layer bay-by-bay purchase (which is a fine idea) onto the existing 220 m floor; any further resize is an owner decision presented with rendered options.

3. **Belts are an unbudgeted second logistics system, and they are not the EA logistics item.** The owner's priority list says the heavy transport drone hauling dock → storage → stations *IS* the EA "AGV logistics" item, and the EA scope names "storage/AGV logistics" — not conveyor networks. Section 1 quietly commits: a grid pathfinder with alternative-route cycling, a per-item in-transit simulation with full save-graph validation, elevated crossings, implicit splitters/mergers, port filters, blueprint copy, and animated intake arms — on stations that currently have **no port components at all** (ports are car-era; spacecraft stations are data records). "The codebase makes it cheap" is false for the stack that matters. This is the single largest scope trap in the document. Required amendment: belts require explicit owner sign-off as an EA addition at all; if approved, ship only the v001 column and cut crossings/filters/blueprints from EA; drones stay primary, not "fallback".

4. **The WIP model is never stated, and everything hangs on it.** `BuildRoute` derives a strictly serial route. If exactly one craft is in flight (the proposal's own words: "with one ship in flight, every stall is a story"), then stations idle ~90% of the time and the entire throughput apparatus — buffers, belt marks, dock cadence, make-vs-buy capacity — is decoration with no gameplay function. If craft pipeline (which "a ship every few minutes" implies), the "camera reads one big object" narration, genealogy, and hero-path claims all need rework. Required amendment: decide single vs pipelined WIP explicitly before any of Sections 1–3 are costed; it determines whether half the catalogue does anything.

5. **QA + rework breaks the route contract it pretends to sit beside.** The derived route is serial with length equal to the stage-table count; "fail → rework bay → rejoin" is a *branching* route and touches route derivation, genealogy, snapshot validation, and presentation. Selling it as two catalogue buildings is technically naive. Required amendment: for EA, model defects/rework as an in-station state and time cost (no topology change), or budget the branching-route contract change as its own system.

6. **The minute-0–10 "designed stall" violates fail-closed.** `CommissionFactory` and route derivation refuse *before* production starts when a required station or connection is missing — a ship cannot "begin building — and stall". Shipping a deliberately invalid starter layout also means the capture lane must accept a layout the validators reject, i.e. loosening a guard to make a script pass, which the repo conventions forbid. Required amendment: the teaching beat is a refusal-to-start with a plain-words reason; the ship's first frame of construction happens only after the player's fix — which is dramatically better anyway.

7. **Several recommendations import throughput-game psychology the constraints forbid.** A fabrication field of individually visible fast-moving items, side payouts every 3–5 minutes, a research lab giving the factory "a second output besides ships", and per-part make-vs-buy across ~30 items are the Factorio/shapez anxiety loop wearing a hero-path hat. Worse, unrestricted make-vs-buy has a degenerate solution — import everything — which empties the visible factory entirely, contradicting "the making is visible". Required amendment: belts visually subdued (slow, low item density, no glowing lanes); camera and notification priority always yields to ship events; research is one branch fed by deliveries, not a parallel product line; make-vs-buy limited to a few marquee parts with contract terms that require on-site fabrication for premium jobs.

8. **Catalogue arithmetic fails its own EA target.** Ten new entries plus Mk.II marks on top of the existing catalogue exceeds ~15 buildings, and at least five entries smuggle whole simulation systems (defect model, rework routing, research-as-chain, scheduled deliveries, contract finish requirements) behind a building name. Required amendment: audit against the shipped `StationCatalogue()`, count honestly, pick roughly three genuinely new *decisions* for EA, and mark the rest post-EA explicitly.

9. **The owner's number-one priority — the money loop — is missing.** No starting capital, no charging model beyond the existing `CostPence` fields, no reference to the approved placeholder balance, no credits display integration (owner: "50,000 cr", integer hundredths internally). Yet the pacing promises ("bought bay #7 with contract income") presuppose all of it. Required amendment: add a money-loop section, first, with concrete placeholder numbers flagged for owner retuning.

10. **The localization mandate is ignored.** Every quoted refusal string ("No clear path: Hull Fab 2 output blocked by Paint Bay wall, row 12") is hard-coded English, and the owner requires FText/LOCTEXT at the UI layer via reason codes, with English diagnostics kept greppable on the authority side. Required amendment: the toast/reason design must specify reason-code plumbing; catalogue `DisplayName` FStrings need the same path.

11. **The unlock economy is self-contradictory.** Belts unlock by contract (Section 4) but Mk.II "by research" (Section 1); side objectives pay "research points" (shapez pattern) while the lab consumes manufactured equipment (CoI pattern); and the lab enabling research is unlock #9, gated by reputation, downstream of things that need research. Four gating currencies, one circular dependency. Required amendment: one spine — contracts unlock buildings, research (one branch, per EA scope) deepens them — and one research input.

12. **Unmeasured performance absolutes.** "Never batch/packetized" and per-item continuous belt simulation are asserted with zero measurement, in a project whose standing rule is that no direction decision rests on an unmeasured performance claim again. The elevated crossing is also a readability hazard at fixed pitch −35 (occlusion of what's beneath). Required amendment: a measured item-count budget per view before committing the in-transit model; prototype the crossing under the real camera before it enters the catalogue.

13. **Missing items the researched genre actually agrees on.** (a) A production/bottleneck statistics view — every cited game has one; "visible stock levels" on a rack is not a stats screen. (b) Placement undo — full-refund demolish is not undo, and both Factorio and Satisfactory treat undo as table stakes. (c) The dead-time answer: what the player does while a ship builds — time controls, or pipelining, or deliberate watch-and-plan design; the proposal's cadence assumes constant intervention without establishing there is anything to intervene in (see objection 4). (d) Edit-during-production rules: can you demolish a station or belt while a craft is mid-route? The save validator will have opinions; the doc has none. (e) The launch itself gets zero effort lines — it is protected as *land* while belts get a version table, yet the launch camera/sound/fanfare is the signature moment and the wishlist clip is vision priority 5. Required amendment: add all five, and give the launch presentation at least the budget prominence of the belt system.

14. **Smaller but real.** "Coating & livery cell" presumes brand and colours which are formally OPEN — livery content must be presented as owner options, never graded to Cairnwell. "Bays sized against the largest future craft" is a guess — later-tier sizes are undecided; the fail-closed capacity envelope (already implemented via `MaxCraftEnvelopeCm`) is the mechanism, not bay-size divination. "100% refund" is an owner economy decision, not a design axiom. And pre-accepting the first contract deletes the player's first meaningful choice in a game whose pillar is "few, meaningful contracts" — pin it as the *offered* contract and make accepting it the first click instead.
## Appendix C — per-game lessons

[Factorio] Separate transport from transfer, and make the transfer visible. Factorio's belts never touch machines; a distinct, watchable entity (the inserter) does every handoff, and that is where players tune and read their line. For a ship line: the station-to-transport handoff (drone pick, crane lift) should be an explicit placed thing the player owns and can watch, never an invisible teleport between inventories.

[Factorio] Manual connection first, assistance opt-in later. Factorio earned 10 years of goodwill on hand-drawn routing, then took real backlash when 2.0 force-enabled smart belt dragging that guessed wrong. Ship with deliberate port-to-port connection plus strong snapping and clear legality feedback (the fail-closed toast system), and add ghost-planning/copy-paste style assists only once the manual verbs feel good — always with an off switch.

[Factorio] The core loop is bottleneck visibility, not menus. Factorio's minutes-scale cadence is see-the-starving-machine, fix, watch flow resume. With one ship as the product, the ship itself is the bottleneck display: the player should read which station is starving the craft directly off the floor (idle robots, waiting part, empty feed) and every fix should visibly change the ship's build progress.

[Factorio] Time-to-first-automation is the retention gate: under 45 minutes to the first machine doing a job the player did manually, with freeplay-from-zero and the research tree as the goal ladder — not a long tutorial. Gate the ~15-building EA catalogue by research so each unlock visibly changes what the line looks like, and milestone-gate later tiers (as Factorio gates oil) so players cannot research past what they can build.

[Factorio] Do not copy Factorio's scale model. Its effectively infinite chunk-generated map exists to serve thousands-of-items throughput, where single items stop mattering and the camera lives at map zoom. A product-is-the-star game inverts this: a bounded, dense, readable floor that the FOV-48 camera can frame alongside the ship, with growth expressed as bigger bays/floor unlocks for larger craft tiers rather than horizontal sprawl.

[Dyson Sphere Program] Put the player at product scale during onboarding: DSP's mecha makes the first hour of manual work the tutorial — for Line Boss, let the player hand-drive the first ship's assembly steps on the visible line before automating them, so automation feels earned and the ship's size registers against the camera.

[Dyson Sphere Program] One connector that grows beats many connector types: DSP's single extendable, filtered, upgradeable sorter is its most-praised UX call over Factorio's six inserters — Line Boss's belts/AGV drones should be one family with upgrade marks, not a catalogue of variants.

[Dyson Sphere Program] Make routing assisted and mistakes free: auto-curving drag placement plus 100%-refund deconstruction is why DSP's first hours stay fun; its worst complaints are exactly where routing gets fiddly (vertical crossovers, silent backwards sorters) — in 2.5D, snap ports, preview ghosts, refund demolition fully, and make every mis-connection loudly visible (which Line Boss's fail-closed toast system already matches).

[Dyson Sphere Program] Gate content on an artifact the factory visibly manufactures: DSP's matrix cubes mean research IS factory output, so progression and production are the same loop — Line Boss's equivalent is the delivered ship: let contracts/reputation from each launch be the research currency, keeping 'the ship leaving' as the pulse of progression.

[Dyson Sphere Program] Bound the canvas, grow by new canvases: DSP planets are fixed-size and readable, and scale comes from adding planets with distinct roles — for a one-ship-at-a-time game, keep the single factory floor bounded and legible, and expand via new bays/halls for bigger craft tiers rather than an infinite sprawl that dilutes the assembly line as the visual star.

[Satisfactory] Snap-assisted manual routing is the sweet spot, but validate in the ghost: keep player authorship of every connection while making ports magnetic and direction-aware (input/output inferred from what you clicked) — and fix Satisfactory's worst UX sin by showing invalid slope/clearance/reach in the hologram BEFORE the first click commits, which matters even more in a fixed 2.5D camera where depth aiming is harder.

[Satisfactory] Onboard by tedium-then-relief, not tutorial text: make the player hand-perform each task exactly once (carry a part, fit a panel), then unlock the station/drone that automates it; Satisfactory proves the first visible automated chain must land inside the first hour — for Line Boss that means one craft visibly progressing through 2-3 stations before the first contract completes.

[Satisfactory] Gate progression on delivering the product itself (HUB-milestone pattern): Satisfactory's tiers unlock by physically feeding parts into a terminal, which maps directly to contracts-as-income — each delivered spacecraft is simultaneously the paycheck, the unlock currency, and the spectacle, reinforcing the launch-moment signature.

[Satisfactory] Design upgrades as refund-and-replace with mass application from day one: per-segment belt upgrading is Satisfactory's most-cited complaint after five years; with far fewer logistics runs in a one-ship factory, in-place station/route upgrades (materials refunded, line kept running or failing closed visibly) are cheap to do right and avoid the genre's known misery.

[Satisfactory] Size everything in grid tiles against one module (Satisfactory's 8 m foundation: Constructor 1x1, Assembler 2x2, Manufacturer 3x3) so layout math is legible at a glance — and note the inverse scale lesson: Satisfactory needs 47 km2 because thousands of anonymous items sprawl, but a product-is-the-star game needs the opposite ratio, one readable floor where the craft is the biggest, most watched object; spend the space budget on station clearance envelopes for larger craft tiers, not map area.

[shapez 2] Routing assist is table stakes, not polish: drag-to-place with auto-orientation, auto-connect to machine ports, ghost/L-planner with waypoint anchors, and implicit splitter creation are why shapez 2 players happily wire huge lines. Line Boss's grid builder (100 cm snap, ports on cell definitions) should auto-snap belt/AGV routes between station ports and show a ghost plan before commit — never make the player hand-draw every segment.

[shapez 2] Continuous, legible flow beats batch transport: shapez 2's single biggest logistics complaint is trains delivering in packets that starve belts unpredictably. For a one-ship line where every part matters, make transport-drone/AGV deliveries individually visible and every stall explained (this is exactly the fail-closed toast philosophy) — a station waiting on a part should show which part and why.

[shapez 2] Two-tier reward cadence: big milestone unlocks (new station/mechanic + more build area) spaced 30-90 min apart, with small research/task payouts every few minutes in between, is what keeps the first sessions compelling. Map spacecraft contracts to the milestone role and side objectives (quality streaks, OEE targets) to the research-point role, and keep the current contract's target craft permanently visible the way shapez 2 pins the goal shape in the hub.

[shapez 2] Chunked build plots make factories modular and readable, but size them generously: shapez 2's 20x20-tile platforms taught players to think in modules, yet 'platforms too small' is a real complaint thread. Line Boss should sell expansion as discrete bays/plots sized against the LARGEST future craft envelope (Scout is the smallest ship), so upgrading capacity feels like unlocking a bigger bay, not fighting the grid.

[shapez 2] Keep building playful even with an honest economy: shapez 2's free placement/deletion makes experimentation the core pleasure — the game is a layout puzzle, not a scarcity fight. Line Boss charges credits for stations, so compensate with full-refund demolish (or cheap relocation), ghost planning before spend, and instant blueprint-style copy of proven line segments, so money gates progression pacing without punishing iteration.

[Captain of Industry] Route by intent, not by tile: CoI's single biggest UX win was port-snapping plus point-to-point pathfound transports (pick source port, pick destination port, engine routes it; CTRL cycles alternatives). For Line Boss, station-to-station connections should be exactly this — click output port, click input port, auto-routed path, fail-closed with a plain-words refusal when no legal route exists — never freehand belt-drawing.

[Captain of Industry] Ship an ambient logistics fallback before any routed logistics: CoI's automatic truck fleet means the first hour works with zero routing knowledge and belts arrive later as an optimization. Line Boss's transport drones should be that default carrier from minute one, with fixed conveyors/routes as a researched throughput upgrade — onboarding cost drops to near zero.

[Captain of Industry] Tutorialize with a rewarded objectives panel, not a modal tutorial: CoI is pure freeplay plus a guide-objective list that pays free resources per step. Combined with Line Boss's fail-closed toasts as the teaching voice, a contract-shaped objective chain (salvage -> first station -> first component -> first ship) that pays Credits keeps the sandbox honest while steering new players.

[Captain of Industry] Make upkeep a visible, physical heartbeat: CoI's maintenance is a manufactured consumable, and starving it makes machines smoke and stop on screen — the machine economy is honest because failure is a spectacle, not a stat. Line Boss's power/drone-battery/material truths should fail the same way: visible slowdown, beacon changes, an explained refusal — which also feeds the product-is-the-star camera.

[Captain of Industry] Unity of place beats map sprawl: CoI's fixed island where extra buildable ground must be manufactured (terraform/reclaim) makes the factory's footprint itself the progression trophy. For a one-ship-at-a-time game, keep one readable floor and let density, station upgrade marks (CoI's Blast Furnace -> II pattern maps directly to larger craft-capacity station marks) and the launch event express progress — CoI also shows ~100 building types and 5 research eras is the genre's breadth benchmark, reachable via upgrade marks of ~30 base buildings rather than 100 unique designs.

[Production Line: Car Factory Simulation] Keep two visually distinct logistics layers: Production Line's readable floor-level product path vs overhead auto-routed parts supply is exactly the split a product-is-the-star game needs — the spacecraft's journey through stations stays clean and narratable while drone/parts logistics live on a separate visual layer that never clutters the hero path.

[Production Line: Car Factory Simulation] Automatic routing must be either controllable or explainable — PL's loudest complaints are the auto-pathing resource conveyors making opaque suboptimal choices and junctions feeding busy stations while free ones idle. Line Boss's fail-closed plain-words refusal system is the right instinct; apply it to logistics too: every idle drone or starved station should state its reason.

[Production Line: Car Factory Simulation] Make subdivision-of-one-line the progression spine: PL's best idea is that research doesn't unlock parallel factories, it splits your existing 8 fat stations into 30+ specialized ones — the visible line itself is the trophy of progress. For one-ship-at-a-time production this is ideal: the same craft journey gets longer, finer-grained, and more choreographed rather than duplicated.

[Production Line: Car Factory Simulation] Never destroy work-in-progress on edit: players hated that rerouting a conveyor deletes half-built cars and their sunk cost. With one expensive spacecraft in flight at a time this pain multiplies — line edits should pause/park the craft or refund WIP, never vaporize the hero product.

[Production Line: Car Factory Simulation] The first product must complete fast and the tutorial must live in the world: PL hooks players because the first car rolls within minutes, but its pause-popup tutorial pushed everyone to community guides, and instant bankruptcy at $0 punished learners. Line Boss should land first-ship-delivered inside the first session, teach through the toast/refusal system in situ, and keep the early economy forgiving enough to survive the learning curve.