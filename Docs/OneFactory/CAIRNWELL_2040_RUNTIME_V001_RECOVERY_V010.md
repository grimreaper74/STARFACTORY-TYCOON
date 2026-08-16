# Cairnwell 2040 Runtime v001 — validation-only recovery v010

Status: `OFFLINE_PREPARED__WAITING_FOR_EXACT_V010_CONTRACT_FREEZE_AND_ROOT_LAUNCH_AUTHORIZATION`

V010 does not import, reimport, save, move, copy, delete, rename, or quarantine any Content package. The v009 importer completed successfully in UnrealEditor process 36612 and produced the exact 11-package authority. The v009 wrapper then failed before launching its validator because Windows PowerShell rejected the one intentional empty JSON property at `assets.materials.body.graph.detail_clamp.inputs[""]`.

The preserved v009 evidence is immutable:

- run: `Recovery_v009/20260815T141819Z-435fcd56`, exact six-file closure;
- import receipt: SHA-256 `F11952FD07E9B573E0882059C49DF474E166CAE9B25F2F677023260ACAA413A6`;
- wrapper failure summary: SHA-256 `10025897FA49CDFFB94B37C78B082E0D43391E2062BC15BC426BF52C0E6E9265`;
- quarantine receipt: SHA-256 `AB17DB911591102E0EB01D0F3DEC56DE03DB51FCE05157739A642E4E796FD587`;
- current destination: exact 11 files, with every package hash equal to the import receipt;
- v009 validator process/evidence: absent.

PowerShell 7.5/7.6 can parse the full receipt only with `ConvertFrom-Json -AsHashtable`; Windows PowerShell 5.1 does not provide that switch. V010 therefore keeps the runner compatible with PowerShell 5.1 and never asks PowerShell to parse a v009 or v010 receipt containing the empty Clamp key. The bundled Python verifier parses the original bytes, requires exactly one empty-key path, rejects any additional empty key, and performs all package-map comparisons. PowerShell consumes only the v010 contract, fixed PASS markers, and file hashes.

The v009 logs also prove that Unreal startup launched `Build.bat -Mode=ValidatePlatforms`, contradicting the v009 summary's `no_build_tool_invoked=true` field. This was a successful SDK-status query, not a project build or asset failure, but v010 records the contradiction rather than repeating it. Installed UE 5.8 source `TargetPlatformManagerModule.cpp`, SHA-256 `E86827925AECB8ED2250F5D7AB655269ED7FE6A83D6691B244FA36FAAD5A4E17`, defines `UE_SKIP_UBT_SDK_SETUP` and returns before the startup UBT launch when its integer value is `1`. The runner sets and later restores that process environment variable. Any `UnrealBuildTool`, `Build.bat`, `-Mode=ValidatePlatforms`, `AutoSDKInfo.txt`, or UBT return-code token in validator logs fails the lane.

## One-shot topology

The guarded runner creates one fresh `Recovery_v010/<UTC>-<GUID8>` audit root and launches exactly one full `UnrealEditor.exe` process against `/Engine/Maps/Entry`. It runs only `validate_cairnwell_2040_runtime_recovery_v010.py`, with `-NoCompile`, `-NoCompileEditor`, `-NullRHI`, `-NoAutoSave`, and `-NoSaveOnExit`. The validator naturally exits through `-ExecutePythonScript`; it never calls `quit_editor`.

The validator:

1. revalidates the frozen source, protected project, v1–v9 chronology, q1–q6 closures, v009 six-file run, and v010 lane;
2. hashes the exact 11 v009 packages before loading anything;
3. fresh-loads and validates all four meshes and 12 authored LODs, three textures, four materials, exact graph/bindings, dependency closure, collision, navigation, Nanite, UV, bounds, pivot, and material slots;
4. rehashes the 11 packages and all namespace files after validation;
5. writes only a v010 receipt or failure receipt under the new Saved audit root.

The runner then applies strict exit/log gates, invokes the Python post-exit verifier, and writes one v010 summary. It never invokes the v009 importer and contains no `Move-Item`, `Copy-Item`, or `Remove-Item` operation.

## Offline freeze sequence

Before any contract write:

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe' `
  'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\prepare_cairnwell_2040_runtime_v001_recovery_v010.py' --dry-build
```

After independent review of the exact source hashes, freeze the pair once with acknowledgement `FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_ONCE`, then rerun the frozen pre-validation verifier. Contract freeze authorizes no Unreal or UBT launch.

The eventual guarded execution command is intentionally withheld until the frozen pair and independent audit return GO. It will use acknowledgement `VALIDATE_CAIRNWELL_2040_RUNTIME_V001_V009_IMPORT_V010_ONCE` and must be executed at most once.
