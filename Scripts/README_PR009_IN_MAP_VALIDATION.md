# PR-009 in-map technical verification

Run `run_press_shop_pr009_in_map_validation.ps1` from PowerShell. The suite builds the native editor target, runs the established PR-009 and PR-008-to-PR-009 automation tests, audits the map, runs process/motion and navigation checks in PIE, snapshots protected files, and emits one consolidated JSON result.

The only map-selection authority is `TARGET_MAP` in `press_shop_pr009_in_map_validation_config.py`. To retarget a later v085 map, change that one constant; output folders and actor prefixes derive from its `_vNNN` suffix.

Outputs are written under:

- `Saved/Audits/PR009_InMap_vNNN/`
- `Saved/Automation/PR009_InMap_vNNN/`
- `Saved/Logs/PR009_InMap_vNNN/`

The suite never saves the loaded map. Before/after SHA-256 snapshots cover the target map, the two handoff documents, protected PR-004 maps and every repository file whose path contains PR010. `promotion_authorized` is always false.

The one-time `repair_press_shop_pr009_material_flow_singleton.py` and `repair_press_shop_pr009_navigation_coverage.py` scripts are intentionally separate from the validator. They record their own audit JSON and save only the configured v084 map. The navigation repair adds invisible local coverage plus a `NavArea_Null` protected-process-space exclusion; it does not alter visible station geometry. The corrected v084 integration builder contains the same singleton-binding and navigation-authoring behavior so a rebuild does not regress either fix.

Collision gate semantics are deliberate: complete blocking/profile evidence may pass the technical gate while `release_collision_ready=false` records temporary complex-as-simple coverage. That status is not release approval.
