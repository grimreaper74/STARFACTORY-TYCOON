# Press Shop quirky visual direction v001

## Decision

The preserved four-train Press Shop is the recovery and process-reference source, not the target release art density.

The player-facing Press department belongs inside the single shared factory defined by `Docs/LINE_BOSS_FACTORY_VISUAL_STANDARD_v001.md`. It should show one large, readable production flow at management-camera scale:

1. The Line Boss coil-unloading area and a compact coil buffer.
2. The existing procedural Coil AGV moving material into production.
3. One chunky decoiler.
4. Four large press modules with visibly different silhouettes.
5. Inspection.
6. Outbound stillages.

The detailed lorry and Coil FLT candidates are retired from the release path and retained only as archive/reference evidence.

## Visual rules

- Near-future 2040 automation in Cairnwell Green, Safety Yellow, graphite and warm grey.
- Low-poly, rounded, slightly exaggerated industrial forms.
- Large painted floor zones and clear process spacing.
- Keep only fences and guards that communicate gameplay boundaries.
- Keep one simplified automated overhead handling silhouette where the process needs it.
- Remove dense roof trusses, forests of columns, tiny pipes, cables, repeated micro-railings and dark voids.
- Every station and process state must be identifiable at a glance without zooming in.
- Follow the one-factory lighting and camera standard; do not give Press a separate visual treatment.

## Preserved evidence

- Restored source map: `/Game/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001`
- Restored map SHA-256: `D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5`
- Fresh validation receipt: `Saved/Audits/PressShopRestoration/FullFactoryRestored_v001/independent_validation_v001.json`
- Recovery captures: `Saved/ValidationScreenshots/PressShop/FullFactoryRestored_v001/`

## Concept

- Image: `Saved/Concepts/PressShop/LB_PressShop_QuirkySimplified_Concept_v001.png`
- SHA-256: `ABA79127E6CE810E899C288E84D477A726A526C3C9E87698CDD5FEFF47DDEC99`

This concept is visual-direction evidence only. It is not an Unreal asset, production geometry or a release screenshot. Product pricing is deliberately not fixed by this document; it will be set later from the completed scope, player value and market evidence.

## Generation prompt

> Use the recovered Unreal Press Shop only as layout and process reference, then redesign it for a clean stylised near-future factory-management game. Show one bright isometric automotive Press flow: Line Boss coil unloading and buffer, the procedural Coil AGV, one chunky decoiler, four large distinct press modules, inspection and outbound stillages, plus one simplified automated overhead-handling silhouette. Use low-poly rounded industrial forms, Cairnwell dark green, safety yellow and warm grey concrete. Remove the detailed lorry and Coil FLT, dense roof trusses, forests of columns, tiny pipes, cables, micro-railings, dark voids and photoreal detail. Keep only gameplay-relevant fences. Every station must read at a glance. No UI, labels, text, logos or watermark.
