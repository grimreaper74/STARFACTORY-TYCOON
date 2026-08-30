# MRB Concession Balancing Research — second pass, at measured inputs (v002)

## Provenance

This document was commissioned by the owner through Cowork as a balancing study of
the Material Review Board disposition choice — the economics of letting a player
concede a defective craft to a customer at a discount rather than reworking it, and
what the surrounding contract deadlines do to that choice.

The original artefact is a spreadsheet, the second-pass workbook
`MRB_balancing_v2.xlsx`, held in the owner's Downloads folder. Its six sheets —
Inputs, Deadlines, Curves, Break-even, Reputation stress, Recommendation — were
extracted to a faithful text dump on **2026-08-29** and are preserved here. **The
spreadsheet is the original; this Markdown is the preserved copy.** It exists because
the workbook lived only in Downloads and would not have survived a tidy-up. Where the
two disagree, the workbook is the record of what was computed; this document is the
record of what it said and why.

**Authority.** This is research. It is an *input* to the owner's decisions and does
not settle anything by itself. Where a recommendation below is binding, it is binding
because the owner accepted it, and that acceptance is noted explicitly. The owner
accepted the deadline recommendation — the single largest change in the study — and
it is shipped in the runtime today (verified in source, cited below). He did not
adopt the cash late-delivery fee, the concession slope reduction, the proportional
concession reputation cost, or the scrap material recovery; those remain proposals,
and the document says so plainly rather than describing them as done.

This is the **second pass**. The first pass ran on assumed inputs. The second pass
rebuilt the model on measured ones and, in doing so, **reversed three of its own
earlier recommendations**. Those reversals are the most valuable content in this
document and are marked `[REVERSED]` throughout, exactly as the workbook marked them.

---

## 1. What was decided, and what it supersedes

The study's headline finding is not about the concession curve at all. It is that the
contract deadline formula in the source gave a single-craft Scout order **6,200
seconds to complete a 440-second build — 14.1 times the craft's own build time.** The
workbook calls this cell, verbatim, **"THE NUMBER THAT BROKE THE MECHANIC."** At that
much slack no rework can ever threaten a delivery, so "put it right" is always the
right answer, the disposition menu has one correct button, and every coefficient in
the concession curve is decorative.

The recommendation that follows from it, and the one the owner accepted:

> **Deadline allowance = 300 s + 1.0 × pipelined wall-clock**, replacing
> `1800 s + 10 × W × quantity`.

This supersedes the first pass's whole approach in two ways. First, the first pass
tuned the deduction coefficients against the existing deadlines; the second pass
concludes that any tuning done at 5,760 seconds of slack is **fitting noise**, because
every coefficient set produces the same answer there. Second, the first pass replaced
the model's cost-of-a-stall with a single lambda term; the second pass **removes the
single lambda entirely** and replaces it with an explicit **tempo** term (deferred
margin, discounted) plus a **late-delivery** term driven by remaining slack. The
single lambda is gone as a structure, not merely retuned.

The owner accepted the deadline change. He accepted it in the stronger of the two
forms the workbook offered — the pipelined form, not the minimal-change form — and it
is in the shipped runtime. Everything else in this document is still a proposal.

---

## 2. Measured inputs

The workbook's own legend marks each input **MEASURED** or leaves it as a stated
assumption, and flags one figure it could not measure. That distinction is carried
through here unchanged, because it is what allows the study to be re-argued honestly
later.

| Input | Value | Status |
|---|---|---|
| Contract price, Scout | 150,000 cr | **MEASURED** |
| Contract price, Cargo | 360,000 cr | **MEASURED** |
| Material cost per craft, Scout | 28,485 cr | **MEASURED** by walking the bill of materials in-engine, each item priced at the cheaper of make-or-buy |
| Material cost per craft, Cargo | 75,597 cr | **MEASURED**, same method |
| Material share of price, Scout | **19.0%** (0.1899) | **MEASURED** |
| Material share of price, Cargo | **21.0%** | **MEASURED** |
| Margin per craft, Scout | 121,515 cr | Derived. Materials are the only marginal cost — there are no drone wages and no power billing |
| Nominal build time W, Scout | 440 s | **MEASURED** |
| Nominal build time W, Cargo | — | **NOT MEASURED.** The Scout's 440 s is used for both. Flagged in the workbook |
| Bottleneck station cycle | 333 s | **MEASURED** — heaviest station on the unbalanced line |
| Pipelined wall-clock, qty 1 | 440 s | Derived: first craft costs a full build, each subsequent craft costs one bottleneck cycle |
| Margin per second of line time | 364.91 cr/s | Derived (121,515 ÷ 333 — against the **bottleneck cycle**, not against W). Gross rate; explicitly **not** the cost of a stall |
| Credits delivered per reputation point | 75,000 cr | Stated |
| Value of one reputation point | ~6,000 cr | Estimated as ~0.3pp of tier premium per point against remaining lifetime revenue; spiky near thresholds |
| Reputation tier thresholds | Tier 2 at 10, Tier 3 at 25, Tier 4 at 50 | Stated |

### 2.1 The material share, and what it did to everything downstream

**The first pass assumed a 40% material share. The measurement is 19.0% for the Scout
and 21.0% for the Cargo.** This roughly **doubles the margin per craft**, and so
doubles what a second of line time is worth in gross terms.

That single correction is what forces most of the reversals below. When materials are
19% of price, the craft is nearly all margin, rework destroys very little in cash
terms, and the concession curve — which is a *cash* penalty — has to come **down**, not
up, if conceding is to remain competitive with reworking at all. The first pass, at
40% materials, reasoned in the opposite direction on every one of these points.

### 2.2 The cost-of-a-stall model

The workbook is explicit that with no running costs a stall **destroys nothing
directly — it defers revenue**. The old single-lambda formulation charged a stall as
if margin were being burned. The second pass splits it:

- **Tempo discount on deferred margin: 0.10.** The share of deferred margin genuinely
  lost to slower progression. The workbook warns in the cell itself that this term is
  *small by nature* and must not be used to carry the mechanic.
- **Late-delivery fee: 0.0015 of contract price per second late** (0.15%/s), i.e. a
  150-second overrun forfeits 22.5% of the contract. **Cash, not reputation.** New in
  this pass; the current value in source is 0.
- **Late-delivery fee cap: 0.40**, so a catastrophic overrun cannot exceed the craft's
  worth. Current value in source is 0.
- **Late-delivery reputation penalty: recommended DOWN to 1 point** from the current 2.
  Tightening deadlines tenfold while keeping a large reputation penalty is what would
  break progression.

---

## 3. The deadline finding

### 3.1 The formula as it stood, and the minimal-change fix

The workbook first modelled the smallest possible change: keep the shape already in
the source (`base + multiplier × W × qty`) and change only the two numbers, from
`1800 + 10 × W × qty` to `300 + 1.0 × W × qty`.

| Order qty | Pipelined wall-clock | CURRENT allowance | Current ratio to build | Current slack | RECOMMENDED allowance | Recommended ratio | RECOMMENDED slack |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 440 | 6,200 | 14.09× | 5,760 | 740 | 1.68× | 300 |
| 2 | 773 | 10,600 | 12.05× | 9,827 | 1,180 | 1.34× | 407 |
| 3 | 1,106 | 15,000 | 11.36× | 13,894 | 1,620 | 1.23× | 514 |
| 4 | 1,439 | 19,400 | 11.02× | 17,961 | 2,060 | 1.17× | 621 |
| 6 | 2,105 | 28,200 | 10.68× | 26,095 | 2,940 | 1.11× | 835 |
| 8 | 2,771 | 37,000 | 10.51× | 34,229 | 3,820 | 1.09× | 1,049 |

The current column is the number that broke the mechanic, measured across the range:
**14.1× at qty 1, 12.0× at qty 2, 11.0× at qty 4** and never dropping below 10.5×.

### 3.2 Why the minimal change is not good enough

The table above exposes its own flaw. Because the multiplier applies to **per-unit
work** while the line actually runs **pipelined**, slack *grows with order size* — 300 s
at qty 1 but **1,049 s at qty 8**. A 540-second rework can never breach that, so the
mechanic quietly dies on bulk orders even after the fix.

Scaling the allowance on **pipelined wall-clock** instead holds slack constant at
every quantity:

| Order qty | Pipelined wall-clock | PREFERRED allowance | Ratio to pipelined | SLACK | Ratio to W × qty |
|---:|---:|---:|---:|---:|---:|
| 1 | 440 | 740 | 1.68× | 300 | 1.68 |
| 2 | 773 | 1,073 | 1.39× | 300 | 1.22 |
| 3 | 1,106 | 1,406 | 1.27× | 300 | 1.07 |
| 4 | 1,439 | 1,739 | 1.21× | 300 | 0.99 |
| 6 | 2,105 | 2,405 | 1.14× | 300 | 0.91 |
| 8 | 2,771 | 3,071 | 1.11× | 300 | 0.87 |

> **PREFERRED FORMULA: allowance = 300 + 1.0 × pipelined wall-clock.** Slack is a
> constant 300 s at every order size, so the disposition choice behaves identically on
> a single Scout and an eight-craft run, and the rework that breaches the deadline is
> always the same one (4 defect points and up). It needs the runtime to know the
> pipelined time rather than per-unit work — slightly more plumbing, materially better
> behaviour.

### 3.3 The binding constraint, and why 300 s

For the disposition choice to exist at all, **the largest rework must be able to
exceed remaining slack.** Otherwise no rework ever threatens a deadline, rework is
free at every defect count, and the menu has one right answer. With rework at 90 s per
defect the worst case is 540 s, so slack has to sit somewhere near **200–350 s**. That
is what pins the recommended base to about 300 s, and the workbook is candid that it
is **a genuinely tight design corridor**: much more slack and the mechanic dies, much
less and ordinary variance makes the player late.

| Rework curve | d=1 | d=2 | d=3 | d=4 | d=5 | d=6 | vs recommended slack |
|---|---:|---:|---:|---:|---:|---:|---|
| 90d, min 120 (owner's original, and recommended) | 120 | 180 | 270 | 360 | 450 | 540 | breaches slack — OK |
| 120 + 20d (pass-1 recommendation) | 140 | 160 | 180 | 200 | 220 | 240 | **never breaches — mechanic dead** |
| 60 + 60d | 120 | 180 | 240 | 300 | 360 | 420 | breaches slack — OK |

---

## 4. The curves at measured inputs

The comparison that matters is the concession **premium over the sunk failed-test
deduction**, against the cost of a rework at the current slack. The sunk failed-test
deduction (f = 0.10 for one recorded failure) is paid whether or not the player
reworks; a concession **replaces** it rather than stacking on it.

Computed on the recommended parameter set (concession 8 + 4d clamped 8–45%; rework 90d
min 120 s; tempo 0.10; late fee 0.15%/s capped at 40%), on a Scout at 300 s of slack:

| Defect points | Concession deduction | Premium over sunk | Total cost of conceding (cr) | Rework time (s) | Seconds late | Late fee (cr) | Total cost of reworking (cr) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.12 | 0.02 | 9,240 | 120 | 0 | 0 | 4,379 |
| 2 | 0.16 | 0.06 | 18,720 | 180 | 0 | 0 | 6,568 |
| 3 | 0.20 | 0.10 | 28,200 | 270 | 0 | 0 | 9,853 |
| 4 | 0.24 | 0.14 | 37,680 | 360 | 60 | 13,500 | 26,637 |
| 5 | 0.28 | 0.18 | 47,160 | 450 | 150 | 33,750 | 50,171 |
| 6 | 0.32 | 0.22 | 56,640 | 540 | 240 | 54,000 | 73,705 |
| 7 | 0.36 | 0.26 | 66,120 | 630 | 330 | 60,000 (capped) | 82,989 |
| 8 | 0.40 | 0.30 | 75,600 | 720 | 420 | 60,000 (capped) | 86,274 |
| 9 | 0.44 | 0.34 | 85,080 | 810 | 510 | 60,000 (capped) | 89,558 |
| 10 | 0.45 (clamped) | 0.35 | 89,700 | 900 | 600 | 60,000 (capped) | 92,842 |

Two structural notes on how those columns are built, both of which reproduce the
workbook's arithmetic exactly and are worth recording because they are what makes the
model auditable:

- **Cost of reworking = tempo × margin-per-second × rework seconds, plus the late
  fee.** At d=1 that is 0.10 × 364.91 × 120 = 4,378.92 cr. The late fee appears only
  once the rework exceeds the 300 s slack, and the cap bites at d=7 where 330 s late
  would otherwise cost 74,250 cr against the 60,000 cr ceiling (40% of 150,000).
- **Cost of conceding = the cash premium, plus the reputation charged for the
  concession, plus the reputation lost because the discounted delivery earns less
  name.** That third term is why the concession column is slightly steeper than the
  cash discount alone: a 150,000 cr Scout is worth 2 reputation points at 75,000 cr a
  point, so every point of discount also shaves the reputation earned on delivery.

---

## 5. Break-even by remaining slack

**Slack, not defect count, is the primary variable.** Each column is a different
amount of deadline headroom; each row a defect count. This is the table to read when
deciding whether the mechanic is worth keeping.

| Defect points | 5,760 s (current deadlines) | 800 s | 500 s | 350 s | 300 s | 200 s | 120 s | 60 s |
|---:|---|---|---|---|---|---|---|---|
| 1 | rework | rework | rework | rework | rework | rework | rework | **CONCEDE** |
| 2 | rework | rework | rework | rework | rework | rework | **CONCEDE** | **CONCEDE** |
| 3 | rework | rework | rework | rework | rework | rework | **CONCEDE** | **CONCEDE** |
| 4 | rework | rework | rework | rework | rework | **CONCEDE** | **CONCEDE** | **CONCEDE** |
| 5 | rework | rework | rework | rework | **CONCEDE** | **CONCEDE** | **CONCEDE** | **CONCEDE** |
| 6 | rework | rework | rework | **CONCEDE** | **CONCEDE** | **CONCEDE** | **CONCEDE** | **CONCEDE** |
| **Crossover** | 0 | 0 | 0 | 1 | 2 | 3 | 5 | 6 |

The leftmost column is the game as it stood: **5,760 s of slack on a single-craft
Scout order, and nothing in the defect range flips it.** The mechanic does not begin
to breathe until slack falls under roughly 500 s, and it is only genuinely live
between about **350 s and 100 s**. The workbook states without hedging that this band
is narrow, and that this is the honest case both *for* and *against* keeping the
mechanic.

---

## 6. Reputation stress: does a tenfold deadline tightening break progression?

Reputation earns from delivered value at 1 point per 75,000 cr, so a Scout pays about
1.8–2.0 points. The question is whether a higher late rate can outrun that. Figures
are **means of 200 simulated runs**.

| Scenario | Late rate | Rep penalty per late | Contracts | Reputation reached | Tier |
|---|---:|---:|---:|---:|---|
| Healthy line, deadlines tight | 0 | 2 | 60 | 90.8 | Tier 4 |
| Occasional overrun | 0.15 | 2 | 60 | 72.6 | Tier 4 |
| Occasional overrun, harsh penalty | 0.15 | 5 | 60 | 47.2 | Tier 3 |
| Struggling | 0.30 | 2 | 60 | 54.3 | Tier 4 |
| Struggling, harsh penalty | 0.30 | 5 | 60 | 15.2 | Tier 2 |
| Badly struggling | 0.50 | 2 | 60 | 32.3 | Tier 3 |
| Badly struggling, harsh penalty | 0.50 | 5 | 60 | 2.6 | Tier 1 |
| **EARLY GAME — unbalanced line** | 0.50 | 2 | **12** | **7.7** | **Tier 1** |
| **EARLY GAME — harsh penalty** | 0.50 | 5 | **12** | **2.3** | **Tier 1** |
| **EARLY GAME — very unbalanced** | 0.70 | 5 | **12** | **0.8** | **Tier 1** |

**Verdict.** The long run is safe. Delivered value earns roughly 2 points per Scout,
which comfortably outruns a 2-point penalty even at a 30% late rate — a player late on
a third of their contracts still reaches Tier 4 over 60 contracts. The owner's
instinct that tightening deadlines tenfold might collapse reputation is **right in
shape but wrong in magnitude: the earn rate dominates.**

The real risk is **the opening, not the economy**. Over the first dozen contracts, on
the unbalanced starter line, a player late half the time sits near zero and never
reaches Tier 2 — so they never see the 5% tier premium, which slows them further. That
is a soft-lock in feel if not in mechanics.

Three mitigations, in the workbook's order of preference:

1. **Make the late penalty cash and keep reputation for quality.** Lateness is a tempo
   failure; shoddiness is a trust failure. Collapsing both onto one meter is what
   creates the coupling the owner was worried about.
2. **Scale the allowance multiplier by contract tier** — generous on Scout while the
   player is learning, tight on Cargo and above once they have a working line.
3. **If reputation must carry a late penalty, drop it to 1 point, not 2.**

---

## 7. Coefficient-by-coefficient recommendations

Every coefficient with its recommended value and the reasoning, including the ones
deliberately left **unchanged from the owner's original because the first pass had
been wrong to move them.**

| Parameter | Current in source | Recommended | Reasoning |
|---|---|---|---|
| **Deadline allowance** | 1800 + 10 × W × qty | **300 + 1.0 × W × qty** (preferred: 300 + pipelined) | Gives 1.68× the craft's own build time at qty 1 and about 300 s of slack, easing to 1.4× at qty 4 because pipelining beats W × qty. **This is the whole fix — no coefficient change matters until this one lands.** |
| **Late-delivery penalty** | Reputation only | **CASH: 0.15% of contract price per second late, capped at 40%** | A reputation-only late penalty *mathematically cannot* make rework expensive enough to matter: it would take a 20-point hit — two entire tiers — for one late contract to move the decision. Cash can. It also decouples lateness from quality, which is what protects the reputation economy under tighter deadlines. |
| **Late-delivery reputation penalty** | 2 points | **1 point** | Recommended **down, not up**. Tightening deadlines tenfold while keeping a large reputation penalty is what would break progression. |
| **Rework time** | 90d, minimum 120 s | **UNCHANGED — 90d, minimum 120 s** `[REVERSED]` | The first pass cut this to 120 + 20d, reasoning that a 540 s stall dwarfed any money term. That was correct at an assumed lambda of 1 and is **wrong at the measured one**. With deadlines the binding constraint, long reworks are **the point**: at 20 s per defect the worst rework is 240 s, which never breaches a sensible slack, so rework would be free at every defect count. Keep the original curve. |
| **Rework time — fixed component** | 0 | 0 | Unchanged. |
| **Rework time — minimum** | 120 s | 120 s | Unchanged. |
| **Concession deduction — base** | 8% | **8% — UNCHANGED from the owner's original** | The first pass raised it to 10%. At the measured material share that was wrong. |
| **Concession deduction — per defect point** | 6% | **4%** `[PARTLY REVERSED]` | **Reduced, and this reverses the first recommendation** (which had raised the slope to 8). At a 19% material share rework is cheap in cash terms, so the concession curve has to come **down** to stay competitive at all. The slope moves the opposite way from last time. |
| **Concession deduction — clamp min** | 8% | 8% | Unchanged. |
| **Concession deduction — clamp max** | 45% | **45% — keep the number, drop the rule** `[REVERSED]` | The first pass derived this as 100% minus material share, so that a concession at the clamp returned materials and nothing more. **At 19% materials that rule yields ~79%, which is not a credible discount for a customer to accept. The derivation does not survive the measurement.** 45% is right for narrative reasons instead — a customer accepting worse than a 45% discount stops being credible — and it should be a **chosen** number, not a formula. |
| **Concession ceiling** | 6 defect points | **6 — keep as a chosen number** | Same fate as the clamp rule. The pass-1 derivation (ceiling = where the curve stops rising) gave 6 only because the clamp happened to bite there. With the gentler slope the curve does not clamp until d=9, so the derivation would put the ceiling too high to constrain anything. Set it at 6 deliberately. |
| **Concession reputation cost** | 1 + d/2 points (flat) | **(0.25 + 0.25d) × the contract's own reputation** | **This one survives the re-measurement intact.** The proportional form keeps the decision identical on a 150,000 cr Scout and a 360,000 cr Cargo, which the flat form does not. The coefficients come down because the concession curve did. |
| **Failed-test deduction per failure** | 10% | 10% | Unchanged. Sunk when the MRB opens. |
| **Failed-test deduction cap** | 30% | 30% | Unchanged. |
| **Tempo discount on deferred margin** | 0.10 | 0.10 | Small by nature; do not use it to carry the mechanic. |
| **Scrap — share of materials recovered** | 0 | 0.40 | Still does not rescue scrap on its own. |

---

## 8. Should the mechanic be kept?

The workbook argues both sides rather than concluding, and the argument is preserved
here because it is the part a future reader will need.

**The case against.** It is live only in a narrow band. The break-even table shows the
choice does not flip at all until slack drops below about 500 s, and it is genuinely
interesting only between roughly 350 s and 100 s. Reaching that band costs a deadline
retune, a new cash penalty system, a reputation rebalance and a UI that shows
remaining slack. That is real systems work — days, not hours — for one decision point,
in a game whose core loop is line-building. And the failure mode if the band is set
wrong is not a boring mechanic but an **unfair** one: a player late through no visible
fault of their own.

**The case for.** The mechanic is not really about the three buttons. Tightening
deadlines gives the whole game a clock, and right now it has none — at 11–14× build
time, nothing the player does on the line has time pressure attached, which is a large
hole in a factory game regardless of the MRB. The disposition choice is a good reason
to fix that, and **the fix is worth more than the mechanic.** Once deadlines bite the
choice becomes legible in a way it is not today: *"this rework takes 540 s and you
have 300 s of slack"* is a decision a player can actually make, rather than an
arithmetic puzzle about deduction percentages.

**The recommended sequence.** Keep it, but sequence it. **Ship the deadline change
first and on its own**, and play the game without touching the MRB — the disposition
menu can keep its current numbers and its one right answer for now. If tighter
deadlines make the game better, the MRB gets interesting for free and is tuned with
the numbers above. If tighter deadlines feel nagging rather than tense, that has been
learned cheaply and the MRB is cut without anything having been spent on it. The
mechanic is downstream of a question not yet answered: **does this game want a clock?**

**The one thing not to do.** Do not tune the deduction curves against the current
deadlines. At 5,760 s of slack every set of coefficients produces the same answer, so
any tuning done now is fitting noise. *That includes the numbers on the recommendation
sheet — they are conditional on the deadline change landing first.*

---

## 9. What was implemented, verified in source

Checked on 2026-08-29 against the working tree at
`C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8`. Every claim below is a claim
about the source as read, not about a packaged build; nothing here is a release gate.

### 9.1 Deadline allowance — ADOPTED, in the preferred form

`Source/LineBossCarFactory/LBSpacecraftGameMode.cpp:771` — `ContractAllowanceSeconds`
now sums the recipe's per-stage cycle seconds into total work and takes the maximum as
the bottleneck, then at `:800-802` computes

```
PipelinedSeconds = CycleSeconds + BottleneckSeconds * (Units - 1)
```

and at `:813-814`

```
constexpr double SlackSeconds = 300.0;
const double Allowance = SlackSeconds + PipelinedSeconds;
```

This is the workbook's **preferred** formula — `300 + 1.0 × pipelined wall-clock` —
not the minimal-change `300 + 1.0 × W × qty` form, so slack is a constant 300 s at
every order quantity, exactly as §3.2 argued. The function's own comments restate the
study's reasoning nearly verbatim, including the 6,200 s figure, "fourteen times the
time needed", the 540 s worst-case rework, and the corridor argument for 300 s.

One addition beyond the study: at `:816-817` the allowance is multiplied by
`FLBSpacecraftDifficulty::Current().DeadlineScale` (floored at 0.05). That dial is
1.6× on Relaxed and 0.7× on Demanding
(`Source/LineBossCarFactory/LBSpacecraftDifficulty.cpp:23` and `:33`), Standard being
1.0. This is a per-difficulty generalisation of the study's second mitigation
(§6) — generosity while learning — applied by difficulty rather than by contract tier.

The change is guarded by an automation test,
`LineBoss.Spacecraft.Research.MissingADeadlineCostsYourName`
(`Source/LineBossCarFactory/LBSpacecraftResearchAuthorityTests.cpp:329`), which
asserts the corridor from both sides — one craft gets more time than it takes to build
but less than 3× it — and asserts pipelining directly: four craft cost exactly three
extra bottleneck cycles, and slack does not grow with order size
(`:362-385`). A test existing is not a run; no fresh `index.json` report is cited here.

### 9.2 Rework time — UNCHANGED, matching the reversal

`Source/LineBossCarFactory/LBSpacecraftProductionTypes.cpp:391-398` —
`ReworkSecondsFor` is `90 s × defect points`, floored at 120 s. This is the owner's
original curve, which the second pass explicitly recommended keeping and which the
first pass had been wrong to cut to `120 + 20d`. The shipped comment still marks it
`PROVISIONAL, pending the owner's economy tuning`.

### 9.3 Concession ceiling — matches

`Source/LineBossCarFactory/LBSpacecraftProductionTypes.cpp:533-541` —
`MaxConcedableDefectPoints()` returns **6**, as recommended, and as a chosen number
rather than a derivation.

### 9.4 Concession deduction slope — NOT adopted

`Source/LineBossCarFactory/LBSpacecraftProductionTypes.cpp:544-556` —
`ConcessionDeductionPercent` is still

```
const int32 Owed = 8 + 6 * FMath::Max(DefectPoints, 0);
return FMath::Clamp(Owed, 8, 45);
```

The base (8%) and the clamp (8–45%) match the recommendation, because the
recommendation for those two was **to leave the owner's originals alone**. The slope
is still **6% per defect point; the recommended reduction to 4% was not adopted.** The
Curves and Break-even tables in §4 and §5 were computed at 4%, so they do not describe
the shipped curve.

### 9.5 Concession reputation cost — NOT adopted

`Source/LineBossCarFactory/LBSpacecraftProductionTypes.cpp:558-565` —
`ConcessionReputationCost` is still the flat `1 + DefectPoints / 2`. The proportional
form — `(0.25 + 0.25d) × the contract's own reputation`, the one recommendation that
survived re-measurement intact — is **not in the source.** The consequence the study
named still stands: the disposition decision is not identical on a 150,000 cr Scout
and a 360,000 cr Cargo.

### 9.6 Cash late-delivery fee — NOT adopted

There is no per-second cash late fee anywhere in `Source/LineBossCarFactory`. A
missed deadline moves an accepted contract to `Expired`
(`Source/LineBossCarFactory/LBSpacecraftProductionAuthority.cpp:896-910`; an offer
never accepted merely lapses to `Withdrawn`), and settlement
(`:395-425`) deducts only the failed-test percentage or, if a concession was signed,
the concession percentage **in place of it, never on top**. Lateness costs no cash.

The late penalty remains **reputation-only**, which is precisely the arrangement the
study said "mathematically cannot make rework expensive enough to matter". Moreover,
the shipped penalty is **not** the recommended reduction to 1 point:
`Source/LineBossCarFactory/LBSpacecraftReputationAuthority.cpp:56-69` charges twice
what the whole order would have earned, floored at 3 points, and scaled by the
difficulty's `LatePenaltyScale` (0.5 on Relaxed, 1.5 on Demanding). For a single Scout
worth 2 points that is a 4-point hit on Standard — between the 2 and 5 point cases the
reputation stress simulation modelled, and heavier than the study recommended. It is
applied once per contract, only for an order actually taken on
(`:96-105`).

The surrounding reputation constants do match the study's stated inputs:
`PencePerReputationPoint = 7500000`, i.e. **75,000 cr per point**
(`Source/LineBossCarFactory/LBSpacecraftReputationAuthority.h:62`); tier thresholds
**10 / 25 / 50** (`LBSpacecraftReputationAuthority.cpp:11-26`); and a **5% price
premium per tier** above the first (`:41-44`).

### 9.7 Scrap material recovery — NOT adopted

`Source/LineBossCarFactory/LBSpacecraftProductionAuthority.cpp:807-843` — `ScrapUnit`
removes the unit and returns nothing to the ledger. The recommended 40% material
recovery does not exist. The study itself noted it "still does not rescue scrap on its
own", so nothing turns on this.

### 9.8 Summary of adoption

| Recommendation | Status in source |
|---|---|
| Deadline allowance → 300 + pipelined wall-clock | **Adopted**, in the preferred form, plus a difficulty scale |
| Rework time unchanged at 90d / min 120 s `[REVERSED]` | **Matches** — the original was kept |
| Concession base 8% and clamp 8–45% unchanged `[REVERSED]` | **Matches** — the originals were kept |
| Concession ceiling 6, as a chosen number | **Matches** |
| Concession slope 6% → 4% `[PARTLY REVERSED]` | **Not adopted** — still 6% |
| Concession reputation cost → proportional | **Not adopted** — still flat `1 + d/2` |
| Cash late fee 0.15%/s, capped 40% | **Not adopted** — no cash late fee exists |
| Late reputation penalty 2 → 1 point | **Not adopted** — the shipped penalty is heavier (2× order earnings, floor 3, difficulty-scaled) |
| Scrap recovers 40% of materials | **Not adopted** — scrap returns nothing |

This is consistent with the study's own advice in §8: ship the deadline change first
and on its own, leave the MRB coefficients alone until it is known whether the game
wants a clock. The deadline change landed; the MRB retune deliberately did not. The
concession coefficients in the source still carry their `PROVISIONAL, pending the
owner's economy tuning` comments, which is an accurate description of their status.

---

## 10. Open items carried forward

- **Cargo's nominal build time has never been measured.** The whole study uses the
  Scout's 440 s for both craft. Every Cargo figure that depends on build time is
  therefore assumed, not measured, and the workbook flags this in the cell.
- **The value of a reputation point (~6,000 cr)** is an estimate — about 0.3pp of tier
  premium per point against remaining lifetime revenue — and is explicitly spiky near
  the tier thresholds. It is not a measurement.
- **The narrow live band (roughly 350–100 s of slack)** has not been playtested. The
  study's whole recommendation rests on finding out whether a clock improves the game,
  and that question is answered by playing, not by arithmetic.
- **Whether the MRB is kept at all** remains the owner's call, and the study is
  deliberately non-committal on it.

---

## Related documents

- `Docs/ECONOMY_CALIBRATION_PRODUCTION_LINE_v001.md` — economy calibration against the
  genre benchmark.
- `Docs/CAR_MANUFACTURE_MECHANICS_NOTES_v001.md` — the benchmark game's contract and
  quality vocabulary, mined read-only.
- `Docs/SPACECRAFT_SLICE_GOAL_v001.md` — the vertical slice this economy sits inside.

Two documents named in earlier drafts of this study — a contract-design ideas note and
the spacecraft pivot authority — are **not present in `Docs/`** in this tree as of
2026-08-29. They are not cited here as if they were.

The first-pass MRB workbook is not preserved in `Docs/`. What is known of it survives
only as the `[REVERSED]` entries in this document, which is a reason to keep those
entries verbatim rather than tidying them away.
