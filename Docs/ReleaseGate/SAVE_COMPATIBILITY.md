# Save compatibility

## Current source authority

The checked-in root is
[`ULBPressShopSaveGame`](../../Source/LineBossCarFactory/LBPressShopSaveGame.h)
with `SaveFormatVersion = 17`. The coordinator is
[`ALBPressShopCampaignController`](../../Source/LineBossCarFactory/LBPressShopCampaignController.cpp),
whose current format is also 17. Its preflight admits root versions 13-17 and
campaign ID `THE_RESTART_PRESS_SHOP`.

This is a **source contract**, not a released compatibility claim. Both v17
campaign tests succeeded again in the final live Unreal MCP five-test
campaign/material-flow gate, but no
standalone indexed report or packaged process-restart journey covers this
revision yet.

| Root version | Checked-in loader | Migration meaning in current source |
|---:|---|---|
| 1-12 | Rejected | Historical roots are not admitted. The presence of legacy fields is not evidence that these files load. |
| 13 | Accepted legacy | Restores the authored press-shop topology, rejects future topology/management/fleet payloads, and creates fresh deterministic management plus one starter stillage FLT. |
| 14 | Accepted legacy | Adds coherent optional inbound delivery/coil-AGV restoration; management and the stillage fleet are freshly migrated. |
| 15 | Accepted legacy | Adds ED/e-coat state; future v16 fleet/jobs and v17 management are rejected, then fresh migrated authorities are created. |
| 16 | Accepted legacy | Retains its native validated stillage-FLT fleet/jobs and receives fresh deterministic v17 management with no inherited research. |
| 17 | **Current source; focused live validation** | Requires a valid explicit `LegacyAuthoredPressShop` or `PlayerBuiltFactory` topology and a validated `FLBFactoryManagementSaveState`. Both focused round trips passed in the final live 5/5 gate; indexed and packaged proof is pending. |

## V17 topology and management contract now present

The checked-in source:

- stores `ELBCampaignTopologyMode TopologyMode` and
  `FLBFactoryManagementSaveState FactoryManagement` at the campaign root;
- captures legacy topology when exactly one operations console exists and
  player-built topology when none exists;
- clears stale PR-004 through PR-010 state when capturing a player-built root;
- validates v17 topology and management, and rejects non-default future fields
  smuggled into v13-v16 roots;
- restores dynamic machines, ED lines, AGV infrastructure and storage before
  connection topology; and
- applies the validated management snapshot last so structural restoration does
  not charge saved cash or replay capital transactions.

The source also contains two campaign tests in
[`LBPressShopCampaignControllerTests.cpp`](../../Source/LineBossCarFactory/LBPressShopCampaignControllerTests.cpp):

- `LineBoss.PressShop.Save.WholeShopCampaignRoundTrip` for the authored legacy
  topology, v13-v16 migrations, future-payload rejection and v17 management; and
- `LineBoss.PressShop.Save.PlayerBuiltV17ManagementRoundTrip` for a console-free
  dynamic-machine root, invalid-management zero-mutation preflight, and exact
  cash/research restoration.

Both tests returned `Success` in the 2026-08-11 final live five-test gate recorded
in [`UnrealMCP_Rerun3.log`](../../Saved/Logs/UnrealMCP_Rerun3.log). That is focused editor
evidence, not an indexed release report or packaged restart proof.

## Evidence gap and remaining risk

The latest archived `WholeShopV16Combined` report is red. It demonstrates the
old v16 authored/player-built topology conflict, but predates the v17 source and
does not override the later live success of both v17 tests. Conversely, the live
log does not replace a standalone indexed report, failure-injection coverage or
a packaged process-restart journey.

Preflight reduces invalid-input mutation, and the new player-built test checks
one rejected management case. The restore method still performs several
structural restores in sequence. Release proof must demonstrate that every
failure path is either non-mutating or rolled back; this documentation does not
infer transactional safety from ordering alone.

## Save release tests

A save feature is not finished until all applicable cases are archived green:

1. Fresh v17 player-built campaign memory and disk round trip.
2. V17 legacy-authored topology memory and disk round trip.
3. V13, v14, v15 and v16 migration fixtures with exact expected fresh/native
   management and fleet behaviour.
4. Rejection of bad identity, duplicate identity, invalid topology and future
   payload smuggling with zero world, ledger or inventory mutation.
5. Failure injection after each structural restore stage with verified rollback
   or a documented non-mutating guarantee.
6. Active/pending physical stillage jobs, purchased FLTs, management ledger,
   research, upgrades, quality, wear and OEE bucket restoration.
7. Save in a packaged build, exit the process, restart, load, then continue
   production without duplicate revenue/research or lost inventory.

Serialization to memory alone is insufficient: the restored world and its next
gameplay event are part of compatibility proof.
