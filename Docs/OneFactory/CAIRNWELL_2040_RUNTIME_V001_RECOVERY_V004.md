# Cairnwell2040Runtime_v001 chained recovery v004

Status: `OFFLINE_PREPARED__UNREAL_NOT_LAUNCHED`

Recovery v004 preserves the exact v001, v002, and v003 failed runs, the v001
four-package quarantine, the v002 seven-package quarantine, and all eleven
packages produced by v003. It performs no deletion, overwrite, reimport,
project-map load/save, Source/Config/save change, runtime binding, or panel-lane
operation during preparation.

## Exact v003 incident

The pinned run is
`Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/UnrealImportLane_v001/Recovery_v003/20260815T105958Z-79a98abc`.

- `import_failure_recovery_v003.json`: SHA-256
  `3FB3E1A8F27F1E4EF477C6F1E3E3AF41E53F2C8618CAC9A4E0A047F91BD60E7C`,
  status
  `FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V003_UNREAL_IMPORT`.
- `lane_summary_recovery_v003.json`: SHA-256
  `6771F6D980A89CF32D92B7FD1013BAF297D1003AFAEC71B6EEDE824EA8183C45`.
- `quarantine_receipt_v003.json`: SHA-256
  `1BCE465D7D8CF731CBE6F17121149A74AA550EA12E31C53EAF80D6F55A198D80`.
- Import abslog/stdout/stderr SHA-256 values are respectively
  `BC70CA39AA8EEA93AFD9BB7E67AF0AADDA6DB7AE8485AD695BD73D3B0830144C`,
  `34E586D561A7A1A9AE5C39E75F26359A8DEC4C22C94484856FCFBEB160FA1E63`,
  and
  `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`.

The redirected stdout lock correction worked: the wrapper waited for nine
real read-open attempts, captured final bytes, observed editor exit code zero,
and found no fatal/ensure/ModeManager signature. It then stopped because the
importer had truthfully emitted a failure receipt.

## Exact geometry diagnosis

The preserved v003 AutomotiveSkeleton package embeds these LOD0 StaticMesh
AssetRegistry tags:

- triangles: expected `59998`, actual `59998`;
- source vertices: `29092`, actual render vertices: `29109` and positive;
- source UV channels: expected `0`, actual Unreal render UV channels: `1`.

Thus triangulation and degenerate-face removal were not the failure. The
triangle count remained byte-for-byte exact. The MikkTSpace degenerate-tangent
and nearly-zero-binormal warnings concern tangent generation, not face removal.
The sole failed predicate was comparing a source UV count of zero to Unreal's
runtime UV count of one.

Installed UE5.8 `FbxStaticMeshImport.cpp:709-718`, SHA-256
`D6E42F80894F87E580DD72FC2EE7F9A46E312DDE1AB006F18F01A068408523C6`,
computes the source/existing UV maximum and then explicitly applies
`NumUVs = FMath::Max(1, NumUVs)` before setting both vertex-instance and
MeshDescription channel counts. Therefore both zero-source-UV BIW roles have
exact runtime UV counts `[1, 1, 1]`. Body and rolling gear already have source
UV counts `[1, 1, 1]` and remain `[1, 1, 1]` in Unreal.

Recovery v004 retains every source `uv_channels` value unchanged. It introduces
a separate exact `expected_unreal_uv_channels_by_lod` contract. This is an
engine sanitation model, not a weakened or ranged UV gate.

## Recoverable quarantine and result topology

The complete eleven-package v003 destination is moved once as a whole
directory to:

`Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/Incident_20260815T105958Z-79a98abc_v003`.

Recovery results use
`Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/UnrealImportLane_v001/Recovery_v004/<UTC>-<GUID8>`.

- `quarantine_receipt_v004.json`:
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v004/quarantine/v4`.
- `import_receipt_recovery_v004.json`:
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v004/unreal-import/v4`.
- `fresh_process_validation_receipt_recovery_v004.json`:
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v004/fresh-process-validation/v4`.
- `lane_summary_recovery_v004.json`:
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v004/import-lane-summary/v4`.

Every receipt binds all three failed run IDs/import-failure hashes, the v004
recovery-contract hash, `incident_chain_sha256`, and the v004 quarantine
receipt. Any v004 result consumes the lane; no automatic rerun is allowed.

Reviewed command shape, not executed by preparation:

```powershell
& 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_cairnwell_2040_runtime_import_lane_v001.ps1' -Acknowledgement RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V004_ONCE
```
