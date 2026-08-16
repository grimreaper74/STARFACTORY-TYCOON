# Line Boss asset catalog

This directory has two complementary authorities:

1. `master_asset_catalog.json` / `.csv` — the curated family register. It explains what each important family actually is, its best authority, lifecycle/runtime status, audit path, Content path (when verified) and next action.
2. `sourceassets_file_ledger.jsonl` / `.csv` — the exhaustive loss/integrity register for every file under `SourceAssets`, including relative path, byte size, UTC modification time, SHA-256, extension and nearest manifest folder where one can be resolved.

`meshy_files_received_2026-08-12.csv` is the exact 21-file receipt register for today's seven Meshy families. `MESHY_RECONCILIATION_2026-08-12.md` is the evidence-backed human summary. `sourceassets_manifest_index.json` / `.csv` discovers every manifest-bearing SourceAssets folder so less prominent families are not hidden by the curated front page.

`sourceassets_duplicate_hash_groups.json` / `.csv` is the SHA-256 duplicate-content index. It is evidence for review only: a repeated hash can be an intentional authority/intake/audit copy and does not authorize deletion.

## Verified snapshot (2026-08-12)

- SourceAssets files: `5,990`
- Total bytes: `39,833,778,358` (`37.098 GiB`)
- Ledger SHA-256: `008E226C9607155EAA31BCDD33BE0D4D0EDECAC8484D577D008319DE4D0E6733`
- CSV SHA-256: `CEE8379586A19FE4503CB7BA7E2948B32CB38521F66511459FDDBCD13893E1C1`
- Duplicate-content groups: `194` (`453` files; `259` extra copies)
- Potential bytes beyond one copy per group: `205,820,434` (review only; do not assume reclaimable)
- Standard validation: `PASS` (`5,990 / 5,990`, zero errors)
- Full SHA-256 validation: `PASS` (`5,990 / 5,990`, zero errors or hash mismatches)

The latest validation evidence is saved in `sourceassets_validation_result.json` and `sourceassets_validation_result_full.json`.

## Status vocabulary

- `REFERENCE_ONLY_RUNTIME_BLOCKED` — preserved visual/engineering evidence; raw source is not approved for runtime.
- `RUNTIME_CANDIDATE_NOT_IMPORTED` — optimized or runtime-oriented source exists, but no verified Unreal import authority.
- `UNREAL_IMPORTED_CANDIDATE` — candidate Content assets exist; this does not imply final shipping promotion.
- `REJECTED_DO_NOT_USE` — retained only for provenance/negative evidence.
- `CURATED_SOURCE_AUTHORITY` — source/manifest authority with runtime status stated separately.

Role verdicts are `PASS`, `CONCEPT_PASS_EXACT_BLOCKED`, `PARTIAL`, `WRONG_ROLE` and `REJECTED`.

## Repeatable scanning and validation

Run from PowerShell:

```powershell
& '.\Docs\AssetCatalog\Scripts\scan_source_assets.ps1' -Mode Scan
& '.\Docs\AssetCatalog\Scripts\scan_source_assets.ps1' -Mode Validate
& '.\Docs\AssetCatalog\Scripts\scan_source_assets.ps1' -Mode Validate -FullHashValidation
```

`Scan` is deterministic and resumable. It sorts normalized relative paths, reuses an existing hash only when both byte size and UTC modification time still match, and writes checkpoints during long scans. The final ledger is replaced atomically. `Validate` checks ledger membership, paths, sizes and timestamps plus every curated source/path; `-FullHashValidation` re-hashes every SourceAssets file.

Regenerate the curated CSV projections after hand-editing the JSON:

```powershell
& '.\Docs\AssetCatalog\Scripts\export_master_catalog_csv.ps1'
```

The scanner is read-only with respect to `SourceAssets`, `Content`, C++ and Unreal. Its only writes are catalog artifacts under this directory.
