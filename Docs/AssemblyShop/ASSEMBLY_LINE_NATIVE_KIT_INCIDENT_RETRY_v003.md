# Assembly Line Native Kit — command-line incident retry v003

Static-only preparation complete. No Unreal, importer, UBT, or Content-writing process was launched while preparing v003.

## Why v002 did not validate

Recovery v002 passed its full offline preflight and launched a clean editor process, but its `-ExecutePythonScript` argument contained the Windows path `Scripts\revalidate...`. Unreal interpreted `\r` as a carriage return, producing `Scripts` followed by a line break and `evalidate...`. Python never opened or executed, so no package validation, Content write, asset save, import, reimport, or delete occurred.

The complete four-file failed run `20260815T030646Z-e8c9a5eb` is hash-pinned and preserved. Its log contains the exact control-character failure, while its summary proves no importer process and no PASS receipt.

The first v003 baseline also correctly failed closed when concurrent OneFactory UI work changed the two CaptureBridge files. That pre-v005 baseline is retained unchanged at SHA-256 `B465F68B5DC540B7C68EBCB6BD4C682271A2826A8841A902EC98FBAE3DCAA9B5`. The final baseline pins the explicitly frozen UI v005 bridge hashes: header `2C5442B15B94504CEA085A3F46F4740BCC4FD0A83CDE70DB37E3C7D0FC04673B` and source `849C7E1ACD6A02B27126831202E774E8C922E422050904EC3DF5349C6D01CA30`.

## v003 correction and regression gate

The v003 runner converts the validator path to an absolute `/`-separated form before constructing the argument. It fails before launch if the normalized path or complete argument contains a backslash, ASCII control character, wrong suffix, wrong root, or differs from this exact value:

```text
-ExecutePythonScript="C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Scripts/revalidate_assembly_line_native_kit_incident_v003.py"
```

An independent PowerShell regression repeats this exact check without launching Unreal. The one-use runtime remains read-only: it starts one validator process, never starts the importer, writes only new v003 Saved evidence, and fresh-loads the existing eight packages to validate all 24 authored LODs, triangles, UVs, bounds, pivots, material semantics, collision, screen sizes, Nanite, target hashes, settled Source, protected project state, original import evidence, and both failed validation incidents.

## Exact one-use command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_assembly_line_native_kit_incident_retry_v003.ps1" -Acknowledgement REVALIDATE_EXISTING_ASSEMBLY_NATIVE_KIT_V001_INCIDENT_V003_ONCE
```

This command remains unconsumed by the static preparation task. Any PASS or FAIL result permanently consumes v003.
