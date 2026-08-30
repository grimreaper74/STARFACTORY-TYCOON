# Economy calibration from Production Line's shipped data (v001)

Method: read-only mine of the installed game's CSVs (2026-08-26), four
domain analysts + a calibration synthesis. Raw agent returns in the
session workflow journal (wf_50511bc6-34f). PROVISIONAL Line Boss
numbers should be retuned against this; final calls are the owner's.

## Calibration memo (synthesis)

# Line Boss Economy Calibration Memo
**Against:** Production Line (Positech) shipped data — resources.csv, tasks.csv, research.csv, mission/tutorial files
**Status of numbers below:** recommendations for the provisional economy; owner retunes final values.

---

## 1. Where our ratios diverge suspiciously

### 1a. Starting capital vs first-line cost — **broken, fix first**

| | Production Line | Line Boss (provisional) |
|---|---|---|
| Starting capital | $1,300,000 | 600,000 cr |
| First working line | ~$840,000 | ~580,000 cr (5 stations ~405k + power plant 150k + storage 20k + belts ~5k) |
| Line as % of capital | **~65%** | **~97%** |
| Cushion after building | ~$460k (35%) | ~20k cr (3%) |

PL's design leaves a visible-but-finite cushion so the player survives their first mistakes, with loans as the deliberate stress lever. Ours leaves nothing — one mispurchase and the run is dead before the first delivery.

**Change:** starting capital **600,000 → 900,000 cr** (1.5× the costed slice line, exactly the derivation PL implies). Alternative if 600k is sacred: cut the power plant to 90k and the station band to 35k–90k so the line lands ~400k. Do not do both.

### 1b. Import markup — **2.5× is far too fat**

PL keeps import prices within ~5% of the sub-part basket, and chain steps at +30% to 2.6× per processing step. Local manufacture wins on throughput, logistics and research — never on fat arbitrage. Our 2.5× markup means importing is a trap the moment on-site production exists, which kills it as a real ongoing choice.

**Change:** import markup **2.5× → 1.3×** (band 1.2–1.4×). Keep the 450–2,600 cr import stickers and redefine on-site cost as import ÷ 1.3 (≈350–2,000 cr). Deliberately do NOT go to PL's 1.05×: PL's local-make advantage is throughput at thousands of units, which our one-ship cadence can't leverage — we need ~25–30% arbitrage to justify the make-station capex at 15–20 ships/hour.

### 1c. Margin per product — likely 2–4× too generous

PL anchor: bare car sells at **1.92×** its parts bill ($16,360 vs $8,526); researched features earn 2–5× their part cost on top. If a Scout's imported sub-part basket is ~10,000–15,000 cr (15 parts, 450–2,600 band), the 50,000 cr contract is a **3.3–5× margin** — and 8×+ once parts are made on-site at the current 2.5× markup.

**Change:** hold the 50,000 cr Scout contract as the anchor and deepen the recipe until the **imported parts basket ≈ 25,000 cr** (2.0×). Deepening quantities is on-theme — more parts flowing means more visible making. Cargo: basket target ~55,000 cr against the 120,000 cr contract (2.2× — tier steps may widen margin slightly; PL's price-band steps are 1.8–2.8×, so Cargo at 2.4× Scout is fine, keep it). Widen margin further only through researched optional modules (the feature-value 2–5× pattern), never on the bare hull.

### 1d. Station capex vs product revenue — mostly fine, one note

PL: one station ≈ 1.0× one product's revenue, ≈ 2× one parts basket. Ours: 45k–120k stations vs 50k Scout revenue = 0.9–2.4× — in range. With the fixes above (25k margin/Scout), the 580k line pays back in ~23 ships ≈ 70 minutes at one-per-3-min. Good arc; PL's is 108 cars, and we should be much faster in event-count (see §3).

### 1e. Belts at 8 cr/m — economically invisible

PL conveyors cost 7% of a station per tile; ~25 tiles of the first line cost $30k (~2 stations' worth). Layout efficiency has a price. Our 8 cr/m makes 100 m of belt cost 1.6% of one cheap station — routing is free, so sprawl is free.

**Change:** belts **8 → 200 cr/m** (a typical 30 m inter-station run ≈ 6,000 cr ≈ 7% of a mid station, matching PL's ratio). Add a priced logistics-intelligence tier: splitter/merger/router at **~30,000 cr** — PL prices smart junctions at 2× a fit station; routing brains being expensive is a deliberate, copyable choice.

### 1f. Raw materials 40–120 cr — too flat

PL raws span 28–2,600 (93×), median 254, and raw-vs-manufactured is NOT a price tier — premium raws out-price finished parts. Our 3× span makes all materials feel identical.

**Change:** keep bulk structurals at 30–120 cr, add mid raws at 200–500 cr, and 1–2 premium raws (exotic alloy, fusion-cell precursor) at **800–2,000 cr** — priced above the cheapest sub-parts, which is correct and reads as exotic.

### 1g. Sub-part price distribution — no cheap tail

PL: half the catalogue under 200, median 211, heavy right-skew; the expensive tail comes from upgrade variants (2×–52× within one slot), not from every part being mid-priced. Our 450–2,600 band (5.8× span) has no cheap structural filler and no premium tail.

**Change:** redistribute the 15 parts right-skewed — ~8 parts at 150–700 cr, ~5 at 700–1,500, 2 at 2,000–2,600. Get future top-end from **Mk2/Mk3 variant ladders of existing slots** (2–6× base per ladder), and discount researched combined variants 30–40% below the sum of their donors.

### 1h. Research pacing — 5 nodes is a placeholder, and delivery milestones need rescaling

PL ships 211 nodes (400–28,500 cost, ~1.5–2× per chain step, 828k total points) with sales milestones at 10/250/500 cars. Five nodes is fine for the slice but the schema must be built for hundreds, and PL's milestone magnitudes assume continuous output — at our cadence 250 deliveries is 12+ hours.

**Change (slice):** 5 nodes as one themed chain, geometric costs ~**1.6–1.8× per step** (e.g. 200 / 350 / 600 / 1,000 / 1,700 with ~100 pts per Scout delivery): first node after ~2 deliveries, chain complete ~25–35 cumulative deliveries (~90 min). **Milestones:** craft-delivered gates at **3 / 15 / 40**, not 10/250/500.

### 1i. Expansion bays — flat 150k undersells the moment

150k = 3 Scout contracts ≈ 10 minutes of production for a major footprint unlock. PL's cost curves escalate ~1.5–2× per step within any chain.

**Change:** bays escalate **150k / 300k / 600k**. Each successive bay should be the hero purchase of its era, like PL's 13,800 battery pack against a 211 median.

---

## 2. Structures to copy next

1. **Composite stations that subdivide (the single most reusable structure).** PL's 8 root stations fan into ~113 placeables purely by splitting `[subtasksapplied]` lists down a 5-level tree — a child station is its parent's ini with a subset list; durations live in one CSV row; composites sum children so throughput math never breaks. Author each of our 5 slice departments as a composite holding **3–8 named subtasks now** (~25–30 leaf tasks per craft total, vs PL's 43). Phase-2's ~15 buildings is then the *first split* of the same data, post-EA ~30 the second — PL's own L2 tier (~25 stations) is shipped-playable, and our EA target sits right between their L1 and L2. Zero new content authoring, and the per-task `[subtasksrequired]` DAG maps exactly onto our fail-closed genealogy: a craft missing prerequisites simply cannot be processed.

2. **Research as a wide-shallow forest, sized for 200+.** 30 roots, 85% of nodes within 2 hops, max depth 6, hubs with fan-out 6–8, chain steps 1.5–2×, ~70× total cost spread. Content mix to copy: ~1/3 production capability, ~1/4 **vertical integration** ("make this sub-part in-house instead of importing" — PL's single biggest category at 23%, and it maps one-to-one onto our 15 imported sub-parts), ~1/4 contract-demanded optional modules, remainder passive efficiency. The EA "one research branch" = **25–40 nodes** as 4–6 short chains under one hub. Use PL's sparse cross-link rule: module tech is prerequisite to its own in-house-manufacture node, ~3% of nodes, no more.

3. **Flat class-wide station pricing.** Nearly every PL fit station costs exactly $16,800; differentiation is cycle time and consumed parts, never a price puzzle. Collapse our 45k–120k spread to 2–3 legible price points per class (e.g. all fabrication 60k, all assembly 90k) until tuning data exists.

4. **Slow stages are passive stages.** PL's mega-bottleneck is paint *drying* (24k/28.4k ms — 5× a fit task): the first bottleneck teaches parallelization, not punishes a purchase. Ours: hull curing, systems burn-in, fuel/pressurization as the deliberately slow passive steps.

5. **~Half the catalogue research-locked at start** (PL: 56/109), and difficulty staged by clock onto a *working* factory (defects hour 70, breakdowns hour 200) — the player gets a friction-free window to their first launch.

---

## 3. What NOT to copy — one ship at a time changes the math

1. **The 100-product line payback.** PL's line costs ~98 parts baskets / ~51 cars' revenue and pays back over ~108 cars — correct for a continuous stream, deadly for us. Every ship is an event; payback must stay *countable*: **15–25 ships** ("my 19th ship paid off the factory"), which the §1 numbers land at ~23. Never let a capex item cost more than ~30 deliveries.

2. **The continuous market simulation.** Customer ticks every 4 s, 0.6–1.4× price-acceptance bands, rarity-by-segment matrices, marketing, showrooms — all of it models anonymous demand for thousands of identical units. Contracts *are* our demand model. Bake the 2–5× feature-value math into per-contract premiums for optional modules instead; do not build a price-setting screen.

3. **Percentage defect rates.** PL's 1% base defect rate at hour 70 produces steady rework flow across thousands of cars. At ~15–20 ships/hour, 1% is one defect every 5+ hours — invisible. Make defects **per-ship QA events at ~5–15% probability** modulated by station maintenance, resolved through contract penalties and reputation tiers (already priority #2). One defect should be a scene, not a statistic.

4. **Interchangeable leaf-task durations as a goal.** PL clamps fit tasks to a tight 4,000–6,500 band so specialist stations are swappable line segments under continuous flow. With one craft at a station, cycle-time *asymmetry* is fine and even desirable — it is choreography for the camera. Keep only the passive-slow-stage half of that lesson (§2.4).

5. **Catalogue breadth at launch.** 109 resources / 128 placeables / 211 nodes is PL's *final* state. The owner's ~30 chain items and ~15 buildings for EA is PL's shipped-playable L2 density — do not let genre envy pull the EA build toward the full tree.

6. **Milestone magnitudes.** CARS_SOLD 10/250/500 assumes continuous output; ours are 3/15/40 craft delivered (§1h).

---

## Summary of recommended changes

| Item | Provisional | Recommended |
|---|---|---|
| Starting capital | 600,000 cr | **900,000 cr** (1.5× costed slice line) |
| Import markup over on-site cost | 2.5× | **1.3×** |
| Scout parts basket (imported) | ~10–15k cr (implied) | **~25,000 cr** (contract stays 50k, ratio 2.0×) |
| Cargo parts basket | — | **~55,000 cr** (contract stays 120k) |
| Belts | 8 cr/m | **200 cr/m** |
| Splitter/router | — | **~30,000 cr** |
| Raw materials | 40–120 cr | 30–120 bulk, 200–500 mid, **800–2,000 premium** |
| Sub-part spread | 450–2,600, no skew | Right-skewed: 8 cheap / 5 mid / 2 premium; variants for top end |
| Combined researched parts | — | **30–40% below** donor sum |
| Research (slice) | 5 nodes, unstructured | 5-node chain, **1.6–1.8× cost steps**, done in ~25–35 deliveries |
| Research (EA branch) | — | **25–40 nodes**, forest schema built for 200+ |
| Delivery milestones | — | **3 / 15 / 40** craft |
| Expansion bays | 150k flat | **150k / 300k / 600k** |
| Line payback target | ~11.6× revenue (uncushioned) | **15–25 ships** to breakeven |
| Station pricing | 45k–120k bespoke | **2–3 flat class prices** (e.g. 60k / 90k) |

The one non-negotiable: fix 1a (capital vs line cost) and 1b (import markup) before any playtest — the first makes every run a coin-flip, the second silently deletes the import-vs-make decision the whole materials chain exists to pose.

## Mined domain facts

### Factory-game economy calibration — Production Line (Positech) resources.csv parts/pricing data
- Catalogue size: 109 priced entries in resources.csv (115 lines incl. header and 5 blank separators). 93 typed RES_COMP (components), 16 RES_RAW (raw materials). 56 of 109 are locked=1 (research-gated) at game start, 53 available immediately. 35 entries are variants declaring a parent (11 base families).
- Currency scale: plain integers, no sub-unit precision (displayed as $ in-game). Full range 21 to 13,800 — a ~657x span. Median 211, mean 928, quartiles 89 / 211 / 840 — heavily right-skewed: 51 of 109 items cost under 200, only 14 cost over 2,000.
- Price bands: 0-50: 10 items; 50-100: 20; 100-200: 21; 200-500: 24; 500-1,000: 9; 1,000-2,000: 11; 2,000-5,000: 10; 5,000+: 4.
- Cheapest items: lightbulb 21, glass 28, then a 36 tier (bottomtrim, front/rear arch, front/rear bumper). Most expensive: large_batterypack 13,800, small_batterypack 8,100, shp_electric_powertrain 6,000, shp_powertrain 5,500, super_high_perf_motor 4,800, large_touchscreen 4,520, hybrid_batterypack 4,100, gold_wheels 3,020.
- Raw materials (16): glass 28, steel 40, nickel 56, rubber 64, paint 88, paint_colour 88, cobalt 210, aluminium 240, leather 269, lithium 400, chrome 419, sodiumazide 440, wood 495, leather_nappa 600, battery_cell 1008, battery_module 2600. Raw stats: median 254.5, mean 440, max 2,600 — a 93x span within raws alone.
- Raw vs manufactured is NOT a price tier: component median 211 vs raw median 254.5 (nearly equal); component mean 1,012 vs raw mean 440 (components ~2.3x on average, driven entirely by the premium-tech tail). Basic structural raws are the cheapest things in the game; luxury/EV raws (leather_nappa, battery_cell/module) out-price most finished components.
- Upgrade-variant ladders within one slot (parent field): wheel 133 -> alloy 227 -> five_point 270 -> matte_black 426 -> high_tech 617 -> turbine 1,200 -> gold 3,020 (22.7x base). Seats 475 -> nappa 1,500 -> red 1,800 -> white 2,200 (4.6x). Roof 216 -> sunroof 454 -> panoramic 740 (3.4x). Lights 105 -> LED 145 -> directional_xenon 235 (2.2x). Powertrain family 930 -> stop-start 1,380 -> electric 1,500 -> hybrid 1,950 -> hp 2,650 -> hp_electric 3,000 -> shp 5,500 -> shp_electric 6,000 (6.5x). Steepest ladder: fuel tank 264 -> hybrid_batterypack 4,100 -> small_batterypack 8,100 -> large_batterypack 13,800 (52x base).
- Chain-step pricing visible in the file: steel 40 -> steel_sheet 52 (+30% for one processing step); glass 28 -> window 57 (2x) -> windscreen 211 (7.5x raw); EV chain lithium 400 + cobalt 210 + nickel 56 = 666 input basket -> battery_cell 1,008 (1.5x basket) -> battery_module 2,600 (2.6x a cell); engine_block 60 -> engine_assembly 722 -> powertrain 930, where powertrain's plausible sub-part basket (engine_assembly 722 + transmission 50 + drive shaft 110 = 882) undercuts the finished import by only ~5% (basket composition inferred from names, not stated in this file — the file carries import prices only; local-make economics live in the recipe/slot data elsewhere).
- Combined-feature parts are discounted vs the sum of their donors (combos defined in adjacent resource_combos.txt): heated_and_folding_wing_mirror imports at 110 vs heated 90 + folding 90 = 180 (39% discount); directional_xenon_light 235 vs directional 155 + xenon 185 = 340 (31% discount).
- Pricing style mixes round and charm prices: 99 (chip), 199 (alarm, satnav), 2,099 (ai_chip), 2,980 (super_high_perf_engine), alongside round 300/400/600/1,500 values. One inversion worth noting: raw sodiumazide (440) costs more per delivered unit than the finished airbag it feeds (225) — unit-of-measure per crate, not per consumed part, explains raws priced above their product.
- File schema: token,name,icon,delivery-icon,cost,size,type,parent,locked. Size is 128 for every entry except door panel (166). Silicon (740), copper (400) and magnet (200) are typed RES_COMP despite being materials — the RAW/COMP flag is a logistics/behaviour flag, not a semantic one.

Lessons:
- A shipped factory-management game in this exact niche runs ~110 purchasable items total — Line Boss's Phase-2 target of ~30 chain items is comfortably inside genre norms, and the full post-EA catalogue could double that without exceeding precedent.
- Calibrate price distribution as heavy right-skew: median item near the bottom of the range (211 of a 21-13,800 span), ~half the catalogue under 200, and only ~13% of items above 2,000. The expensive tail is what makes hero purchases feel like events.
- Get the top end from upgrade VARIANTS of existing slots, not new part types: one slot's ladder spans 2x-52x (wheels 133->3,020; battery packs 264->13,800). For Line Boss, premium marks of the same station/part family are the cheap way to add economic depth.
- Do not price raw-vs-manufactured as a tier system — Production Line's raw and component medians are nearly identical (254.5 vs 211). The real price axis is tech/luxury tier. A 'raw' can legitimately cost more than a finished part (sodiumazide 440 vs airbag 225) when units differ.
- Keep per-processing-step margin thin: +30% for steel->sheet, 1.5-2.6x per step in the EV battery chain, and finished-part import only ~5% above its sub-part basket. Local manufacture should win on throughput, logistics and research unlocks, not on fat per-part arbitrage — otherwise importing is never a real choice.
- Discount combined/researched variants ~30-40% below the sum of the two donor parts they merge — this makes research feel like it pays without breaking the ladder.
- Integer-only prices with occasional charm pricing (99/199/2,099) on consumer-gadget items read as deliberate flavour; structural parts use flat round numbers (36, 40, 52). Line Boss's integer-hundredths credits ledger is compatible with this style.
- Roughly half the catalogue (56/109) research-locked at start is a workable default for how much of the economy the player should NOT see on day one.

### Research-tree design calibration — Production Line (Positech car-factory tycoon), base + dlc1 + dlc2 research.csv
- Node count: 222 research nodes total — base game 211, dlc1 (premium doors/supercar) 4, dlc2 (design variety) 7. Files: data/simulation/research/research.csv plus content/dlc1|dlc2/data/simulation/research/research.csv.
- Type split: PROCESS 122 (55%), TECHNOLOGY 72 (32%), DESIGN 28 (13%). Schema per node: token, name, parent, icon, cost, type, unlocks, optional milestone requirement (CARS_SOLD,n), optional ignore_auto_requirements + cross-branch prerequisite.
- Cost distribution: min 400, max 28,500 (71x spread). Mean 3,729; median 2,590; quartiles 1,275 / 2,590 / 4,910; deciles 750, 1099, 2000, 2400, 2590, 3170, 4551, 5240, 7545. Buckets: <1,000: 43 nodes; 1,000-2,499: 66; 2,500-4,999: 61; 5,000-9,999: 39; 10,000+: 13.
- Whole-tree completion cost: 827,894 research points (base-only 731,294). The dearest quartile of nodes costs 459,949 vs 42,885 for the cheapest quartile — a 10.7x aggregate ratio.
- Progression curve by tree depth (mean cost): depth0 3,695 (median only 2,080 — the 5 starter department-specialization roots are 400 each and category headers 400-550), depth1 2,815, depth2 4,236, depth3 4,992, depth4 5,012, depth5 8,000, depth6 15,000. Early real picks are 400-750; midgame clusters at 2,400-5,000; endgame 8,000-28,500.
- Unlock-kind fractions: new stations/production capability ~36% (21 nodes split assembly into specialized station tasks (9.5%), 52 nodes unlock make-your-own-component manufacturing stations (23.4% — the single largest category), 7 unlock facilities like power plant/marketing/research center (3.2%)); installable sellable car features (TECHNOLOGY) 65 nodes (29%); body styles & cosmetic designs (DESIGN) 28 (12.6%); efficiency/named upgrades 20 (9%); passive/implicit upgrades and marketing campaign unlocks 22 (10%); pure category-header gate nodes with no unlock 7 (3%).
- Branching shape: a FOREST of 30 roots, not one tree. Depth distribution 0:30, 1:94, 2:66, 3:25, 4:5, 5:1, 6:1 — max depth 6, 85% of nodes at depth <=2. 124 of 222 nodes (56%) are leaves. Of the 98 parent nodes, 64 have exactly 1 child (short linear chains dominate); fan-out >=6 only at 8 hub nodes, max fan-out 8 (accessories_specialization, convenience_features), then 7 (safety_features, performance_features).
- Longest chain (7 nodes) is the self-driving ladder: driver_assistance 550 -> cruise_control 750 -> adaptive 2,400 -> traffic-aware 3,170 -> autosteering 4,500 -> basic_self_driving 8,000 -> advanced_self_driving 15,000 — a clean geometric ~1.5-2x per step.
- Secondary gating: 7 nodes require sales milestones on top of cost — the five 400-point department specializations need CARS_SOLD 10; export_specialization (4,800) needs 250; rapid_shipping (8,200) needs 500. Six nodes use ignore_auto_requirements with a cross-branch prerequisite: in-house manufacture of a component (PROCESS) requires first researching the feature itself (TECHNOLOGY), e.g. research_manufacture_hp_powertrain requires research_high_perf_engine.
- Cost by type: DESIGN is premium-priced (mean 7,119, median 6,000, range 2,000-21,000); PROCESS mean 3,217 median 2,410 (but holds the single max, 28,500 in-house chip manufacture); TECHNOLOGY mean 3,279 median 2,400 (max 17,200 super-high-perf motor).
- Ten most expensive nodes: chip_manufacture 28,500; scissor_door 21,000 (dlc1); gold_wheels 17,500; super_high_perf_motor 17,200; super_high_perf_engine 15,500; advanced_self_driving 15,000; butterfly_door 12,300 (dlc1); body_sport 12,024; ai_chip_manufacture 12,000; body_supercar 11,800 (dlc1). Cheapest tier (400): the 5 department specializations, morerobots1, improved_efficiency, security_features.
- DLC pricing pattern: dlc1 = 4 aspirational designs at 9,500-21,000 (mean 13,650, all above the base tree's 90th percentile); dlc2 = 7 body-style variants all at a flat 6,000, each parented to its base body style.

Lessons:
- Genre-scale for a shipped factory-management research tree is ~200+ nodes; Production Line ships 211 in base alone. Line Boss's early-access 'one research branch' should be understood as one of ~30 such sub-trees, not the whole system — plan the data schema for hundreds of nodes even if content lands later.
- Shape lesson: wide-and-shallow beats deep. 30 independent roots, 85% of nodes within 2 hops of a root, max depth 6, and 56% leaves. Player agency comes from choosing WHICH short themed chain to push, not from descending one long tree. Hubs with fan-out 6-8 (a category header costing ~10-15% of a normal node) are the organizing device.
- Cost curve lesson: ~70x total spread, tuned in three bands — on-ramp 400-750 (first session), a fat middle where ~57% of nodes sit between 1,000 and 5,000, and a long tail of ~6% aspirational nodes at 10,000-28,500. Within a single chain, each step costs roughly 1.5-2x the previous. Aggregate late-game spend is ~11x early-game spend for the same node count.
- Content-mix lesson: about one-third of all research buys production capability (stations/facilities), one-third buys sellable product features, one-eighth buys cosmetic/design variety, one-fifth buys passive efficiency. The single biggest category (23%) is vertical integration — 'manufacture the component yourself instead of importing it' — which maps directly to Line Boss's materials-to-parts chain: make in-house production of each spacecraft part a researchable upgrade over importing it.
- Dual-currency gating works cheaply: pure research points for most nodes, plus production milestones (cars sold: 10 / 250 / 500) on a handful of spine nodes ties research pace to actually running the factory — for Line Boss, 'craft delivered' milestones on department unlocks would replicate this.
- Cross-branch dependencies are used sparingly (6 of 222 nodes) and always in one pattern: the customer-facing feature tech is prerequisite to its in-house manufacturing tech. Sparingly-used cross-links keep the forest readable while still rewarding broad play.
- Premium/DLC calibration: aspirational cosmetics price at or above the base tree's 90th percentile (9.5k-21k); straightforward variants price flat (all 6,000) just above the base median — cosmetic prestige carries the highest price tags in the whole tree (gold wheels 17,500 vs most stations ~2,400).

### Production Line (Positech, Steam) — car-factory sim data files: task/station catalogue, assembly-line decomposition, and the breadth-via-subdivision model
- tasks.csv has 148 lines but 128 real task rows (# prefixed). Breakdown: 19 logistics (13 conveyor variants, 4 smart junctions, 1 overhead resource conveyor, 2 resource importers), 48 'fit' assembly slots (13 of them zero-time composite parents, 35 timed leaves), 44 'make' component-manufacture slots, 6 paint-stage slots, 5 QA slots (incl. rework), 4 export slots, 2 GUI category folders.
- The fully consolidated line is 8 root stations in fixed order: Chassis -> Body -> Paint -> Engine(fit) -> Accessories -> Electronics -> QA -> Export. Each root is a 'parent' entry with process time 0 and cost 0 in tasks.csv; its real cycle time is the sum of the subtasks it applies.
- Subdivision is data-driven per station ini via two lists: [subtasksapplied] (work this station performs) and [subtasksrequired] (tasks that must already be done on the car — a strict DAG enforcing line order). Example: fit_bonnet REQUIRES fit_rollcage; paint REQUIRES fit_wingmirrors; qa REQUIRES windscreen+aircon+computer.
- Root station subtask loads: Chassis applies 5 (rear axle, front axle, drive shaft, undercarriage, fuel tank), Body applies 13, Engine applies 8, Accessories 6, Paint 4, Electronics 2, QA 3, Export 2 — total ~43 core leaf assembly tasks per car.
- Subdivision tiers via guilevel: L1 = 8 line roots + importer; L2 = ~25 first-split stations (axles, bodyframe, doors, engine assembly, wheel assembly, steering assembly, paint/dry undercoat, paint/dry finish, visual/performance/emissions checks, paperwork, shipping...); L3 = ~40 second-split (front_axle, rear_axle, brakes, wheels, tires, steering column/wheel, rollcage, bonnet, boot, windows... plus most make_ stations); L4 = ~23 third-split (front/rear arch, front/rear bumper, plus most component makers); L5 = 2 deepest (make_engine_block, make_valve feeding make_engine_assembly). A mid-tier station applies a strict subset of its parent: fit_axles applies 3 of Chassis's 5; fit_wheelassembly applies brakes+wheels+tires; a leaf applies exactly 1.
- Subdivision is research-gated: research.csv (211 entries) has e.g. research_chassis_specialization (cost 400, requires CARS_SOLD 10) unlocking 'task_fit axles, task_fuel_tank, task_fit_undercarriage'. All non-root stations ship locked=1.
- Leaf fit-task durations cluster tightly: 35 timed fit tasks, mean 4,980, most in 4,000-6,500. Extremes: fit_controls 900, fit_computer 1,000, fit_cabin 1,100 (fast); fit_steering_wheel 10,000, fit_roof 9,225, fuel_tank 8,200, fit_windscreen 8,000 (slow). So any specialist station has a roughly comparable cycle.
- Composite cycle asymmetry drives subdivision priority: Body sum ~64,900 vs Chassis sum ~26,400. Paint chain is the designed mega-bottleneck: undercoat 7,900 + dry 24,000 + finish 8,500 + dry 28,400 (+polish 7,000) = ~68,800 - drying alone is 2.5-7x a typical fit task.
- Make-station durations span 1,230 (make_bonnet) to 59,300 (make_aircon), mean ~11,700; typical 4,000-18,000; other outliers make_panoramic_sunroof 51,200, make_sunroof 44,000, make_exhaust 22,140. QA checks are uniform and short (3,000-3,700); export: paperwork 5,200, shipping 2,000, rapid shipping 1,500.
- Costs are deliberately flat within a class: nearly every leaf fit slot costs exactly 16,800 (a few 18,200-19,900) with power 165; make stations 18,200-95,000 (typical 36,125-58,200, power 122-400) with one prestige outlier make_chip at 400,000; conveyor 1,200/60W; smart junction 35,000/200W; importers 66,000 and 95,000.
- Footprints scale with consolidation: root fit_chassis = 11 tile sections (~3x4 plus stockpile), mid fit_axles = 5, leaf fit/QA/paint slots = 3 (conveyor tile + stockpile + work tile), make_wheels = 6 (incl. TT_EXPORT output tile). Slot inis also define decorative props (fences, forklifts, employees) per tile.
- Material model: leaf fit slots consume named resources (fit_brakes: brake x4); make slots convert ([resources] steel=2 -> [exports] wheel=2). resources.csv defines 109 resource/component types with unit costs (aerial 55, airbag 225, aircon 480). The deep manufacture chain is only 2-3 levels: engine_block+valve -> engine_assembly -> powertrain -> fit; battery_cell -> battery_module -> small/large battery pack.
- features.csv: 92 feature rows = 15 base/common features (feature_basic_car carries base market value 16,360; the rest are 0-value commons like basic lights/solid roof) + ~77 optional features with market values 165 (antilock brakes) to 26,000 (gold wheels). Each feature has a rarity per price segment (max_cheap/mid/expensive/luxury: UNIVERSAL/COMMON/RARE/VERY_RARE), mutually exclusive categories (CAT_WHEELS, CAT_SUNROOF, CAT_POWERTRAIN, CAT_AUTONOMY...), prerequisites (climate_control requires aircon; large_batterypack requires electric_powertrain & motor tiers), and body-style restrictions (car1..car8).
- Body styles: 7 component folders (car1-car7; features reference a car8). Powertrain breadth handled as features + parallel make stations: ICE, hybrid (make 4,800), electric (make 5,490), plus engine/motor performance tiers worth 4,200-19,500 in market value.

Lessons:
- Breadth-via-subdivision means content scale is mostly the SAME work re-partitioned, not new work: 8 root stages fan out into ~113 placeable production stations (35 leaf fit + 44 make + specialists) purely by splitting composite task lists down a 5-level tree. For Line Boss's ~30-building Phase-2 target, the analogue is designing each spacecraft department as a composite station whose [subtasksapplied]-style list can later split into 2-13 specialist stations without touching the product recipe.
- The split is trivially cheap to author because a station is just (task list, required-task DAG, footprint, cost): a child station's ini differs from its parent only in applying a subset. The per-task duration lives in one CSV row and is inherited everywhere - composites sum their children at runtime, so throughput math stays consistent across every consolidation level.
- Ordering is enforced per-TASK, not per-station ([subtasksrequired] on the car's task checklist), so any physical layout that satisfies the DAG is legal - this is exactly a fail-closed validation pattern: a car arriving without prerequisites simply cannot be processed. Maps directly onto Line Boss's authority/fail-closed architecture and its genealogy checklist per unit.
- Duration calibration: keep leaf tasks in a tight band (here 4,000-6,500, ~7:1 total spread) so specialist stations are interchangeable line segments; make the deliberately slow stages PASSIVE ones (paint drying at 24k/28.4k, 5x a fit task) so the first bottleneck the player meets teaches parallelization/duplication rather than punishing a wrong purchase. The most-consolidated station (Body, ~65k sum) is the tutorialized reason to research subdivision.
- Progression gating of subdivision by output milestones (research 'specialization' nodes unlocked after N cars sold) turns line-scaling itself into the tech tree - Line Boss's one research branch for early access could be exactly this: department-specialization nodes rather than new product content.
- Product variety is a separate cheap axis from station variety: ~77 optional features on a (rarity x price-segment) matrix with market values, exclusivity categories, and prerequisite chains create configuration depth with almost no new stations (features mostly attach to existing slots or single make stations). For spacecraft: contract-demanded optional modules per tier beat authoring new station types.
- Flat class-wide costs (every leaf fit slot 16,800/165W) make the subdivide-or-not decision purely about throughput and floor space, never a price puzzle - a good default for Line Boss station pricing until the economy is tuned.
- Materials chain depth for a full factory game is shallower than it looks: 109 resource types but conversion chains only 2-3 stations deep, with most parts importable OR locally manufacturable (make_x station parented under fit_x in the build menu - vertical integration as an opt-in per part). The owner's ~30-chain-item target matches this scale well.
- Calibration anchor: Production Line's full catalogue is ~128 placeables / 43 core assembly tasks / 109 resources / 92 features / 211 research nodes. Its guilevel-2 tier (~45 stations) is roughly the density the Line Boss Phase-2 wishlist build (~15 buildings, ~30 chain items) is aiming under - i.e. the owner's target sits between Production Line's L1 and L2 consolidation tiers, which the game itself treats as perfectly playable early states.

### Production Line (Positech Games) — data-file economy, tutorial, and scenario calibration
- Starting cash by map (data/missions/*.txt): Small Factory $1,300,000 (60x60 tiles), Medium $1,700,000 (62x62), Tight Budget $1,000,000 (66x66), Detroit $1,250,000 (150x150), Giant $3,000,000 (72x72), Mega $3,000,000 (102x102). The tutorial forces the Small map (tutorial.csv token choose_mission: Disable(ALL_MISSIONS), Enable(mission_small)), so the canonical first-game bankroll is $1.3M.
- Cost of the tutorial's first working line (tasks.csv construction costs; parent slots cost 0 and are the sum of their subtask stations): Chassis 5x16,800=$84,000; Body 13x16,800=$218,400; Paint $63,300 (14,850+16,800+14,850+16,800); Engine $136,800 (19,200 engine-assembly + 7x16,800); Accessories $105,300 (4x16,800 + cabin 19,900 + controls 18,200); Electronics $29,320 (14,920+14,400); QA $47,500 (18,500+17,000+12,000); Export $56,160 (paperwork 23,660 + shipping 32,500). Slots total $740,780; plus ~25 conveyor tiles at $1,200, resource importer $66,000, resource conveyors $1,800/tile — roughly $840k, i.e. ~65% of the $1.3M start, leaving a ~$460k operating cushion (~35%).
- Tutorial structure (data/tutorial.csv): 67 hint tokens total. A guided ~23-step spine — intro x3, zoom, move, basics, slot_button, slot_picker x2, then place 8 slots in fixed order (chassis, body, paint, engine, accessories, electronics, QA, export) each auto-focusing the map and enabling exactly one placeable, then main conveyor, exit conveyor, resource importer x2, resource conveyor, complete_line. The other ~44 tokens are event-triggered one-shot popups taught lazily on first encounter: car design price (WIN_DES_PRICE), car colors, research, loans, imports, power station, marketing, market analysis, scheduler, breakdown/maintenance, defects/rework, efficiency, car stock, demolish, smart junctions, production manager. Verbs taught in the spine: zoom, pan, open picker, place station, chain conveyor, import resources.
- Margin model: a bare default sedan's parts cost $8,526 (resources.csv: chassis group $830 = 2 axles@192 + drive shaft 110 + undercarriage 72 + fuel tank 264; body $2,025 incl. 4 door panels@211, 5 windows@57, roof 216; paint $528 = 6x88; engine $3,505 = powertrain 930 + 4 brakes@153 + 4 wheels@133 + 4 tires@158 + exhaust 300 + radiator 124 + steering 375; accessories $1,638 = 2 seats@475, 4 lights@105, windscreen 211, horn 57). Bare-car market value = $16,360 (features.csv feature_basic_car), giving a base value:parts ratio of 1.92. Customers accept prices 0.6x-1.4x perceived value (simconfig CUST_PRICE_MIN_MULT/MAX); wrong body style multiplies appeal by 0.7.
- Feature economics deepen margin: each installed feature adds marketvalue typically 2-5x its component cost — aircon +$2,537 value vs $480 part; touchscreen +$3,146 vs $1,680; climate control +$1,365 vs $780; electric powertrain +$12,353 vs $1,500-6,000 parts; in-car music +$593 vs ~$150 (speakers). Sales price bands (sales_categories.ini): Cheap from $9,000, Mid from $25,000, Expensive from $45,000, Luxury $100,000-$200,000, with category bonuses +0/+2,000/+4,000/+6,000. Missing an expected 'universal' feature penalises value by 250 each (simconfig).
- Loans and economy pacing (simconfig.txt): loan amounts are exe-hardcoded (no data file), but rules are data: taking a loan while one exists multiplies interest 1.5x, multiple loans 2x, and loans require company value >= $100,000; playguide text warns terms are short and daily interest high by design. Hourly wages: production $48, scientist $98, engineering $104, sales $120, chip-fab $142, marketing $160. One game hour = 120,000 ms; assembly subtasks take 4,000-10,000 ms (~3-8% of an hour); sales tick every 4,000 ms with 2.2 base customers per tick. Defects start at hour 70 (1% base), breakdowns at hour 200, random events at hour 240 — difficulty is staged onto a working factory rather than present from minute one.
- Scenario goals (data/scenarios/*.ini) are 240-360 hour timed targets layered on the same maps: #1 Starting Out (Small map, 360h): 3,000 cars incl. 250 expensive + 750 mid; #2 Mass Market (Medium, 240h): 3,000 cheap cars; #3 High End (Budget map, 240h): 50 luxury cars AND $6M luxury income; #4 Global Production (Giant, 240h): 3,500 cars, 1,000 expensive, 85,000 components produced.
- Station catalogue scale: tasks.csv defines ~130 placeables — 13 conveyor variants ($1,200-$2,700), 4 smart junctions ($35,000-$44,000), ~45 fit stations (mostly $16,800 each, 165 power), ~45 make-component stations ($18,200-$89,000, chip fab $400,000), QA/inspection ($12,000-$18,500), export/shipping ($16,800-$65,900). Specialisation is a split of the same subtasks the combined starter slots already contain (e.g. Fit Body = 13 named subtasks), so the upgrade path is data-shaped as parent->subtask trees, not separate machines.

Lessons:
- Calibrate starting capital so the tutorial-taught first line consumes ~60-70% of it: Production Line gives $1.3M against an ~$840k first line, leaving a visible but finite cushion, with loans (gated and punitive) as the deliberate expansion lever rather than a bigger grant. For Line Boss's money loop, the placeholder starting balance should be derived the same way: cost the five-station slice line first, then set capital at ~1.5x that figure.
- A ~2:1 sale-value to raw-part-cost ratio on the base product is the genre-proven anchor, with option/feature content earning 2-5x its part cost — margin should come from what the player researches and adds, not from the bare hull. For spacecraft contracts: price the bare Scout near 2x its material bill and let recipe upgrades widen margin.
- Teach with a ~20-25 step guided spine that places the entire first line one station at a time in fixed order (each step enables exactly ONE buildable and auto-focuses the camera on the target tiles), then deliver everything else — pricing, loans, research, marketing, maintenance — as one-shot contextual popups triggered by first encounter. 67 total hints but only a third are sequential; the economy screens are never front-loaded.
- Stage difficulty onto an already-working factory by the clock: defects at hour 70, breakdowns at hour 200, market events at hour 240. A new Line Boss player should get a friction-free window to reach their first delivery before failure systems arm.
- Make one assembly station cost ~2 finished products' worth of parts, and the full line ~90-100 products' worth: payback over dozens of sales is what forces the optimise-throughput loop. Also note station cost is flat and legible ($16,800 for almost every fit station) — differentiation comes from process time and consumed parts, not bespoke prices.
- Structure the buildable catalogue as parent slots that are literally the sum of named subtasks (cost = sum of children), so line specialisation is a split of existing data rather than new content — a directly reusable shape for Line Boss's station-upgrade marks and the ~30-building Phase-2 catalogue.
- Timed scenario goals reuse the sandbox maps with 240-360 in-game-hour limits and 2-3 stacked quotas by price tier — a cheap way to multiply content from one factory sim, relevant to Line Boss contract design (quota + tier mix + deadline, not bespoke maps).

