# Line Boss support-robot runtime v002 quarantine

Status: **DORMANT / NOT PROMOTED / NOT ENABLED**

This document records the replacement native architecture under:

`Plugins/LineBossSupportRobotsRuntimeV002`

It supersedes the staged `Source/LineBossCarFactory/LBSupportRobot*`,
`LBCleaningAMR*` and `LBMaintenanceAMR*` files as the design direction only.
Those v001 files remain byte-for-byte untouched. Nothing in v002 is a promoted
runtime implementation until native build, UHT, runtime, save, collision and
fresh-Unreal visual gates all pass.

## Quarantine boundary

- `EnabledByDefault` is `false` in the plugin descriptor.
- The plugin is absent from `LineBossCarFactory.uproject`.
- The project descriptor still has no `Modules` array.
- The accepted data-only RP01 Pawn Blueprint is unchanged and has not been
  reparented or given this component.
- No v002 component creates a root, collision, static mesh, skeletal mesh or
  scene component.
- No v002 code calls `SetActorLocation` or `SetActorTransform`.
- Native authority providers are not supplied yet, so all route, dock,
  commissioning, fault-clear, work, tool and physical-proof requests fail
  closed.

## Runtime ownership

`ULBSupportRobotRuntimeComponentV002` can attach to either `APawn` or `AActor`.
It resolves existing scene components by canonical name, Blueprint's generated
`_GEN_VARIABLE` / `_0` suffix, or by either stable tag:

- `LB.Anchor.<CanonicalName>`
- `LBAnchor:<CanonicalName>`

The component validates transform, parent, duplicate-name/tag and one-component-
per-anchor conditions but never creates or reparents geometry. A component with
several coincident anchor tags cannot impersonate multiple canonical anchors.
RP01 uses the 23 accepted canonical shared
anchors. CR01 adds M07-M25 following
`LB_CR01_UNREAL_CHILD_COMPOSITION_CONTRACT_v001.json`. MR01 adds its arm,
outrigger, mast, carousel and T1-T8 socket hierarchy. Dock-side CR M28-M30 and
MR M35-M37 remain the responsibility of separate dock actors.

Each runtime class is locked to its constructor-defined RP01, CR01 or MR01
variant identity. Configure/restore cannot relabel the shared base as a derived
variant and bypass the corresponding cleaning or maintenance interlocks.

## Native-only authority boundary

Blueprint can request a route by catalog ID and expected revision. It cannot
submit waypoints or a `bCertified` flag. The following provider interfaces use
`CannotImplementInterfaceInBlueprint` and are registered through non-reflected
world-subsystem methods:

- `ILBRouteAuthorityProviderV002`
- `ILBDockAuthorityProviderV002`
- `ILBSafetyAuthorityProviderV002`

Provider slots cannot be replaced while the registered provider remains live.
They are weak references and therefore fail closed if the provider expires;
explicit unregister remains the normal lifecycle path. Registration rejects
providers from a different Unreal world. Initial route, commissioning, fault,
sensor, task and work issuance/validation now receives the owning actor, and
all actor-bound proof use rejects cross-world actors. Route
grants, dock proofs, work grants, outrigger
proofs, travel proofs and tool-coupling proofs are plain C++ structs rather than
Blueprint structs. Proofs bind to unit, route/dock/work-point/permit/task IDs as
applicable and are revalidated during use.

If a provider reports success/failure with a malformed or identity-mismatched
route grant, dock proof or work grant, the registry releases/revokes any returned
reservation before discarding it. Requesting a second dock proof while one is
active is rejected, preventing a silent overwrite of the first dock reservation.

The trusted route provider, rather than the robot component, owns route-catalog
certification, corridor containment and actual swept movement. A named route
destination never sets the robot docked. Alignment, charge contacts, network,
parking brake and leak sensors must all be proved and continuously revalidated
by the dock provider before charging.

## State and restore rules

Commissioning is explicit and cannot skip stages:

`Mothballed -> Inspection -> RepairRequired/ReadyForTest -> ManualCommissioning`

CR01 then enters `RouteValidation`; MR01 must enter and complete `Calibration`
first. Every transition consumes evidence validated by the native safety
provider. Final certification does not itself clear route revalidation.

Battery health defaults to unknown (`0`) and now inhibits final certification
and route dispatch. A native-only, safety-provider-validated battery service
result records finite 0-100% state-of-charge/health; zero remains valid
diagnostic data but cannot be treated as operational health. Dispatch also
requires charge above the 15% route reserve.

Restore accepts only finite, versioned data. It never applies the diagnostic
saved transform or observed arm/mast pose. It revokes/clears:

- route and dock authority;
- active tasks and permits;
- sensor-coverage proof;
- travel, work, tool-coupling, outrigger and arm-parking proof;
- commanded cleaning motion and water flow.

The restored component enters `SafetyStop`. If no common fault was saved it
sets `RestoreRevalidationRequired`; otherwise it preserves the saved common
fault rather than hiding it. Fresh trusted fault clearance as applicable and
stopped route revalidation are required. CR/MR persisted fault identities and physical
inventory observations may be shown in UI, but never become authority.

Restore application is deliberately native-only. Blueprint may capture and
serialize the reflected DTOs, but cannot apply a fabricated DTO to skip manual
commissioning, MR calibration or final certification. Common and variant
restore paths reject out-of-range resource/health/pose observations and reject
contradictory `Certified` / `Commissioned` state.

Fault clear uses a two-phase order: validate common and variant clearance first,
commit the variant clear second, then clear the common fault. It never calls a
variant travel-permissive function while the variant fault is still active.

## Pack contract encoded

- CR01: 120 L clean water, 130 L recovery, 45 L hopper, 1.35 m swath,
  250/180/300 rpm brush families and separate 25-35 mm/s / 25 deg/s mechanism
  rates. Dry sweep does not require clean water; wet scrub does. Sensor coverage
  and an active cleaning task's zone/evidence are revalidated through the native
  safety provider while the route is in use; safe-stop clears both proofs.
- MR01: exact F01-F22 and T1-T8 identifiers, four independently driven corner
  wheel modules using the linked RP01 wheel/hub family, 400 mm lift and published joint
  limits, finite continuous J6, 45-degree carousel indices, 350 mm straight
  withdrawal, 12 mm clamp travel, 12 kg tool limit and 25 kg combined tool plus
  handled-payload limit.
- Approved MR01 mobility override: 0.1/0.2/0.6/1.2/2.0 m/s with 0.35/0.8/1.2
  m/s2 occupied/normal/emergency acceleration. Emergency speed additionally
  requires a fully stowed mast.
- MR01 revalidates work and tool authority while waiting for explicit outrigger
  deployment, but only requires the four-load outrigger proof before arm motion
  or task completion. Lost work/tool/outrigger proof maps to the relevant F-code,
  and an overweight issued work grant is revoked before rejection.
- Open gates, open trapped-key boundaries, suspended-load zones, low traction,
  spills and protective-field intrusions always safe-stop. Shared-aisle
  occupancy is a distinct, trusted derate input.

## Open gates and known gaps

The current strict native package gate passes in `B/V2C5`:

- UnrealHeaderTool;
- UnrealEditor Win64 Development;
- UnrealGame Win64 Development;
- UnrealGame Win64 Shipping;
- strict includes, no PCH/shared PCH, and unity disabled.

Evidence:

`Saved/Audits/lb_support_robot_runtime_v002_build_v2c5.json`

This proves compilation only. All items below remain open and block promotion:

1. No production native route, dock, safety or cleaning-process provider implementation exists. The v002 cleaning-process provider interface and registry contract now compile, but no production provider is registered or runtime-proven.
2. MR01 tool coupling/return is now transactionally represented, but still
   needs a production safety-provider implementation and runtime fault tests.
3. No route-catalog, nav-corridor, replication/server-authority or movement
   adapter has been integrated.
4. No v002 component is attached to the accepted RP01/CR01/MR01 Blueprints.
5. The accepted RP01 Pawn has no promoted simple collision or movement
   component; v002 intentionally does not invent either.
6. CR01 visual animation and provider-owned water/recovery/hopper/wear/coverage
   progression, plus dock actor M28-M30, remain open for live runtime proof.
7. MR01 arm/mast/outrigger motion adapters, collision/swept-volume checks,
   exceptional 180-degree parking motion and dock actor M35-M37 are open.
8. MR01's four-wheel design decision is resolved by the supplied numeric
   authority. Its four corner modules still require Unreal integration,
   steering/movement implementation, collision and runtime validation.
9. The native save coordinator, SaveGame disk serialization, fresh-process
   round trip and corrupt-save tests are open.
10. AI/logistics, HMI, work orders, audio, materials and condition-state visual
    binding are open.
11. Collision, navigation, docking, route-intrusion and fault-injection runtime
    automation are open.
12. Fresh fixed-camera Unreal screenshots against Pro references are open.

Source-level audit:

`Scripts/audit_lb_support_robot_runtime_v002_source.py`

Expected report:

`Saved/Audits/lb_support_robot_runtime_v002_source_audit.json`

The source audit can pass while every native/runtime/visual gate remains open.
It always reports `promotion_authorized: false`.

Independent semantic review:

`Saved/Audits/lb_support_robot_runtime_v002_independent_semantic_review.json`

## v2c5 cleaning-process authority addition

`ILBCleaningProcessAuthorityProviderV002` now owns issued cleaning mode and
monotonic measured process samples. The registry issues, revalidates, samples
and revokes same-world task grants; callers no longer supply a wet/dry mode
boolean or directly advance coverage and consumables. Replayed sequences,
non-finite values, capacity violations and speed/swath-implausible samples
safe-stop with `ProcessAuthorityFault`.

This is an interface/registry and strict-compilation gate only. There is no
registered production provider or live robot proof, and the plugin remains
disabled, absent from the project descriptor and unpromoted.
