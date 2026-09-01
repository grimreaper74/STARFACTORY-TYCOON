# Star Factory Tycoon — Two-Minute Video Shot List (v001)

**Target:** 120 seconds. Demonstrate core loop (place → commission → work → deliver), mechanics (grid/drones/crane), art (clean industrial bright), UI (management), and progression (unlocks). Owner films; Claude preps states.

---

## Shot 1: Establish Empty Hall
**Duration:** 5s | **Speed:** Real-time

**On Screen:** Empty OneFactory map with clean floor, clear grid, hud showing objectives panel ("OBJECTIVES" / "FIRST STEPS").

**Prepare State:** 
- Fresh save, no stations, no contracts accepted.
- Camera framing to show full hall width + runway in distance.
- Highlight the grid and hazard striping on the floor.

**Demonstrates:** Art (clean bright industrial palette, grid clarity, floor design), UI (objectives panel for player direction).

---

## Shot 2: Build Production Line
**Duration:** 15s | **Speed:** 4× speed

**On Screen:** Place 4–5 assembly stations along the grid in a line. Track auto-routes between them as each station lands. Ghost previews show placement legality. Objectives panel updates to show "Place assembly stations [DONE]" as last station places.

**Prepare State:**
- Empty build authority, ready for placement.
- Camera steady, slightly elevated isometric angle to show grid and track routing clearly.
- Pre-plan station positions to form a clean line (no mistakes that need undo).

**Demonstrates:** Mechanics (grid snap, auto-routing track, dock placement), UI (objectives guide), player agency (direct control over factory shape).

---

## Shot 3: Commission the Factory
**Duration:** 3s | **Speed:** Real-time

**On Screen:** Close on objectives panel. "Commission the factory" line appears as pending. Click Commission button; panel updates to "[DONE] Commission the factory". UI toast or flash confirms state change.

**Prepare State:**
- Stations already placed from Shot 2.
- Point cursor at the Commission button in the management UI (top corner or build panel).

**Demonstrates:** UI workflow (management layer makes factory operational), progression checkpoint.

---

## Shot 4: Accept a Contract
**Duration:** 4s | **Speed:** Real-time

**On Screen:** Contracts panel (or popup menu) appears. Select a contract (e.g., "Assemble 1× Tier 1 Spacecraft"). Accept button. Panel updates to show contract accepted. Objectives panel updates "Accept a contract [DONE]".

**Prepare State:**
- Factory already commissioned.
- Contracts are available (game mode seeded with sample contracts).
- Point cursor to contract accept flow.

**Demonstrates:** Progression system (contracts drive work), player choice (which contract to accept).

---

## Shot 5: Production — Drones Fitting (Main Sequence)
**Duration:** 35s | **Speed:** 4× speed, with one cycle at real-time

**On Screen:** Craft rides the track via crane pulse. At each station, drones swarm and fit allocated parts onto the hull. Cycle repeats through 3–4 stations, then slow to real-time for one station close-up to show drone motion and part detail.

**Prepare State:**
- Contract accepted, production initialized.
- Craft spawned at start of line with allocated parts staged in dock dollies beside each station.
- Camera pan/framed to show 2–3 consecutive stations; let the player watch work progress.

**Demonstrates:** Core mechanic (drones as co-stars, fitting parts, crane pulse motion), art (machinery detail, drone motion, part colors), pacing (4× shows efficiency, real-time shot confirms mechanical quality).

---

## Shot 6: Spray Booth (Paint Stage)
**Duration:** 10s | **Speed:** Real-time

**On Screen:** Craft moves into spray booth. Machinery (gantry arms or spray heads) actuate and apply paint. Craft body changes color/finish. Duration ~10 seconds to show the detail and satisfy the "show mechanics" bar.

**Prepare State:**
- Craft arrives at paint station with all assembly work complete.
- Paint cycle configured and ready.

**Demonstrates:** Specialized station type (paint finishing), machinery choreography, visual transformation of the product, quality/craftsmanship in the presentation.

---

## Shot 7: Delivery and Launch
**Duration:** 20s | **Speed:** 4× speed

**On Screen:** Finished craft exits spray booth, moves to runway docking area. Crane or lift mechanism stages the craft for departure. Launch sequence: craft lifts/slides away from factory building. Camera holds on the finished spacecraft in flight or pulling away.

**Prepare State:**
- Craft at end of line, painted and ready.
- Runway/dock staging area clear and framed for the exit move.

**Demonstrates:** Complete loop closure (all work done, product leaves), world-scale (factory as a building, craft as significant object), progression payoff (you built and shipped it).

---

## Shot 8: Progression UI and Next Steps
**Duration:** 8s | **Speed:** Real-time

**On Screen:** Management UI shows money received, new bay count unlocked, and progression objectives updated ("CONVEYOR BELTS [1/2]", etc.). Objectives panel highlights new research or features available. Fade or end.

**Prepare State:**
- Delivery complete, money/progression authority updated.
- UI shows balance, new unlock, next milestone.

**Demonstrates:** Progression system (money earned, unlocks work toward next milestone), player growth (what you can build next), standing UI language (clean hue-free interface, progression readability).

---

## Notes

- **Audio:** All shots play with in-game ambient (machinery hum, drone buzz, crane beeps). No music or voiceover in this cut; audio is the owner's commission path (Docs/AUDIO_PRODUCTION_v001.md).
- **Pacing:** 4× speed on placement and production shows efficiency; real-time on paint and one drone close-up sells the quality. Owner judgment on exact timing.
- **One-shot state:** Shoot this as one continuous run (accept contract → manufacture → deliver → progression) to keep the loop legible. No cuts or resets mid-delivery.
- **Fallback:** If the paint booth is not ready or audio is incomplete, compress Shot 6 and Shot 8, extend Shot 5 to 40s and show a second contract/delivery cycle for "here's the repeat loop that earns you money."

**Total:** 120 seconds | **Critical Path:** Shots 1–8 as listed, in order. Owner films live play; Claude prepares the starting state and verifies each beat loads correctly.

---

## Fable verification (2026-09-01) — corrections to the draft above

The structure and timings stand. Four claims do not match the game and
must be read as corrected here before filming:

1. **Shot 1 names the wrong map.** The game opens on the spacecraft
   site map (`LB_SpacecraftFactory_v002`), factory building pre-placed;
   the player clicks in to the hall. "OneFactory" is the car-era
   integration map and is not what gets filmed. The empty-hall
   establish shot happens after entering the pre-placed ship factory.
2. **Shot 6 oversells the spray booth.** The booth is a pass-through
   process station; there is currently NO visible colour change on the
   craft body. Film the booth as a tunnel beat the craft passes
   through, or use the fallback in the Notes (extend Shot 5). Do not
   promise a paint transformation the build cannot show.
3. **Shot 7's "in flight" hold must be filmed from the runway view.**
   The launch camera is deliberately disabled (owner decision,
   2026-08-30, do not re-enable). The craft departs the building; the
   camera stays in the world view.
4. **The Notes' "in-game ambient" audio does not exist.** The module
   ships silent today; audio is a pending owner commission. Plan the
   cut for licensed music or commissioned SFX overlaid in the edit —
   do not rely on captured game audio.
