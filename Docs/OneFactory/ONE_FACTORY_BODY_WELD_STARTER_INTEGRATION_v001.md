# OneFactory Body/Weld starter integration contract v001

This tranche is a NativeOnly, player-created Body/Weld starter for the
Moorcross Works Body bay. It is intentionally isolated from maps, Content,
Config, saves, HUD/Canvas code and the shared player builder.

## Frozen production contract

- Authority class:
  `ALBOneFactoryBodyWeldStarterLayoutAuthority`
- Presentation class:
  `ALBOneFactoryBodyWeldStarterPresentationActor`
- Stable layout ID:
  `MOORCROSS_BODY_WELD_STARTER_NATIVE_V001`
- Exact process:
  18 configurable positions, 18 ordered programmes and 17 sequential routes,
  accepting `PressedPanelSet` and handing off `BodyInWhite`.
- Robot contract:
  every installed position has one explicit mirrored pair of large six-axis
  robots. Both side duties are reassigned together by
  `AssignRobotPairRoles`; the candidate must retain every programme's required
  robot duty.
- Mutation contract:
  `AssignProgramme`, `AssignRobotPairRoles`, `MoveStation`, `RestoreLayout`
  and `Commission` preflight a copy and commit only a complete valid state.
  Programme, role and movement changes clear commission. Any active or
  reserved unit blocks configuration and commissioning.
- Save contract:
  persist only `FLBOneFactoryBodyWeldLayoutState`. Presentation actors,
  HISM instances, semantic materials, decorative full stillages and any
  vehicle-shaped proxy are never persisted as WIP.

## Frozen presentation contract

The presentation resolves all dependencies before exposing instances and
clears atomically on any failure. The canonical layout produces 24 HISM
batches and 469 visual instances, including 36 seven-link robots, 16 C-guns,
all 12 support-kit meshes, 18 programme fixtures, 17 route marks, 36 role
markers and 18 status markers. Role-compatible reassignments may change the
C-gun count; exact expected counts are derived from the committed snapshot.

Allowed authored roots are only:

- `/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/`
- `/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/`

Engine Cube and BasicShapeMaterial supply the four semantic batches. Meshy,
RuntimeGLB, external-generated, legacy underbody-slice and old runtime
BodyWeldLine references fail closed.

## Later shared PlayerBuilder wiring

The shared builder should perform these steps as one transaction:

1. Spawn exactly one Body/Weld authority and exactly one presentation actor.
2. Configure presentation only from `Authority->CaptureLayout()`.
3. On programme, robot-role or movement edits, mutate the authority first;
   rebuild presentation only after the mutation succeeds.
4. On presentation failure, clear/destroy both newly created actors and leave
   the previous committed player state unchanged.
5. Expose player actions for programme assignment, mirrored role assignment,
   movement, delete and commission. Never create logical WIP from the
   presentation actor.
6. Feed real pressed-panel identities into the later production coordinator
   and emit the same `UnitId` as `BodyInWhite`; this starter does not invent a
   second WIP authority.

The intended lifecycle seam is Press -> Body/Weld -> Paint -> Assembly.
