# OneFactory native player builder v001

## Player contract

The dedicated Moorcross Works map still starts as a premade, empty native shell.
Its existing `ALBManagementPawn` opens the existing `ULBManagementRootWidget` UMG
surface. On the Build page, `ULBOneFactoryPlayerBuilderSubsystem` supplies exactly
five controller-, keyboard- and mouse-compatible actions:

1. New Factory / commission the Press starter.
2. Select the next stable station responsibility.
3. Change the selected starter programme, or move a selected player machine.
4. Move a starter station, or disconnect a selected player machine.
5. Remove a selected player machine.

No AHUD Canvas presentation was added or re-enabled.

## Atomic New Factory transaction

`New Factory` is disabled until exactly one `ALBOneFactoryBootstrap` is `Ready`.
The action then performs two explicit phases:

1. Create one canonical `ALBOneFactoryPressStarterLayoutAuthority` data actor.
2. Validate the exact NativeOnly profile and materialise one
   `ALBOneFactoryPressStarterPresentationActor` from the captured data snapshot.

If phase two fails, both newly created actors are destroyed. Commission is a
separate explicit action and verifies the coherent data revision, exact native
class/asset provenance, presentation instance count and all seven station
transforms before commit.

Programme and starter-station moves capture the previous data state, mutate the
data authority, then rematerialise the presentation. A presentation failure
restores both the previous data and previous presentation.

## Edit authority boundary

The seven canonical starter responsibilities are a coherent seven-station,
six-route package. They can be reprogrammed or moved but cannot be individually
removed or disconnected in v001. Their UMG card states that reason explicitly.

Player-added `ALBFactoryBuildMachine` actors retain their existing authorities:

- movement calls `ULBFactoryMachineBuilderSubsystem::MoveMachine`;
- disconnect first calls `CanEditMachine`, then
  `ULBFactoryConnectionSubsystem::DisconnectActor`;
- removal calls `ULBFactoryMachineBuilderSubsystem::RemoveMachine`.

Those authorities retain the existing active-WIP, reservation, owner,
placement-envelope and exact-connection rollback gates. The UMG view model shows
the current rejection reason rather than claiming an edit succeeded.

## Integration seam

The only shared runtime integration is three narrow branches in
`LBControlRoomHUD.cpp`: OneFactory action count, UMG view-model projection, and
action confirmation. Old maps without an `ALBOneFactoryBootstrap` continue to use
the existing generic factory catalogue unchanged.

