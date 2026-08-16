# Cairnwell 2040 Runtime v001 — Validation Recovery v011

Status: offline incident contract only. Contract freeze authorizes no Unreal, UBT,
Content, map, Config, save, import, reimport, move, copy, or delete operation.

## Why v011 exists

The v009 Unreal import itself completed successfully and wrote the exact eleven
runtime packages. Its PowerShell wrapper then failed while parsing the one
intentional empty JSON property at
`assets.materials.body.graph.detail_clamp.inputs[""]`; the v009 validator never
ran. V010 correctly changed the recovery to one read-only validator, but its
offline contract was cut just before a late independent audit identified
underconstrained final receipt and summary identity checks. V010 was never run.

V010 is therefore preserved byte-for-byte as stale, unexecuted chronology
evidence:

- contract: 155045 bytes, SHA-256
  `CBE1DA417B4009F188E9D35D13402AEA1C7D0CAB9A3EED041ED57F20DA4ADF45`;
- sidecar: 122 bytes, SHA-256
  `0FAA9591022AB275E88BE0DFBDD201BC39FA2BDB69200AA4C345DFBED5ED1C5A`;
- `Recovery_v010` must remain absent.

V011 supersedes V010 additively. It does not edit any V010-bound file.

The current car is approved for the game build, not visually locked for final
release. Runtime asset identity and production state remain decoupled from the
underlying visual geometry. This integration is explicitly provisional and revisionable;
any later geometry replacement must arrive as a new, separately
approved authority revision without silently changing this frozen evidence.

## Authorized runtime shape

The eventual guarded V011 run is validation-only:

- exactly one full `UnrealEditor.exe` read-only validator process;
- no importer and no import/reimport/save API;
- no quarantine move and no Content write;
- current eleven v009 packages must hash identically before and after loads;
- the v009 six-file run, q6 quarantine, approved source, protected project,
  frozen lane, V010 pair, and absent `Recovery_v010` are reverified throughout;
- the result root is a fresh
  `Saved/.../UnrealImportLane_v001/Recovery_v011/<UTC>-<GUID8>` directory.

The validator may write only its PASS or failure receipt in the fresh result
root. The wrapper may additionally write three logs and the final lane summary.
The successful final root is exactly five regular non-link files:

1. `fresh_process_validation_receipt_recovery_v011.json`;
2. `fresh_process_validation_recovery_v011.log`;
3. `fresh_process_validation_recovery_v011.stdout.log`;
4. `fresh_process_validation_recovery_v011.stderr.log`;
5. `lane_summary_recovery_v011.json`.

## Exact receipt and summary binding

Python uses duplicate-rejecting JSON parsing and requires the sole empty key to
remain the Clamp input path above. The fresh receipt is compared as a complete
object, including exact top-level key set, original contract and baseline
hashes, V009 and V010 contract hashes, q9 receipt hash plus embedded path/bytes/
hash/status row, V009 wrapper classification and binding, incident-chain hash,
UE 5.8 engine-version prefix, 4 meshes / 12 authored LODs / 3 textures /
4 materials / 11 packages, persisted dependency closure, exact assets,
namespace, registry, source, protected, lane, package hashes, zero mutation,
zero import/reimport, and empty failure/map lists.

The final summary is also compared as a complete object. Its exact binding
includes acknowledgement, run root, destination, original contract and baseline
hashes, V009 run ID and evidence hashes, stale V010 hash, V011 contract hash,
preflight PASS plus contract hash, validation receipt path/hash/status,
post-validation PASS plus receipt hash, process/log hashes, retry evidence,
package map, strict-exit policy, environment restoration, zero UBT matches, and
a timezone-aware ISO timestamp. Synthetic preflight regressions prove that a
missing acknowledgement, wrong receipt path, drifted wrapper incident binding,
duplicate normal key, or duplicate empty key fails closed.

## UBT and lifecycle gates

The runner is Windows PowerShell 5.1 compatible and never parses the full v009
or V011 receipts. Python owns those exact JSON checks. Before the validator,
the runner sets process environment `UE_SKIP_UBT_SDK_SETUP=1`; installed UE 5.8
source is pinned for that guard. Logs reject `Launching UnrealBuildTool`,
`UnrealBuildTool`, `Build.bat`, `-Mode=ValidatePlatforms`, `AutoSDKInfo.txt`, and
`UBT AutoSDK ReturnCode`. A scoped CIM check catches dotnet-hosted UBT command
lines. All three process environment variables are restored independently and
verified before PASS. Any early, restoration, post-summary, final-verifier, or
final-process failure rewrites the summary `FAIL_CLOSED` and exits nonzero; the
PASS marker is emitted only after the final five-file verifier.

The validator relies on the natural deferred exit of `-ExecutePythonScript` and
does not call `quit_editor`.

## Freeze and execution separation

The no-write dry build reconstructs and validates the full payload, strict JSON
round trip, stale V010 chain, current packages, prior evidence, all exact lane
files, and the synthetic tamper regressions before the V011 pair may be written.
An independent reviewer must return GO against frozen source hashes before the
one-time offline pair cut. Contract cut still authorizes no Unreal or UBT launch.
The guarded one-use execution command is withheld until post-cut revalidation.
