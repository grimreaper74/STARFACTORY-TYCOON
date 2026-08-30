# Craft tier ladder — climbing versus sideways (research, v001)

## Provenance

This document was commissioned by the owner through Cowork and delivered as a
four-sheet spreadsheet, `Tier ladder scope.xlsx`, in the owner's Downloads
folder. It was extracted to Markdown on **2026-08-29** and preserved here
because the workbook existed nowhere else and would have been lost to a
tidy-up.

**The spreadsheet is the original artefact; this Markdown is the preserved
one.** Where the two ever disagree, the workbook is the primary source — but
the workbook is not under version control and may not survive, which is why
every number it carried is reproduced below rather than summarised.

The four sheets were `Inputs`, `Counts`, `What comparables do` and
`Recommendation`.

**Authority.** This is an *input* to the owner's decision, not an authority
over him. The research argues a case; it does not settle anything by itself.
What makes the outcome binding is that **the owner accepted the
recommendation on 2026-08-29**: tiers 3–10 ship as Cargo-sized roles, with a
single Large class held in reserve as a late-game capstone. That acceptance is
recorded separately as the standing decision; this document exists so the
reasoning behind it can be re-argued honestly later, including against the
owner, if the measurements turn out to be wrong.

---

## 1. What was decided, and what it supersedes

**Decided (owner, 2026-08-29, accepting the recommendation of sheet 4):** the
craft ladder branches **sideways** rather than climbing. Tiers 3 to 10 are
Cargo-sized craft in different **roles** — survey, interceptor, rescue tender,
tug and so on — differing in the parts they want, their fitting orders and
their customers, not in their size. **One Large class is held in reserve** as
a late-game capstone, to be built only once the roles have proved the game is
fun.

This is the owner's own hybrid instinct, trimmed from three size classes to
two-plus-one-optional.

**What it supersedes.** The pinned pivot record already said the Scout is the
smallest craft and that "stations must be designed to cope with much bigger
craft in later tiers", with "larger station marks as the intended upgrade
path". That framing assumed a climbing ladder. It is superseded for tiers 3–10:
the two marks that exist today are the whole size ladder, and any further mark
should buy **throughput at the same footprint**, not capacity. The
fail-closed per-station craft-capacity envelope itself is *not* superseded —
it stays, and it is what the reserved Large class would eventually move.

It also supersedes, by trimming, the owner's own opening instinct of "two or
three size classes". Two of his three components survived unchanged
(reputation gating, hall-by-adjacent-land); the third was cut to one reserved
step. See §7.

**What it does not touch.** Early access still ships two tiers (Scout and
Cargo). The shared-internals constraint stands and is in fact load-bearing to
the argument. Nothing here changes the FOV-48 camera, the pulse line, or the
one-repeated-station model.

---

## 2. Inputs — measured, derived, and assumed

The workbook labelled its inputs by confidence, and that labelling is the most
important thing to carry through. A figure that is measured can be checked; a
figure that is assumed can be argued with; a figure that is unknown is a
declared hole. Do not flatten these into one list.

### 2.1 Measured from the project — not guessed

| Input | Value | Note as recorded |
|---|---|---|
| Craft tiers shipped | 2 | Scout 14.0 × 7.5 × 3.9 m; Cargo 21.0 × 11.2 × 5.8 m |
| Components per craft | 6 | hull, electronics, power, propulsion, navigation, interior |
| Part definitions | 104 | Shared across all tiers — a settled constraint |
| Raw materials | 9 | |
| Line station families | 4 | |
| Marks per family today | 2 | Mk1 and Mk2 |
| Other buildings | 6 | dock, power, storage, hall, booth… |
| **Station meshes bound** | **32** | The key measured figure — see the ratio below |
| Target tier count | 10 | Intended ladder. Tiers 3–10 are undesigned |

### 2.2 Derived from the measurements

| Derived value | Value | How |
|---|---|---|
| Station definitions today | 8 | 4 families × 2 marks |
| **Meshes per station definition** | **4.0** | 32 bound meshes ÷ 8 definitions |

The 4.0 multiplier is the hinge of the entire model. It says that **every new
station definition costs four meshes**, and it is measured from this project's
own content rather than estimated from industry rules of thumb. Every asset
count downstream is this number multiplied out.

### 2.3 Assumptions — flex these

| Assumption | Value | Confidence as recorded |
|---|---|---|
| Build forms per craft tier | 4 | **MEASURED.** chassis / airframe / fitted / complete — four whole-hull meshes swapped as the craft moves down the line |
| Per-component externals | 0 | **MEASURED.** Components are never modelled on the hull; they exist only as inventory items with crate meshes |
| LOD levels per build form | 1 | **UNKNOWN — the one figure still unmeasured** |
| Hall variants, climbing | 10 | Climbing re-models the hall at each size step |
| Gantry crane marks, climbing | 10 | |
| Size classes, hybrid | 3 | Small (Scout), Medium (Cargo), Large (one new class) |
| Extra throughput mark, sideways | 1 | A Mk3 for **speed**, not a size mark |

### 2.4 The declared unknown

Whether each build form is authored at multiple LOD levels is the one input
the model could not measure, and it is flagged as such rather than assumed
away. At **1 LOD per form, craft art is 32 meshes**. If each build form is
authored at **3 LODs, craft art triples to 96**, and a ten-tier ladder becomes
materially more expensive under *every* option.

Critically: **this does not change the climbing-versus-sideways differential**,
because the differential is entirely station art either way. What it changes is
whether ten tiers is affordable at all, and it is worth knowing before
committing to ten rather than six.

### 2.5 The historical warning — measured from this project

> The craft envelope was once sized for a hypothetical tier six. The hall had
> to be **180 m square** and the starting line occupied **3.9% of the floor**.
> It was reverted. Building for ships that do not exist made the factory look
> abandoned.

The workbook calls this "the strongest single piece of evidence in the whole
model, because it is a measurement from this game rather than an analogy from
another one." That framing is worth preserving: the comparable-games table in
§4 is broad and consistent, but it is still analogy. The 180 m hall is not.
This project already ran the climbing experiment, saw the result on screen, and
undid it.

---

## 3. The asset counts

These are **new** assets required to reach ten tiers, on top of what exists
today.

| Asset class | CLIMBING | SIDEWAYS | HYBRID | Note as recorded |
|---|---:|---:|---:|---|
| Build-form hull meshes | 32 | 32 | 32 | **Identical in all three**, and the point most easily misread |
| Per-component external models | 0 | 0 | 0 | Zero under every option — measured |
| New station definitions (data, not art) | 32 | 4 | 4 | **The divergence.** Climbing needs a mark per size step; sideways needs none |
| New station meshes | 128 | 16 | 16 | At 4 meshes per definition |
| Hall variants | 9 | 0 | 1 | Sideways grows the hall by buying adjacent land — a system that already exists and works |
| Gantry crane marks | 9 | 0 | 2 | |
| UI icons | 40 | 12 | 12 | One per new station definition plus one per craft |
| **TOTAL NEW ASSETS** | **218** | **60** | **63** | Station definitions are data rows, not art, and are excluded from the total so their meshes are not double-counted |
| Shared cost — identical in all three | 40 | 40 | 40 | Build-form hull meshes plus one UI icon per craft. Unavoidable under every option |
| **DIFFERENTIAL — the part actually being decided** | **178** | **20** | **23** | |

### 3.1 The three ratios

| Ratio | Value |
|---|---:|
| Climbing ÷ sideways, totals | 3.63 |
| **Climbing ÷ sideways, DIFFERENTIAL** | **8.9** |
| Climbing ÷ sideways, station meshes only | 8.0 |

The differential ratio is the honest one, and it is the one to quote. Totals
flatter sideways less than they should because 40 of every option's assets are
shared and unavoidable. **Strip the shared cost out and the decision is 178
assets against 20 — an 8.9× differential, genuinely close to an order of
magnitude.**

Removing the per-component externals (see §6) took the last place a craft-side
saving could have hidden, so **the whole difference is station art**.

Station definitions in the shipped game, were the ladder completed: **40**
under climbing, **12** under sideways, **12** under hybrid.

### 3.2 What sideways costs instead

Sideways is not free. It trades mesh work for balance work:

| Work item | Count |
|---|---:|
| Fitting orders to author | 8 |
| Per-component quantity tables | 48 |
| Contract / customer archetypes | 8 |
| **New part definitions** | **0** |

The zero is a consequence of the already-settled shared-catalogue constraint:
because all tiers draw on the same 104 part definitions, eight new roles need
none. And as the workbook puts it, **balance work is reversible; a modelled
station is not.**

### 3.3 A discrepancy in the source, recorded rather than smoothed over

The `Recommendation` sheet states the differential in prose as "**186 new
assets against 28**". The `Counts` sheet computes **178 against 20**. The two
differ by exactly 8 on each side, and only the `Counts` figures reproduce the
headline **8.9×** ratio the recommendation itself quotes (186 ÷ 28 = 6.6, which
is the *pre-correction* ratio described in §6).

The `Counts` figures are therefore the live ones and the recommendation's prose
appears to carry a stale pair from the earlier pass. Both are recorded here
because a preserved document that silently picks one has thrown away the
evidence that the model was revised.

---

## 4. What comparable games actually do

This was the broadest evidence gathered, and the workbook's own summary of it
is blunt: **across every factory game checked, building footprint tracks INPUT
ARITY, never product size.**

| Game | Product gets physically bigger? | Bigger station tiers to buy? | What carries progression instead |
|---|---|---|---|
| **Production Line** | No — body styles are market variants; components are deliberately body-agnostic | No. Research **subdivides** one slot into several, each faster | Task subdivision (which consumes floor space), per-slot robot upgrades, feature research on a rarity clock, vertical integration, buying adjacent lots |
| **Car Manufacture** | Not found. Complexity rises (more assembly steps), not size | No evidence. Scale by more stations (≤20 per line) and more lines | Research unlocking ~60 models, labour-to-robot automation, worker levels, logistics, pricing and brand |
| **Automation** | Bodies have real dimensions but are gated by **era**, not earned by scale | **Yes** — Small/Medium/Large factory tiers. But gated by **materials tech** (steel presses need Medium+), not by car size | Calendar tech unlocks, techpool R&D, engineering vs factory automation, factory portfolio and shifts. No floor layout at all |
| **Factorio** | No — abstract items; 8 per belt tile regardless of item | No. Assembling machine 1/2/3 are **all 3×3** at 0.5 / 0.75 / 1.25 speed | Speed multipliers, module slots 0/2/4, beacons, quality tiers, infinite productivity research |
| **Satisfactory** | 3D meshes but uniform ~1.186 m of belt per item, any item | **No production tiers at all.** Miner Mk1/2/3 identical dimensions at 60 / 120 / 240 per min | Overclocking to 250%, Somersloops, conveyor Mk1–6, alternate recipes, milestone tree |
| **Shapez / Shapez 2** | Shape complexity is semantic — one belt slot regardless | None. Upgrades are **global and retroactive**, bought at the hub | Global speed multipliers, unlocking new operations, platform space budget |
| **Dyson Sphere Program** | No — abstract | Assembler Mk1/2/3 at 0.75 / 1.0 / 1.5 speed, same 3×3 (*inferred — wikis unreachable*) | Proliferator spray, belt and sorter tiers, infinite research, Dyson sphere power scale |
| **Captain of Industry** | **Yes** — loose material has real volume and density | No for production: Assembly I to V are **all 6×5 tiles** at 10× power. **Yes for storage**: 5×5 to 10×10 | Throughput multipliers, the three-tier Maintenance system requiring whole new supply chains |
| **FOUNDRY** | No | **Yes** — Advanced Smelter needs 3×3 instead of 2×2 for 1.5× speed | Players call this out as a **bad trade**: 2.25× area for 1.5× speed reads as a density downgrade |

Two entries carry explicit confidence caveats and those caveats must survive:
the Dyson Sphere Program row is **inferred** because the wikis were unreachable,
and the Car Manufacture row records "not found" and "no evidence" rather than
"no" — an absence of evidence, honestly labelled.

Note what the table does *not* say. Two games do gate on facility size —
Automation and Captain of Industry's storage — but neither gates on **product
size**. Automation gates on materials technology; Captain of Industry gates
production not at all and storage on volume held. FOUNDRY is the one case that
approximates the climbing proposal, and its own players describe it as a
downgrade.

### 4.1 The decisive quote

Satisfactory had Mk.2 variants of the Constructor, Assembler, Foundry,
Manufacturer and Smelter in closed alpha, and **cut them**. The documented
reason:

> "These buildings weren't introduced because Coffee Stain felt they would need
> unique designs, which takes a lot of work just for them to be the same but
> faster, especially with overclocking available."

A studio with Coffee Stain's resources looked at exactly this decision and
concluded the art cost was not worth it — and replaced the tier with a stat
dial.

**Sourcing caveat, as recorded:** community wiki, uncited. Treat as
well-established rather than verified first-party. It is quoted here at the
weight the source gave it, no higher.

---

## 5. Where size-gating *does* work — the five conditions

The research did not conclude that size-gating is always wrong. It identified
five conditions under which it becomes a real decision rather than a toll, each
with a worked example from a game that meets it.

1. **Over-provisioning must carry an ONGOING cost, not just a purchase price.**
   Airport CEO's Large runway costs **$3,333/hr** against a Small runway's
   **$300/hr**, and **6 ramp agents against 2**. That is what keeps "small" a
   permanently valid choice instead of a stage you graduate from.

2. **The upgrade needs LEAD TIME, not just cost.** Rule the Waves 3 grows docks
   **1,000–2,000 tons per year**, which turns the gate into a forecast: you
   decide today what hull you will want in five years, and being wrong is a
   real loss.

3. **Mixed sizes must COEXIST with explicit allocation.** Airport CEO lets each
   stand toggle which sizes it accepts, so the question stops being "have I
   upgraded?" and becomes "who gets the scarce big slot right now?" — a
   scheduling problem that never resolves.

4. **The bigger facility should demand a DIFFERENT KIND of infrastructure, not
   a bigger rectangle.** Large stands in Airport CEO drag in international
   zoning, passport control and second-floor jetways. Compare KSP, where
   lifting the mass cap changes nothing about how anything connects.

5. **Prefer a SOFT penalty over a hard block.** OpenTTD gives small airports a
   **5% crash chance per landing** rather than refusing big planes, so running
   undersized infrastructure stays a knowing risk-for-cash bet.

### 5.1 The warning case

Kerbal Space Program's career mode **fails all five** and is the closest
analogue to naive climbing. The sharpest community observation, offered against
the idea of adding *more* tiers to make the progression feel gradual:

> "You still want specific things at specific times and if you need the
> building to be level 4 to do that specific thing, you're going to upgrade it
> right to level 4 and not really care about levels 2 and 3."

More tiers does not equal more decision. The workbook adds a second observation
that is easy to miss and worth keeping: the complaints attach to the **funds
grind** rather than to the limit itself — "which is exactly what a toll feels
like from the inside."

---

## 6. The self-correction — what changed between passes, and why

The workbook contains an explicit revision note, and it is the most useful part
of the document because it shows the model being argued against and getting
*firmer* rather than being quietly tuned toward its conclusion.

**The earlier version of the model assumed four externally visible components
re-modelled per hull.** The real structure is **four whole-hull build forms per
tier and zero per-component externals**. Components are inventory items with
crate meshes; nothing on a hull is per-component.

The arithmetic landed in the same place — the same 32 craft meshes, reached a
different way — so the totals stood. **What changed was the reasoning.**
Because nothing on a hull is per-component, a role variant costs *exactly* what
a size variant costs, and there is no craft-side saving hiding inside climbing.

The differential moved from **6.6× to 8.9×**, and the case against climbing got
firmer, not weaker.

A second correction sits in the recommendation itself: the owner's instinct of
**three size classes was trimmed to one reserved class** (§7), and the
recommendation is equally explicit that **pure sideways was also rejected**
(§7.2). The delivered call is neither of the two options the model was set up
to compare.

---

## 7. The recommendation, as written

### 7.1 The call

> **Sideways, with ONE size step reserved — not three.** Ship tiers 3–10 as
> Cargo-sized roles: survey, interceptor, rescue tender, tug, and so on. Hold a
> single Large class in reserve as a late-game capstone, and only build it once
> the roles have proven the game is fun. That is your hybrid instinct, trimmed
> from three size classes to two-plus-one-optional.

### 7.2 Why not pure climbing — three reasons, in descending order of confidence

1. **The reverted 180 m hall** is direct measured evidence from *this* game
   that building for ships which do not exist makes the factory read as
   abandoned. No analogy needed.
2. **The differential cost.** (The recommendation sheet states this as 186
   against 28; the `Counts` sheet computes 178 against 20 — see §3.3.) Either
   way, **128 of the climbing assets are station meshes**, the most expensive
   class in the project.
3. **No comparable factory game ties station footprint to product size**, and
   the one studio that seriously tried — Coffee Stain — cut it for art cost and
   replaced it with a stat dial.

### 7.3 Why not pure sideways either

Sideways gives up the one thing climbing genuinely buys: the "look what I can
build now" moment. **Eight Cargo-sized craft with different silhouettes is a
catalogue, not a ladder.** One reserved size step at the very top preserves the
spectacle at roughly a tenth of climbing's differential cost, and it lands when
the player has a full factory to fill rather than an empty one.

### 7.4 Is there a climbing that is a real decision?

Yes — but it is a different game from the one being built. It requires the five
conditions of §5, most importantly that big stations carry an **ongoing cost**
so small stays valid, and that mixed sizes coexist so the player allocates
scarce big capacity.

**This economy currently has no running costs at all**, which means condition 1
is unavailable today: a bigger mark would be strictly better the moment it is
bought. That is the definition of a tax with extra steps, and it is why
climbing as specced would land as a toll.

This is a conditional, not a permanent verdict. If running costs are ever
added, condition 1 becomes available and the question is worth re-opening —
against these same numbers.

### 7.5 Testing the owner's instinct

The owner's three components were: two or three size classes; reputation gating
big contracts; the hall growing by adjacent land. The research kept two
unchanged and trimmed the first.

- **Reputation gating is RIGHT**, and is named the strongest part of the
  instinct: it gates on something the player **earns through play** rather than
  something they buy, which is the difference between a decision and a toll.
- **Hall-by-adjacent-land is RIGHT** and matches Production Line, where task
  subdivision consuming floor space is the central tension.
- **Three size classes is one too many.** With no running costs the middle
  class is dominated the instant it is affordable, and the KSP quote applies
  directly — players will skip to the class that unlocks what they want.

### 7.6 What not to do

- Do not build station marks for tiers that do not exist.
- Do not add a Mk3 **size** mark speculatively.
- Do not size the craft envelope for tier ten — that experiment was already run
  and reverted.
- Do not add per-tier internal parts. This was already ruled out and the
  research supports it: Production Line's designer made components deliberately
  body-agnostic, and his documented regret was about **stockpile ambiguity when
  mixing designs**, not about lacking per-body parts.
- Do not treat the two remaining marks as a size ladder — make Mk2 a
  **throughput** upgrade at the same footprint, which is what every game checked
  actually does.

---

## 8. What sideways does NOT save

The workbook asks for this to be said out loud whenever the decision is
restated, because it is the easiest thing to get wrong. Reproduced at full
weight:

> **Sideways is cheap on STATION art, not on ships.** Every one of tiers 3–10
> still needs its own four build forms, because a survey ship and an
> interceptor must not share a silhouette. Craft art is **32 meshes either
> way**. "Sideways is cheaper" must never be heard as "sideways needs fewer
> ships" — it needs exactly as many; they just do not need bigger stations to
> build them.

The `Counts` sheet makes the same point structurally: build-form hull meshes
are **32 under all three options**, and the shared cost of **40** is identical
under all three. Sideways does not reduce it.

Alongside this sits the second thing sideways does not save: **48
per-component quantity tables, 8 fitting orders and 8 contract archetypes**
(§3.2). The saving is real and it is 8.9×, but it is a saving in *art*, paid
for partly in *data*.

---

## 9. Cross-checks against the code

The following were verified in the source on 2026-08-29 and are stated only
where they were actually checked. Nothing here is claimed as implemented on the
strength of the spreadsheet alone.

**Confirmed — six components per craft.** `ELBSpacecraftComponent` enumerates
exactly Hull, Electronics, Power, Propulsion, Navigation, Interior, with a
comment recording that piece-by-piece customisation is deliberately out of
scope.
`Source/LineBossCarFactory/LBSpacecraftProductionTypes.h:37`

**Confirmed — four whole-hull build forms, authored per tier.** The WIP
presentation actor documents the chain "Crate → Chassis (Hull Fabrication) →
Airframe (Component Fabrication) → Fitted, all but the canopy (Assembly
Staging)" and holds a separate mesh slot per form.
`Source/LineBossCarFactory/LBSpacecraftWIPPresentationActor.h:71-82`
A parallel Cargo set (`CargoChassisMesh`, `CargoAirframeMesh`,
`CargoFittedMesh`) confirms the forms are authored **per tier**, which is the
structural fact behind "32 meshes either way".
`Source/LineBossCarFactory/LBSpacecraftWIPPresentationActor.h:596-607`

**Confirmed — the station definition already carries both levers.**
`FLBSpacecraftStationDefinition` has a `MaxCraftEnvelopeCm` field (the
size-gate) and a `CraftSpeedMultiplier` field (the throughput dial), so
§7.6's "make Mk2 a throughput upgrade at the same footprint" is expressible in
the existing data shape without new code.
`Source/LineBossCarFactory/LBSpacecraftBuildAuthority.h:44` and `:89`

**Confirmed — today's Mk1/Mk2 pair is exactly a two-step size ladder, sized to
the two shipped tiers.** The line station `AssemblyRobot` declares
`MaxCraftEnvelopeCm` of **1600 × 900 × 500 cm** and `AssemblyRobotMk2` declares
**2400 × 1400 × 700 cm**. The Scout (1400 × 746 × 387 cm) fits the first; the
Cargo (2100 × 1120 × 580 cm) fits only the second.
`Source/LineBossCarFactory/LBSpacecraftBuildAuthority.cpp:68-82` and `:170-184`
This corroborates the `Inputs` sheet's "marks per family today = 2" and shows
the decision's practical content: that ladder now **stops here** for tiers
3–10.

**Confirmed — a gap against §7.6, worth acting on.** The line Mk2 marks grow
both footprint (1800×1400 → 2700×2100 cm) and craft envelope, but leave
`CraftSpeedMultiplier` at its 1.0 default: today the line Mk2 buys **capacity
and floor area, no speed**. Separately, the crafting-family Mk2 marks scale
footprint by **1.4 per axis (1.96× area) for a 1.6× speed multiplier**.
`Source/LineBossCarFactory/LBSpacecraftBuildAuthority.cpp:286` and `:292`
That is the same shape as the FOUNDRY trade the comparables table flags as a
player-recognised bad deal (2.25× area for 1.5× speed), slightly less steep.
Recording it here as a measured observation, not a change: no code was modified
by this document.

**Not checked.** The `Inputs` sheet's counts of 104 part definitions, 9 raw
materials, 6 other buildings and — most importantly — **32 bound station
meshes** were not independently re-audited. The 32 is the figure the whole
4.0-meshes-per-definition multiplier rests on, so anyone re-opening this
decision should re-count it first. The catalogue is built from literal tables
in `LBSpacecraftBuildAuthority.cpp` and the count has moved before: a code
comment there records that the four car-shaped line families became one
repeated station type on the owner's 2026-08-27 instruction, with the other
three retained only as `bLegacyHidden` entries so old saves resolve
(`Source/LineBossCarFactory/LBSpacecraftBuildAuthority.h:63-67`). The
spreadsheet's "4 line station families × 2 marks = 8 definitions" counts those
legacy entries. That does not change the ratio — the meshes exist and are bound
either way — but it means the *player-visible* catalogue is smaller than the
input row suggests, and a re-audit should say which it is counting.

**The LOD question (§2.4) remains open and is the single most valuable thing to
measure next.** It does not change this decision. It changes whether ten tiers
is the right target at all, rather than six.

---

## 10. How to use this document

- Quote the **8.9× differential**, not the 3.63× on totals. The totals ratio
  understates the decision because 40 assets are shared and unavoidable.
- Restate §8 every time the decision is restated. Sideways is cheap on
  stations, not on ships.
- If someone proposes a Mk3, ask whether it is a **size** mark or a
  **throughput** mark. Throughput at the same footprint is consistent with this
  decision; a third size class is what was explicitly trimmed.
- If running costs are ever added to the economy, condition 1 of §5 becomes
  available and climbing is worth re-arguing — against these numbers, with the
  station mesh count re-audited first.
- The reserved Large class is **held, not cancelled**. It is a late-game
  capstone, to be built once the roles have proved the loop is fun.
