# Body Shop Robot Candidate Decision v001

**Decision date:** 2026-08-14  
**Scope:** read-only comparison of two user-supplied Meshy GLBs as replacements for the current Body Shop resistance spot-welding robot.  
**Decision:** neither candidate is eligible to replace the Weld robot. Retain candidate 1 only as a possible future MIG/arc-welding source asset; reject candidate 2 for production use and retain its audit as evidence. Request a new Meshy iteration built explicitly around a large C-gun and rigid, separated joints.

## Required replacement contract

The replacement must provide all of the following before import or promotion:

- approximately 3.4 m horizontal reach and 2.7 m overall robot height, measured on the robot itself rather than a helper object;
- six-axis industrial articulation with rigid, separately selectable base, shoulder, upper arm, elbow, forearm, wrist links and tool flange;
- a clearly modelled large C-shaped resistance spot-welding gun, open jaws and two opposed copper electrode tips—not a MIG/TIG torch or hose nozzle;
- complete PBR materials and textures suitable for the existing Weld presentation;
- a practical game triangle budget with generated LODs, rather than an approximately 600,000-triangle source used directly at every viewing distance;
- provenance sufficient for promotion: exact source hash plus the associated Meshy generation/export record and usage rights;
- verified electrode contact. The current Weld acceptance remains at most 12 cm from the intended fixture target with tool-direction dot product at least 0.95. Geometry, targets, or sparks must not be moved or faked merely to imply contact.

## Evidence and comparison

| Requirement | Candidate 1: `Meshy_AI_Character_output.glb` | Candidate 2: `Meshy_AI_Character_output (1).glb` |
|---|---|---|
| Exact source | `C:\Users\greg_\Downloads\Meshy_AI_Character_output.glb` (61,032,108 bytes) | `C:\Users\greg_\Downloads\Meshy_AI_Character_output (1).glb` (49,022,228 bytes) |
| SHA-256 | `11A0ADE7D537C3E0FD8C41483C1F4F4F335AD933DC93AE9BFD0DAA239D35469F` | `2880D33A4D37CDB233D3455A5923C78FED1C02F0F32F27B6E20696649F539429` |
| Robot dimensions | Main mesh is only 0.901460 x 0.592391 x 1.700000 m: fails height and reach. | Main mesh is only 1.613168 x 1.239080 x 1.700000 m: fails height and reach. |
| Articulation | One continuously skinned mesh, generic 10-bone chain, no animation actions: not rigid/separable six-axis construction. | One continuously skinned mesh, generic 9-bone chain, no animation actions: not rigid/separable six-axis construction. |
| End effector | Rendered as a slim MIG/arc-welding torch: no C-gun or opposed electrodes. | Rendered as a thin hose/nozzle tool: no clear C-gun or opposed electrodes. |
| PBR | One Principled material with packed 2K base colour, 4K metallic/roughness and 2K normal maps: visually useful. | Zero materials and zero images: fails the PBR requirement. |
| Runtime geometry | Main mesh 432,127 vertices / 593,967 triangles; no supplied LOD evidence: fails the direct-runtime budget. | Main mesh 805,261 vertices / 595,373 triangles; no supplied LOD evidence: fails the direct-runtime budget and has substantially more vertices. |
| Provenance | Exact bits are pinned and the user identifies the source as their Meshy generation. The audit does not contain a generation/export receipt or rights record, so promotion provenance remains incomplete. | Same provisional provenance status; exact bits are pinned, but the generation/export receipt and rights record are not part of the audit. |
| Spot-weld contact | Cannot be accepted or placed as if it contacts the underbody because it lacks the required gun and reach. | Cannot be accepted or placed as if it contacts the underbody because it lacks the required gun and reach. |
| Disposition | **Retain, but not for this role:** isolate as a possible future MIG/arc-welding source candidate, then optimize and validate separately before any use. | **Reject for production:** retain only the source hash, audit and renders; it is not an upgrade over candidate 1. |

Both exports also contain a visible, unparented 42-vertex/80-triangle `Icosphere` with 2.0 m diameter. It expands each reported scene envelope to 1.902116 x 2.000000 x 2.700000 m, but it is not robot reach or robot height and must not be used as acceptance evidence.

## Authoritative audit and render paths

Candidate 1:

- audit: `Saved/Audits/BodyShop/RobotCandidate_v001/Meshy_AI_Character_output/audit.json`
- renders: `Saved/Audits/BodyShop/RobotCandidate_v001/Meshy_AI_Character_output/01_isometric.png`, `02_front.png`, `03_side.png`, `04_top.png`

Candidate 2:

- audit: `Saved/Audits/BodyShop/RobotCandidate_v001/Meshy_AI_Character_output_1/audit.json`
- renders: `Saved/Audits/BodyShop/RobotCandidate_v001/Meshy_AI_Character_output_1/01_isometric.png`, `02_front.png`, `03_side.png`, `04_top.png`

These are read-only audit artifacts. No candidate was imported into project Content and neither changes the currently verified Weld cell.

## Next Meshy iteration

Generate a new floor-mounted, heavy-payload six-axis **resistance spot-welding** robot at true 3.4 m reach / 2.7 m height. Require Auto Split and visibly separate rigid links with gaps and cylindrical pivots. State repeatedly that the end effector is a large open C-shaped clamp with two opposed copper electrode tips and that MIG/TIG torches and hose nozzles are forbidden. Exclude platforms, fences, frames, backgrounds, text and workpieces.

Use quad topology as the editable source, but do not choose a high face count as the acceptance criterion. Preserve the best-looking source, reduce each separated rigid part independently, triangulate for the measured Unreal budget, and generate management-view LODs. Before promotion, rerun the same audit, remove helper geometry, verify PBR maps and provenance, inspect all six pivots, and prove the electrode proximity/direction gate in the actual Weld fixture. Until all gates pass, the verified current robot remains in place and the known contact limitation remains explicit.
