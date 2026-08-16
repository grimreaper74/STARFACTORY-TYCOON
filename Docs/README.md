# Line Boss documentation index

This is the starting point for current implementation and release status. It is a
snapshot of the working tree on **2026-08-11**; it does not turn a source asset,
passing unit test, or editor preview into a packaged-playable feature.

## Release authority

Read these files in order:

1. [Current gameplay status](ReleaseGate/CURRENT_GAMEPLAY_STATUS.md) — what is
   playable, validation-only, source-only, or planned.
2. [Controls and management UI](ReleaseGate/CONTROLS_AND_MANAGEMENT_UI.md) —
   current bindings and the management-screen target.
3. [Save compatibility](ReleaseGate/SAVE_COMPATIBILITY.md) — the checked-in v17
   topology/management contract, v13-v16 migration rules, and the validation
   still required before any compatibility claim.
4. [Asset provenance and promotion](ReleaseGate/ASSET_PROVENANCE_AND_PROMOTION.md)
   — source ownership, private Meshy generations, AI disclosure, and promotion
   states.
5. [Validation evidence](ReleaseGate/VALIDATION_EVIDENCE.md) — exact green and
   red reports plus the last proven Windows package.
6. [Unreal MCP editor operations](ReleaseGate/UNREAL_MCP_OPERATIONS.md) — the
   experimental localhost editor integration, safe operating procedure, schema
   workaround, and live diagnostic results.
7. [Localization and audio](ReleaseGate/LOCALIZATION_AND_AUDIO.md) — no current
   voice acting, localization blockers, and the staged language target.
8. [Feature-finish checklist](ReleaseGate/FEATURE_FINISH_CHECKLIST.md) — the
   mandatory definition of done.
9. [Modular factory asset development standard](ReleaseGate/MODULAR_FACTORY_ASSET_DEVELOPMENT_STANDARD.md) —
   construction, material, LOD, generated-source and promotion rules for robots,
   tools, fixtures, machines and reusable factory modules.

## Status vocabulary

| Status | Meaning |
|---|---|
| **Packaged playable** | The named journey was exercised in the named packaged build. The claim applies only to that package revision. |
| **Validation-only** | Code or content exists and has focused editor/source evidence, but the latest integrated journey has not passed in a fresh package. |
| **Source candidate** | Editable source/export exists; it is not an approved Unreal runtime asset. |
| **Planned** | Direction or contract only. It must not be presented as implemented. |

The strongest evidence wins. A later failing integration test overrides an older
green component test until the failure is fixed and rerun.

## Other authorities

Design intent remains in documents such as
[Press Trains implementation authority](PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md),
[PR-010 implementation authority](PR010_IMPLEMENTATION_AUTHORITY.md), and
[brand identity authority](BRAND_IDENTITY_AUTHORITY.md). Historical handovers
and dated audits are context, not current completion evidence. In particular,
the large `PROJECT_HANDOFF.md` and `NEW_CHAT_HANDOVER_2026-08-03.md` files must
not be used to overrule the release-gate status above.
