# What the automated player measured — import margin, 2026-08-29

**Status: validation-only.** Numbers come from `LB.Spacecraft.AutoPlay 3600`
in an unattended `-NullRHI` run of the editor target, not from a packaged
build. They measure the shipped economy as it stands today; they are not a
balance decision.

## How the measurement became possible

The headless clock (`ALBSpacecraftGameMode::TickWholeSimStep`) did not tick
the drone haulers — they were ticked only from the actor tick, and
`LB.Spacecraft.Run` advances thousands of simulated seconds inside two or
three real frames. The haulers therefore received a few hundredths of a
second in total, never completed a haul, and no station was ever fed. Every
console-driven run built nothing. Fixed by ticking them on the sim clock.

Three further faults in the GREEDY policy had to go before the numbers meant
anything:

1. It never built a supply chain, so it ran on the opening loadout alone.
2. It asked "is the contract list empty" to decide whether to take work. The
   offer board makes that false forever after the first tick, so it took
   **one** contract in sixty simulated hours.
3. Its first restock re-ran `SetupEconomy`, which **is not idempotent about
   machines** — it is idempotent about the dock and the racks only. The
   factory grew from 9 stations to 75 and the run's revenue tripled. That is
   the policy cheating; the figures below are from the version that does not.

## The figures

Sixty simulated hours, nine stations, GREEDY policy:

| | |
|---|---|
| Craft delivered | 481 |
| Revenue per craft | 150,000 cr |
| All-in cost per craft | 47,371 cr |
| **Margin** | **68.4%** |
| Cycle time | ~449 s per craft, sustained |

The 449 s matches the known ~440 s Scout figure, so the line ran flat out for
the whole soak rather than in bursts.

## RETRACTED: the 68.4% margin, and why

**Do not act on the 68.4% figure.** It was published in the first version of
this document and in commit "Teach the automated player to buy parts", with
the conclusion that importing everything beats fabricating and the game does
not punish a player who skips its content. Checking it directly showed the
opposite, and the retraction matters more than the finding did.

**Direct measurement.** Place a delivery dock, note the cash, order one of
each of the six components, note it again:

    cash 86,500,000 -> 74,540,000 pence  =  119,600 cr

That is the exact figure the catalogue comment states as the intended cost of
importing a whole craft, against 150,000 cr revenue - a **20% margin**, which
is the documented design working as written, not a hole in it.

**The two numbers do not reconcile, and that is the open question.** The soak
delivered 481 craft at exactly 150,000 cr each (72,150,000 cr revenue) while
spending only 22,790,000 cr all-in. At 119,600 cr of components per craft it
should have spent about 57,530,000 cr. Roughly 290 craft's worth of parts are
unaccounted for.

Two explanations were tested and **eliminated**:

- *Components are not consumed.* They are. Stocking exactly one craft's worth
  (`BuildEconomy 1`) and running a five-craft contract yields exactly one
  craft, then a fail-closed hold on the next hull.
- *The two purchase paths charge different prices.* They do not. The console
  `LB.Spacecraft.Order` and the panel both go through
  `PlaceResourceOrder` and `GetOrderablePricePence`.

**Narrowed further.** A shorter soak makes the shape clearer: 120 sim-minutes
delivers 17 craft at 424 s each (consistent with the long run's 449 s) and
spends 61,259 cr per craft against the 119,600 cr a full bill costs. The
shortfall is almost exactly HALF, and it holds at both run lengths, so it is
a systematic factor rather than drift.

**The player-facing economy tested clean at every point**, which is what
matters most and bounds the problem to the dev supply path:

- The opening factory's free starting loadout does **not** refill. Taking a
  five-craft contract on the bare opening factory yields exactly one craft
  (+147,880 cr, a 150,000 cr order less a small defect deduction), then a
  correct fail-closed hold naming the missing dock.
- Components are consumed exactly once each; stocking one craft's worth
  yields one craft.
- Contract payment credits revenue and cash by the identical amount, so
  there is no hidden income inflating the cash figure.

**Largely explained, and mostly fixed.** The cause was the same omission as
the haulers, one layer along: `SyncStationStores` also ran only from the
actor tick. A station placed during a console-driven run therefore never got
a **stockpile**, while `CommissionFactory` still gave it a fitting
allocation. In the soak that bought three stations, exactly one had a store —
so four of the six components were allocated to stations with nowhere to hold
parts, and were fitted out of nothing and never paid for.

Syncing station stores on the sim clock as well moved the same 17-craft soak
from 61,259 cr to **78,412 cr** of spend per craft against an unchanged
255,000 cr of revenue. The gap to 119,600 cr has narrowed but is not closed,
and the remainder is not yet understood — note that the run ends holding 180
units of paid-for, unconsumed stock, which pushes the true consumption figure
*further* from the bill, not closer. Treat the residue as open.

So a discrepancy remains and is not fully explained. It may be an accounting fault, or
the policy's restock may interact with the dock's finite hold in a way that
makes deliveries arrive without a matching charge. **It is worth chasing: an
economy that mints parts is a bigger problem than a mistuned one.** Until it
is understood, neither margin figure should drive a balance decision.

**A related claim, RETRACTED.** This document previously said `BuildEconomy
20` "spends 579,200 cr and then the line builds nothing", and blamed a jammed
order queue against the dock's finite hold. That was wrong, and wrong in the
same way as the margin figure: inferred from a symptom instead of read. The
command refused, fail-closed and in plain words — *"INSUFFICIENT FUNDS - NEED
331200 cr, HAVE 320800 cr"* — and the line built nothing because the economy
was never finished. I had grepped only for `LINE HELD` and `STATUS` and never
saw the refusal.

**What the investigation did find is real, and is fixed.** Ordering in bulk
was impossible by construction:

- `FindDeliveryStore` demanded a dock with room for the **whole** order, so a
  900-unit order against a 400-unit dock was refused outright. A big order
  was strictly harder to place than the same goods bought in dribs.
- `TickOrders` delivered all-or-nothing: a store without room for the entire
  order took **none** of it and retried forever, with the money already spent.
- The panel had no quantity control at all — hard-coded lots of 5 and 10.

Deliveries now land as much as fits and keep the rest on the lorry; a dock
with any room accepts an order of any size; and the panel carries a BUY
QUANTITY control cycling x1 / x5 / x20. A 900-unit order against a 400-unit
dock now lands 400 immediately and delivers the remaining 500 as the haulers
drain it. A genuinely full dock still refuses, still says "BACKED UP", and
the test that pins that wording still passes.

## Caveats

- Reputation ended at 2 despite 361 contracts and 481 deliveries. This is
  **not** a fault, and it is worth stating plainly because it looked like
  one: of the contracts taken, 240 completed and **120 expired** with fewer
  craft delivered than ordered. `SyncFromLedger` docks the name once per
  accepted-and-missed order, and credits every delivery, so a policy that
  accepts a two-craft contract the moment the last one clears — while a
  Scout takes 449 s — earns and loses its name in roughly equal measure.
  The deadline and penalty system demonstrably bites. The policy
  over-commits; the game is right.
- The policy still places stations by marching Y outward until it leaves the
  building ("MUST STAND INSIDE A BUILDING" at Y=9200). `SetupEconomy`'s
  internal `TryPlace` already scans the hall for a legal spot and is the
  better tool; it is a local lambda and would need extracting.
- Automation evidence: `LineBoss.Spacecraft`, 130 tests, 0 failed (105 clean,
  25 with warnings), `Saved/Automation/AutoPlayCompetent_v001`.
