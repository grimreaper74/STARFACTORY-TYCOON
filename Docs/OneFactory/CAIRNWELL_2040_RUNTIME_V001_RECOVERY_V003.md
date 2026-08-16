# Cairnwell2040Runtime_v001 chained recovery v003

Status: `OFFLINE_PREPARED__UNREAL_NOT_LAUNCHED`

Recovery v003 preserves both prior failed runs and both package generations. It
never edits v001/v002 evidence and performs no deletion, overwrite, reimport,
project-map load/save, Source/Config/save change, runtime binding, or panel-lane
operation.

## Pinned v002 incident

The exact v002 run is
`Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/UnrealImportLane_v001/Recovery_v002/20260815T103132Z-3fc39714`.

- `import_failure_recovery_v002.json`: SHA-256
  `86AB67E0AD2C501EE8E49CFAF6061694DD78DFD616B81F22B53B80896E127EE1`,
  status
  `FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002_UNREAL_IMPORT`.
- `lane_summary_recovery_v002.json`: SHA-256
  `D152B33365F3CCBE005E7552468FDE90628AEBB21371A93831A7187BEF2146D6`.
- `quarantine_receipt_v002.json`: SHA-256
  `61185A4AF74711FEAD0E67D4026522BF5C48CB48D73CCCC0BAB76DE4A8F0CC57`.
- Import abslog/stdout/stderr SHA-256 values are respectively
  `138E4F06AC6B562325BE84EA8CEA4D6DBE27CCE6140FA718C9A6C6164487BB08`,
  `DCBE73E2CA83CD6BAD6EC18ECC29983D1D20F2E82618642D7609C740BF927B69`,
  and the empty-file hash
  `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`.

The original v001 four-package output remains byte-exact in its v001
quarantine. The v002 destination contains exactly seven fresh packages: three
textures and four materials. Their paths, bytes, mtimes, and hashes are pinned
by the v003 contract and must match the v002 failure receipt before they can be
moved.

## Exact material-slot diagnosis and normalization

All three pinned `BIW_AutomotiveSkeleton` FBXs contain exactly one raw material
name `MI_LB_C2040_BIW_GalvanisedSteel_v005.001`. No source FBX contains the
observed `_001` spelling. Installed UE5.8
`FbxMainImport.cpp:1870-1888` proves `FFbxImporter::MakeName` replaces the exact
special characters `. , / ` %` with underscores. Its inspected SHA-256 is
`506DE36CC110B754D70800E964A6BCF8D38D304B94C8D8AE3E947B0351B99EF8`.

Therefore v003 accepts only this exact chain:

`MI_LB_C2040_BIW_GalvanisedSteel_v005.001` source ->
`MI_LB_C2040_BIW_GalvanisedSteel_v005_001` UE imported identity ->
`MI_LB_C2040_BIW_GalvanisedSteel_v005` canonical gameplay slot.

The importer changes only `MaterialSlotName`, preserving the exact sanitized
`ImportedMaterialSlotName` for source/reimport identity. It requires one static
material and one occurrence in each LOD source. The other three roles must
already match their canonical slot exactly; suffix stripping or fuzzy matching
is forbidden.

## Redirected-log lock correction

The primary importer failure occurred normally, but the wrapper then attempted
`Get-FileHash` while Windows still held redirected stdout open. v003 uses
`Get-LBFileEvidenceWithBoundedReadRetry`: each attempt first performs a real
read-open, retries only after `IOException`/`UnauthorizedAccessException`, uses
bounded exponential backoff, and fails after 15 seconds. The same successfully
opened stream supplies bytes, SHA-256, and text for fatal-pattern scanning.
Process exit code 0 and clean fatal/ensure/ModeManager logs remain mandatory.

## Recoverable quarantine and receipts

The exact seven-package destination is moved once, as a whole directory, to:

`Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/Incident_20260815T103132Z-3fc39714_v002`.

Recovery runs use
`Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/UnrealImportLane_v001/Recovery_v003/<UTC>-<GUID8>`.

- `quarantine_receipt_v003.json`:
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v003/quarantine/v3`.
- `import_receipt_recovery_v003.json`:
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v003/unreal-import/v3`.
- `fresh_process_validation_receipt_recovery_v003.json`:
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v003/fresh-process-validation/v3`.
- `lane_summary_recovery_v003.json`:
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v003/import-lane-summary/v3`.

Every receipt binds both failed run IDs and import-failure hashes, the frozen
v003 recovery-contract hash, `incident_chain_sha256`, and the exact v003
quarantine receipt.

Reviewed command shape, not executed by preparation:

```powershell
& 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_cairnwell_2040_runtime_import_lane_v001.ps1' -Acknowledgement RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V003_ONCE
```
