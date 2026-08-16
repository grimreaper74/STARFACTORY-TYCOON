# Cairnwell2040Runtime_v001 incident recovery v007

## Status

`OFFLINE_STATIC_FREEZE_ONLY__UNREAL_NOT_AUTHORIZED`

Recovery v006 was executed exactly once and failed closed. It must never be rerun. Its immutable
run is:

`Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/UnrealImportLane_v001/Recovery_v006/20260815T124823Z-67c989ee`

The v006 failure, summary, and quarantine-receipt SHA-256 values are respectively:

- `A484FAAB8F612A0EE9FA915436B3389016D7137CB954580C499BDBBFE2A15F06`
- `A301E0F229D172C66351017D5281778A3916232D12F4455C328F45F6C5FE1502`
- `ADA88E957267A48B548E1524B3EED9890AB99DD1839D5A35952F05B55078511A`

All v001-v006 failed evidence, all five existing quarantines, the current exact eleven-package
namespace, approved v005 source, and protected project state remain preserved. Recovery v007 is a
new incident-bound one-use lane. Merely freezing it does not authorize Unreal, UBT, Content moves,
runtime binding, maps, Config, saves, or panel-module writes.

## Exact v006 diagnosis

The current body material is not broken. Its Clamp mode is exactly `CMODE_CLAMP`; its stored minimum
and maximum defaults are within the pre-existing tolerance; and the normalized-luminance connection
was authored through the correct empty destination selector.

UE 5.8 uses two deliberately different representations for that first Clamp input:

- The importer must pass the empty string `""`. `GetExpressionInputByName` converts that selector to
  `FName NAME_None`, which selects the first semantic `Input` pin.
- `GetMaterialExpressionInputNames` shortens semantic `Input` to `NAME_None`, calls
  `Name.ToString()`, and exposes the literal Python string `"None"`.

The v006 validator incorrectly compared the reflected literal `"None"` with logical `""`. Recovery
v007 first requires an exact Python `str` and exact class-specific reflected order. Only after that
raw proof does it canonicalize literal `"None"` to logical `""` before zipping names to source
nodes. Raw empty strings are rejected, duplicate canonical names are rejected, and raw `"None"`
cannot leak into graph evidence. The importer connection remains `""`; it must never be changed to
`"None"` or `"Input"`.

Every `expression_links` path is closed exactly:

- `MaterialExpressionLinearInterpolate`: `A`, `B`, `Alpha`, once.
- `MaterialExpressionMultiply`: `A`, `B`, twice.
- `MaterialExpressionClamp`: raw `None`, `Min`, `Max`; canonical `""`, `Min`, `Max`, once.
- `MaterialExpressionDotProduct`: `A`, `B`, once.

No material, graph, value, tolerance, texture, enum, geometry, UV, bounds, collision, navigation,
Nanite, dependency, paint-mask, or package gate is relaxed.

## Primary UE 5.8 evidence

The frozen contract pins the installed bytes and exact line authorities for:

- `MaterialEditingLibrary.cpp`: input lookup at 46-75 and reflected names at 1203-1225.
- `MaterialGraphNode.cpp`: semantic `Input` to `NAME_None` shortening at 597-613.
- `PyConversion.cpp`: `FString` to Python `str` and array-wrapper conversion.
- `UnrealNames.cpp`: the exact `NAME_None` spelling `None`.
- `MaterialExpression.h`: index-zero-first `FExpressionInputIterator` traversal.
- Clamp, Lerp, Multiply, and DotProduct headers: exact declared input order.
- `MaterialExpressions.cpp`: Clamp input-name derivation.

The preserved v006 failure receipt and exact current body-material package hash provide runtime/uasset
evidence. Source interpretation is not inferred from a string-only test.

## Recovery topology

The v007 runner may move the whole current destination directory exactly once to:

`Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/Incident_20260815T124823Z-67c989ee_v006`

This is MOVE-only and recoverable. Delete, overwrite, reimport, implicit cleanup, and any second
attempt are forbidden. The new audit root is reserved as:

`Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/UnrealImportLane_v001/Recovery_v007`

If separately authorized, the runner still requires two distinct natural-exit UnrealEditor
processes, `/Engine/Maps/Entry`, no compile, strict exit zero, no fatal/ensure/shutdown signatures,
an exact fresh import, an independent read-only reload, exact eleven-package hashes, and final
post-exit all-file namespace closure. Unexpected `.uexp`, `.ubulk`, sidecars, or any other file fail
the closure.

## Offline commands

Freeze or verify the v007 contract without Unreal:

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe' `
  'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\prepare_cairnwell_2040_runtime_v001_recovery_v007.py' `
  --acknowledgement FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V007_ONCE
```

The guarded one-use command below is documentation only until root explicitly coordinates it and all
Unreal/build processes are zero:

```powershell
& 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_cairnwell_2040_runtime_import_lane_v001.ps1' `
  -Acknowledgement RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V007_ONCE
```
