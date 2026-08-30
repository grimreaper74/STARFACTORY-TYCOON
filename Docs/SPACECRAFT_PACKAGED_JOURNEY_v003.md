# Spacecraft slice — packaged journey receipt v003

Date: 2026-08-29 (evening). Supersedes v002 (2026-08-24), which covered the
Scout and Cargo journeys **driven by `LB.Spacecraft.Deposit`** — parts banked
straight into station stores. That is why v002 passed while the fault below
was live: depositing into stores bypasses the drone haulers entirely.

Build: `RunUAT BuildCookRun -platform=Win64 -clientconfig=Development -build
-cook -stage -pak -archive` → `Builds/StarFactoryTycoon_v005/Windows/
LineBossCarFactory.exe`, exit 0.

## What this revision fixes

`ALBSpacecraftGameMode::TickWholeSimStep` — the hand-rolled clock behind
`LB.Spacecraft.Run`, `.Jump` and `.AutoPlay` — did not tick the drone
haulers. They were ticked only from the actor tick, and `Run` advances
thousands of simulated seconds inside two or three real frames, so they
received hundredths of a second in total against a haul travel time measured
in tens. They never completed a phase, no station was ever fed, and every
console-driven run held at the head of the line on a hull that sat in the
delivery dock.

**Scope of that fault, stated precisely:** a human playing a packaged build
was NOT affected — the actor tick feeds the haulers in real time. What was
broken was every automated path, which is why the loop could not be *proven*.

## Journey — Scout canonical, supply-fed (exit 0)

`BuildLine` → `Place DeliveryDock` → `BuildEconomy 2` → `Start 2` →
`Run 1800 1.0` → `Status`, unattended `-NullRHI`:

    CONTRACT SC-CONTRACT-001 SCOUT-01 x2 dispatched=2 state=2   (Complete)
    revenue=30000000 pence   (300,000 cr)
    ON THE LINE: nothing

Log: `C:\Temp\pkg005.log`. This is the first packaged journey in which the
craft were fed **through the supply chain** — dock → rack → drone hauler →
station stockpile — rather than deposited into stores by a dev command.

## Claim

**Packaged playable** for the named journey in THIS Development packaged
revision (`StarFactoryTycoon_v005`), dev-command-driven, headless `-NullRHI`.

**NOT covered:** the rendered path in this revision, mouse/keyboard build UI,
Shipping configuration, audio (none exists), onboarding (none exists),
controller input (none exists).

## v006 supersedes v005 — and is the build to send

`v005` was compiled before the follow-up fix that also syncs **station
stores** on the sim clock. `StarFactoryTycoon_v006` carries it, packaged
exit 0, and ran the identical journey to the identical result:

    CONTRACT SC-CONTRACT-001 SCOUT-01 x2 dispatched=2 state=2   (Complete)
    revenue=30000000 pence   (300,000 cr)

Log: `C:\Temp\pkg006.log`. **Send v006.** Both revisions complete the
journey; v005 is kept only as the evidence that the hauler fix alone was
sufficient to close the loop.

Neither packaged revision carries the later behaviour-neutral refactor that
moved the sim step onto the save context, nor the regression test that
guards it — both are source-only and change no runtime behaviour.

## Automation alongside

`LineBoss.Spacecraft`, 130 tests, 0 failed (105 clean, 25 with warnings) —
`Saved/Automation/StationStoresOnSimClock_v001/index.json`.

A caution recorded with it: the documented automation command uses a
RELATIVE project path, which in several shells here opens no descriptor,
runs **zero** tests, and leaves `Saved/Logs/LineBossCarFactory.log` holding
the previous run's clean tally. Pass the project path absolute and treat a
missing `index.json` as "did not run".
