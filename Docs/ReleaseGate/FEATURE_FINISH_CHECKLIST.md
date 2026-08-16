# Feature-finish checklist

Copy this checklist into the feature's implementation note. A feature may be
called **finished** only when every applicable item is checked with a link to
current evidence. Use `N/A — reason` rather than silently omitting a gate.

## 1. Player outcome and authority

- [ ] One-sentence player outcome and failure/recovery path are documented.
- [ ] Exactly one authoritative owner exists for state, identity and mutation.
- [ ] Invariants, stable IDs, units, capacities and idempotency rules are explicit.
- [ ] The implementation advances the full game direction, not only a test stub.

## 2. Gameplay integration

- [ ] Unlock, price, purchase/refund and progression consequences are connected.
- [ ] Upstream inputs, buffers, downstream outputs and shortage/blocking behaviour work.
- [ ] Quality, maintenance, research, finance and analytics receive exact events once.
- [ ] Automatic routes/markings are legal, readable and player-editable.
- [ ] No actor clips through machines, routes, doors, storage or service envelopes.

## 3. UX, controls and feedback

- [ ] Mouse, keyboard and controller reach every essential action.
- [ ] Valid, invalid, selected, waiting, starved, blocked, fault and maintenance states are distinct.
- [ ] Inspector, alert jump/focus, disabled reason and recovery instruction are present.
- [ ] Camera framing, zoom and placement remain comfortable at small and large factory scale.
- [ ] 720p, 1080p and 4K/UI-scale captures pass readability and colour-independent checks.

## 4. Visual, asset and audio quality

- [ ] Exact runtime asset is promoted through every state in the asset-provenance gate.
- [ ] Pivots, moving hierarchy, LODs, collision, materials and brighter player-livery masks pass.
- [ ] Safety colours, tools, labels, lenses and emergency controls remain protected.
- [ ] Lights, beacons, VFX and SFX follow gameplay state and are visible/audible in package.
- [ ] Asset rights, private-AI generation records, reference licences and Steam classification are archived.

## 5. Save, migration and reliability

- [ ] Current root captures/preflights/restores the feature transactionally.
- [ ] New campaign, current-version round trip and every supported legacy migration pass.
- [ ] Invalid data is rejected before mutation; duplicate IDs/events cannot duplicate value.
- [ ] Save, exit, process restart, load and the next gameplay event pass in package.
- [ ] No crash, assert, missing asset, hidden fallback or unexpected warning remains.

## 6. Localization and accessibility

- [ ] All player-facing text is gatherable `FText`/string-table content.
- [ ] Layout expansion, CJK font coverage, numbers/units and glossary terms are tested.
- [ ] Important colour/audio information has text/icon/caption equivalents.
- [ ] Store language/audio claims match the packaged culture and actual voice coverage.

## 7. Verification and performance

- [ ] Focused tests pass.
- [ ] Affected subsystem and full campaign suites pass with no unexplained warnings.
- [ ] A fresh package of the exact revision passes the complete player journey.
- [ ] Representative-scale CPU/GPU frame time, memory, draw calls, actor count and navigation are within an agreed budget.
- [ ] Screenshots/video, logs, reports, executable hash and source/content manifest are archived under one build ID.

## 8. Documentation and handoff

- [ ] Gameplay/status, controls/UI, save/version and asset provenance docs are updated.
- [ ] Known limitations are explicit; validation-only work is not labelled playable.
- [ ] Test/report/package links resolve from the repository.
- [ ] Another developer can reproduce the validation from the documented commands and inputs.
- [ ] The release-gate index is updated to the new evidence date/build ID.

## Current project-wide blockers

- [ ] Archive the live-green exact physical stillage FLT delivery as an indexed report and prove it in package.
- [ ] Supersede the red v16 report with green v17 legacy/player-built round trips plus v13-v16 migrations.
- [ ] Archive the live-green 24-test management/runtime suite, then prove finance/research/quality/maintenance/analytics integration in a packaged journey.
- [ ] Archive the live-green 24-test FactoryBuilder suite; triage or formally accept its one RHI allocation warning and six synthetic-world teardown warnings.
- [ ] Validate and package the source-present seven-page responsive management UI with input parity.
- [x] Add authorised first-build framing, recognisable placement model ghosts and richer decision-ready catalogue cards in source with focused tests.
- [ ] Accept the camera/ghost/catalogue changes in a fresh packaged journey at 720p, 1080p and 4K.
- [ ] Soften the broad directional shadow bands, then repeat visual/accessibility captures at 720p, 1080p and 4K.
- [ ] Rerun or formally account for the historical context-less world-destroy warnings from the earlier successful press identity selection.
- [ ] Promote a weld vertical slice, then ED/paint and assembly, from licensed optimized assets.
- [ ] Convert HUD text to localization-ready architecture; do not claim voice languages.
- [x] Produce the fresh v1031 Shipping build/archive and verify its observed runtime has no TCP/UDP listener.
- [ ] Complete the v1031 fresh/populated gameplay, save/restart and performance audit.
