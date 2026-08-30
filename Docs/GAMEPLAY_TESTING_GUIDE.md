# Gameplay Testing Guide for Star Factory Tycoon

## Current State (2026-08-30)

**Test Suite**: 130/132 passing (2 expected blockout failures)
**Core Loop**: BuildLine + Start + Production runs correctly
**Scout Model**: v003 integrated and running

## What Works

✅ Factory placement and commissioning
✅ Contract acceptance  
✅ Production line simulation
✅ Craft progression through stations
✅ Power system (idle state)
✅ Research system (zero state)
✅ Drone fleet management
✅ Inventory tracking

## What Needs Testing

### Blocker: Missing Infrastructure in BuildLine

**Issue**: `LB.Spacecraft.BuildLine` creates fitting stations only, NOT supporting infrastructure.

**Required for production**:
- Delivery Dock (to receive materials)
- Storage Racks (to hold materials)
- Initial component inventory

**Symptom**: Line holds with "NO DELIVERY DOCK - BUILD ONE FOR GOODS TO ARRIVE AT"

### Working Test Sequence

Use the autoshow mechanism which pre-stocks components:

```powershell
UnrealEditor.exe 'project.uproject' /Game/Maps/Factory -game -LineBossAutoShow
```

This runs:
1. LB.Spacecraft.BuildLine
2. LB.Spacecraft.StockShowComponents (stocks 4x each component)
3. Coordinates production line
4. Starts a Scout contract
5. Runs production unattended

## What to Test

### Recommended Test Cases

1. **Full Production Run** (140 seconds nominal)
   - BuildLine → Stock → Start → Run 600s
   - Verify: Craft exits line, revenue recorded, contract marked delivered

2. **Multi-Craft Pipeline** (180 seconds)
   - BuildLine → Stock → Start x3 → Run 900s
   - Verify: 3 crafts on line, pipelined execution, each gets components

3. **Station Staffing** (Drone Allocation)
   - BuildLine auto-allocates 2 drones per fitting station
   - Verify: "DRONES total=12 flying=2" in status (should scale with crafts)

4. **Component Allocation**
   - 6 components per Scout craft
   - Stations allocate: Hull+Power, Propulsion, Electronics, Navigation, Interior
   - Verify: All "FITS" lines show correct components

5. **Stall Behavior** (Component Shortage)
   - Start craft without components
   - Verify: Line holds with "INSUFFICIENT RESOURCES" message (correct fail-closed)

### Test Output Interpretation

**Healthy Status Line**:
```
SPACECRAFT STATUS sim=600.0s stations=7 commissioned=1 configured=1 revenue=XXX cash=YYY pence
  ON THE LINE: SCOUT-01-000001 at SprayBooth (route step 6), 0.0s into its stop, stage 7
  CONTRACT SC-CONTRACT-001 SCOUT-01 x1 dispatched=1 state=2  ← state=2 is COMPLETED
```

**Stalled Status**:
```
LINE HELD: INSUFFICIENT RESOURCES: AssemblyRobot-002 NEEDS 1x Component.Hull
```
(This is correct - factory is properly refusing work)

## Dev Commands Available

```
LB.Spacecraft.BuildLine              # Build 7-station fitting line
LB.Spacecraft.Start                  # Accept a contract
LB.Spacecraft.Deposit <id> <count>   # Stock floor store (NOT stations)
LB.Spacecraft.Order <id> <count>     # Order materials (needs Dock)
LB.Spacecraft.Run <secs> <scale>     # Simulate production
LB.Spacecraft.Status                 # Print factory state
LB.Spacecraft.BuildEconomy [target]  # Build parts factory (if implementing)
LB.Spacecraft.Grant [points]         # Grant research points
LB.Spacecraft.Power [kW]             # Add power capacity
```

## Known Gaps

1. **No audio** - Game is silent (owner-dependent)
2. **No onboarding** - Player doesn't know what to do (implementation needed)
3. **No delivery dock building** - Player can't order materials without it
4. **Incomplete dev tooling** - BuildLine doesn't create complete playable setup

## Next Steps for Implementation

**Priority 1: Extend BuildLine** to also place:
- One Delivery Dock (so material orders work)
- One Storage Rack (so materials can be held)
- Initial component stock for first craft

**Priority 2: Add onboarding** UI/flow to explain:
- How to build stations
- How to staff with drones
- How to accept contracts
- How to manage resources

**Priority 3: Audio** (awaiting owner assets)
- Rotor loop (drones)
- Factory ambience
- Craft launch sequence
- UI feedback sounds
