# Press shop — release-standard implementation note, 2026-08-16

The press department of the OneFactory Moorcross Works map, worked against the
[feature-finish checklist](../ReleaseGate/FEATURE_FINISH_CHECKLIST.md) and the
[visual standard's release acceptance](../LINE_BOSS_FACTORY_VISUAL_STANDARD_v001.md).
Per the checklist's own rule, unclosed items are marked openly rather than
silently omitted.

## What was done

**The detailed press train stands in the bay.** The 2026-08-15 recovery design
prepared everything and was never executed. The v449 complete runtime visual —
the accepted v438 Train A as one 306-section mesh with 13 pinned materials — is
now anchored at the committed `ConfigurablePressTrain` station transform with its
pinned datum-local transform (9.25, 2367.5, 0; rotation zero; scale 100).
Verified by registered world bounds: 13.6 × 57.7 × 9.4 m centred on the datum.
The 268-primitive blockout is hidden on commission, reversibly
(`LB.OneFactory.PressBlockout 1`), exactly as the recovery doc specifies.

**Press composition is functional, not generic.** Wrapped coils on adjustable
stands at inbound receiving (2) and coil store (3); staged stillages at panel
dispatch; the inspection light ramp at the panel-inspection quality gate; no
generic cabinets, guarding or conveyor that would interpenetrate the train.

**Lighting moved to the documented standard.** 5000 K fixtures and key light,
fixed −0.50 exposure bias on the management camera, department concrete aprons
over the authored near-black floor areas. Two mistakes made and corrected on the
way: clamping the adaptation range (the standard pins the *bias*, not the
adaptation) turned interiors black; and the one-off 306-section train at scale
100 required a plain static-mesh component — an ISM instance of it never
rendered.

**Save/reload is exact.** Saved mid-press-output at
`BodyFraming / OF_BODY_WELD_POS_01 / 7/57 / cycle 25%`, ran 400 further
simulated seconds to `15/57`, loaded, and returned to precisely the saved state
— station, stage, cursor and mid-cycle progress — with one unit, no duplicate
WIP, and all four presentation pairs rebuilt atomically
(`ONEFACTORY RESTORE COMMITTED; FOUR PRESENTATION PAIRS REBUILT`). Bound to
F5/F9 and Exec-callable.

## Checklist position

| Section | Position |
|---|---|
| 1. Outcome and authority | **Pass** — press layout authority owns state; coordinator owns runtime; presentation holds none. |
| 2. Gameplay integration | **Partial** — flow, buffers, blocking and quality events work and are tested; unlock/price/refund progression is not wired into this shell. |
| 3. UX and feedback | **Partial** — keyboard reaches every action; HUD states distinct; controller input, inspector and multi-resolution captures open. |
| 4. Visual and asset quality | **Partial** — v449 is pinned to the accepted v438 look with authored materials; formal promotion to the owned `DetailedPresentation_v001` root (copy-and-rebind) remains, as does the grouped 337-component renderer for selection and animation seams. |
| 5. Save and reliability | **Pass in editor, packaged proof in flight** — exact round-trip shown above; packaged round-trip is the v004 verification. |
| 6. Localization | **Open** — HUD text is hard-coded English, as project-wide. |
| 7. Verification and performance | **Partial** — 275/275 suite green; packaged journey green in v003; performance budget not yet agreed or measured. |
| 8. Documentation | **This note**, plus the recovery doc and commit trail. |

## Honest deviations from the recovery design

The recovery doc's full design is an internal revision of the frozen press
presentation with a two-phase staging commit and promotion to an owned content
root. What stands today is the doc's own sanctioned *first fidelity release*
(the v449 fallback) delivered through the dev dressing overlay, with the
blockout hidden at runtime rather than retired inside the presentation class.
The difference matters for selection/highlight and future animation, not for
the accepted look. The full internal revision — owned-root promotion, staged
`ConfigureFromLayout`, updated exact-pair contract and regenerated tests — is
the deliberate next step and should not be done quietly.

## Remaining before "release standard" can be claimed without caveats

1. Packaged v004 round-trip evidence (in flight at time of writing).
2. Promotion of v449 into the owned `DetailedPresentation_v001` root.
3. The internal presentation revision per the recovery design, as a versioned
   contract change with tests.
4. Multi-resolution captures, performance numbers, and the project-wide
   localization item.
