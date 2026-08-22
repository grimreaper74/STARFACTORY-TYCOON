# Development Build R32 — playable factory proof

Package root:
`E:\LineBossValidationOutput\Builds\Development_20260821_factory_r32_playable\Windows`

R32 contains the controller-level keyboard fallback and the Paint presentation
availability correction. The latter treats a cooked static-mesh reference as
available in NullRHI validation; render-resource LOD data is deliberately not
available in that mode.

## End-to-end proof

The packaged Development executable was run on 2026-08-21 with NullRHI and
the OneFactory map. Log:

`Validation\r32_full_production_20260821_112646.log`

It exited with code 0 and recorded:

- all four departments created and commissioned;
- `LINE_BOSS_ONEFACTORY_PREBUILT_READY WHOLE FACTORY CREATED, COMMISSIONED AND VALIDATED`;
- one `CAIRNWELL_2040` order started;
- Body/Weld, Paint and Assembly quality passes;
- `LINE_BOSS_DEV_RUN ok=1 ... units=1 completed=1 dispatched=1`;
- a 57-station route, including 18 Body/Weld positions.

This validates the core development production loop. It does not promote the
development car to final art or substitute for current rendered/performance
evidence.
