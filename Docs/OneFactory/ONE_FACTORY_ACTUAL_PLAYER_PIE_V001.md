# OneFactory actual-player PIE validation v001

Status: **THREE UE ATTEMPTS PRESERVED FAIL; CORRECTED V005 ONE-USE RECOVERY
FROZEN, NOT RUN**. This is not an actual-player PASS claim and it does not
authorize an Unreal launch by itself.

## Purpose

The lane opens the already-PASS, immutable OneFactory shell map and uses its
map-local native GameMode.  PIE must possess the real `LBManagementPawn`,
create the native `LBControlRoomHUD` and `LBManagementRootWidget`, and perform
the same reflected HUD action used by the UMG `New Factory` button.  Nothing is
authored back into the map: the Press starter data authority and procedural
presentation live only in the duplicated PIE world and must disappear when PIE
ends.

Frozen map package:

`/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001`

Frozen map SHA-256:

`750FB6C93BBE8220467F5BF9656C4017F0D9E2706B35C413460AF20CEB9EB682`

## Required live proof

Before the player action, the lane requires exactly one native
`LBOneFactoryBootstrap`, exactly one deliberately map-authored
`LBPressShopBuildAuthority`, the exact labels/tags/identity transforms and
authority arrays, and zero starter data, starter presentation, production
machine, process WIP, forbidden legacy actor, Meshy reference or vendor
reference.  The actual player controller must possess and view the native
management pawn and own the native HUD/UMG surface.

The transaction sequence is deliberately player-facing:

1. Call the safe commission route before creation and prove it rejects without
   creating either half of the starter pair.
2. Open Factory Build and invoke `LBControlRoomHUD.activate_management_action(0)`
   to execute `New Factory` through the real HUD/subsystem route.
3. Prove exactly one named Press starter data authority and one named native
   presentation, seven canonical responsibility roles, six routes, eight
   non-empty HISM batches and 268 visible instances.
4. Invoke HUD action 2 to select the next panel programme, then HUD action 0 to
   commission successfully.  Revisions must progress atomically from 0 to 1 to
   2, while all active/reserved WIP arrays remain empty.
5. End PIE, prove the transient pair is gone, prove the empty editor shell is
   still one bootstrap plus one Press authority, and prove the saved map and
   protected anchors are unchanged.

The role instance contract is `18, 37, 31, 34, 89, 19, 40` (total 268).  The
HISM batch contract is `32, 88, 34, 38, 18, 16, 8, 34` (total 268).  The only
presentation geometry/material sources allowed are the Engine basic Cube,
Cylinder and BasicShapeMaterial paths.  The live scan rejects Meshy,
RuntimeGLB, downloaded/vendor, Candidates, legacy Press Runtime/Stations and
developer-validation references.  Presentation items and actors must retain
the NativeOnly/NativeProcedural/VisualOnly/NotProcessWIP provenance contract.

## Screenshots and rendering

The runner uses a real RHI (`-NullRHI` is explicitly rejected), off-screen
rendering at 1920 x 1080, the map's one 5000 K Rect Light authority and its
fixed exposure volume.  It captures exactly these fresh-run files:

- `01_empty_factory_management_overview.png`
- `02_populated_press_starter_wide_overview.png`
- `03_press_train_dispatch_agv_close.png`
- `04_populated_press_starter_with_umg.png`

The first three are high-resolution captures from the actual possessed
management pawn. The fourth is Unreal's native UI-inclusive screenshot and
must visibly include the native UMG. UE 5.8 routes a restricted UI screenshot
through `UGameViewportClient::GetGameViewportWidget()` and sizes it from the
arranged `SViewport` geometry used by `FSlateApplication::TakeScreenshot`.
The narrow native bridge finds that widget's owning `SWindow`, reshapes the
window only by the difference between the current arranged draw size and
1920 x 1080, then the validator waits across frames until
`SViewport::GetCachedGeometry().GetDrawSize()` is stably exact. It rechecks the
real UMG and calls `FScreenshotRequest::RequestScreenshot` with both UI and
game-viewport restriction enabled. No editor chrome or existing image is read,
rescaled, cropped or composited.

Both the in-editor validator and the independent PowerShell reader require
every file to be a stable 1920 x 1080 PNG of at least 32 KiB, then record and
re-check its exact byte count and SHA-256.

## Write and protection boundary

The lane requests no Content save, uses `-NoAutoSave` and `-NoSaveOnExit`, and
never calls an Unreal save API.  It may write only its fresh run receipt, logs
and screenshots below `Saved`.  The runner hashes before/after:

- the OneFactory map and the protected Press v913, restored Press, Body and
  Paint maps;
- the frozen OneFactory shell creation and independent validation receipts;
- all Config files and all existing `Saved/SaveGames` files;
- the exact existing OneFactory bootstrap/GameMode/player-builder/Press-starter
  and management pawn/HUD/widget source seams used by this proof;
- this runner, its live validator and the narrow native Slate-size bridge.

Unrelated new source files are outside that narrow protection set, but no file
should be edited while the one-shot is active.  Binaries and Intermediate build
products are expected to change when the default editor build runs.  The runner
refuses to start if UnrealEditor, UnrealEditor-Cmd, UnrealBuildTool,
AutomationTool, RunUAT or ShaderCompileWorker is active, and checks again after
the process exits.

## Frozen tooling

- `Scripts/validate_one_factory_actual_player_pie_v001.py`
  - SHA-256 `9DFEEE6D6C29B5D96EB6650F38494854BDA780BFDDC09A146150118FF3610099`
- `Scripts/run_one_factory_actual_player_pie_v001.ps1`
  - SHA-256 `B0E7010DFACD27584F1EB096B38D2783F066682FCFDCE09801B371D28CCDFEB7`
- `Source/LineBossCarFactory/LBOneFactoryCaptureBridge.h`
  - SHA-256 `2C5442B15B94504CEA085A3F46F4740BCC4FD0A83CDE70DB37E3C7D0FC04673B`
- `Source/LineBossCarFactory/LBOneFactoryCaptureBridge.cpp`
  - SHA-256 `849C7E1ACD6A02B27126831202E774E8C922E422050904EC3DF5349C6D01CA30`
- `Scripts/recover_one_factory_actual_player_pie_widget_lookup_incident_20260815T023449580Z_v002.ps1`
  - SHA-256 `1432D73BA7AE7E666297B4964504467279D8F0BD2A5674ED9605CD3EC2C92111`
- `Scripts/recover_one_factory_actual_player_pie_ui_resolution_incident_20260815T024250499Z_v003.ps1`
  - SHA-256 `C04D5610F4959D6BD36CA7AC2DCF1C69E7A114DB312B5ACCF12F274F3869CB8C`
- `Scripts/tests/test_one_factory_png_ihdr_parser_ps51_v004.ps1`
  - SHA-256 `6C287FC9BDB9D495337D955F8D1DDA928CBD0B2F35EB3C42CFF73EFB6C63794D`
- `Scripts/recover_one_factory_actual_player_pie_ui_resolution_incident_20260815T024250499Z_v004.ps1`
  - SHA-256 `A1D18D036FF2FB8E862C56F8618513A7FD4654D3AE5EF4C74AD07E6DE1565B76`
- `Scripts/recover_one_factory_actual_player_pie_ui_resolution_incident_20260815T031021499Z_v005.ps1`
  - SHA-256 `01961B7047FF3A80046BA37BDA36480DEDE239181C430F63D47E75AC0E706815`

The mandatory runner-hash argument prevents an edited script from masquerading
as this freeze.  The normal command builds the current Editor target first;
`-SkipEditorBuild` is intentionally not used in the canonical command.

## Preserved first-attempt incident

The exact frozen v001 run was attempted once as stamp
`20260815T023449580Z`.  Editor build and real-RHI PIE startup succeeded; the
map-local GameMode reported the exact ready shell and the actual management HUD
reported ready.  The first widget enumeration then failed closed with:

`module 'unreal' has no attribute 'WidgetBlueprintLibrary'`

UE 5.8 exposes that UMG function library to Python as `WidgetLibrary`, not
`WidgetBlueprintLibrary`.  The corrected validator avoids the rename seam
entirely: it enumerates the exact reflected `LBManagementRootWidget` type with
`unreal.ObjectIterator` and filters by `widget.get_world() == PIE world`, the
same world-safe seam already used successfully for the native builder
subsystem.

The incident remains immutable under
`Saved/Audits/OneFactory/v001/ActualPlayerPIE/Runs/20260815T023449580Z`.
Its live receipt SHA-256 is
`FBE5FA4EF00E365BB6101EF29D7C9510FDC4A6EC77418F5B9906CBDC13C518A5`;
its runner summary SHA-256 is
`51AE20C988345075EA7DAAD67E12C44D55CF3568C6A3988DD8188F9B1B62C169`;
and its Unreal stdout SHA-256 is
`2837BEBA0056057B6339A8956604FA5191DA983B26E9C3D2D6F2AB84E2AF53E4`.
It produced zero screenshots, cleanly ended PIE, retained the empty editor
shell, preserved the exact map SHA-256 and reported zero protected-file
changes.

The historical v002 freeze stated **CORRECTED V002 RETRY FROZEN, NOT RUN**.
It was subsequently invoked exactly once. The widget lookup correction worked:
all gameplay, native UMG, native-only provenance, programme/commission and the
first three exact 1920 x 1080 screenshots passed. That retry then failed closed
only because SHOWUI captured the 1300 x 740 editor Slate window rather than the
requested render resolution.

## Preserved second-attempt UI-resolution incident

The exact second run remains immutable under
`Saved/Audits/OneFactory/v001/ActualPlayerPIE/Runs/20260815T024250499Z`.
Its live receipt SHA-256 is
`FE9C50B9408ED279C50D762A1DF71BB78B9630B8EF11D911A80E0DF6B2001F19`;
its runner summary SHA-256 is
`4F1383241C962B664A8C7EFC8CD6A367FC785D1DB90DC20566D6AC7630FC0D5E`;
and its Unreal stdout SHA-256 is
`5A6A3C9B76D63E51DD4967039EB62A7AC77C0C352C6D0D7F6F0A234B7D6BC1B4`.

The four physical screenshot hashes are:

- empty overview: `C9EB1B2AB86375C7CDF1EECF0A876872834D0C1B374B57ACB4798D8AFB8FE600`
  at 1920 x 1080;
- populated overview: `CDEF996D2A7A5933B3F0C8EB2FCA58A66624CE2E244F534CA764D7B92C104A3B`
  at 1920 x 1080;
- Press/AGV close view: `ED7D476C42FAE9AF1F757CA0238D691B5A33F0F49E6EF3A3801C499030C9BCFF`
  at 1920 x 1080;
- visible native UMG: `6120A5ECCDB3FA24D00251E92961FE623CBFE4B0E3B4C88AF362BAF8CCC8E11B`
  at the rejected 1300 x 740 Slate geometry.

The exact live failure is
`OneFactory screenshot is not 1920x1080: 04_populated_press_starter_with_umg.png=[1300, 740]`.
PIE ended cleanly, the saved map retained SHA-256
`750FB6C93BBE8220467F5BF9656C4017F0D9E2706B35C413460AF20CEB9EB682`,
and the receipts report zero protected changes.

The v003 wrapper was invoked but refused during read-only preflight before it
created a recovery root or launched Unreal/UBT. Its PNG parser allowed Windows
PowerShell 5.1 to bind unparenthesized array-index/shift expressions
incorrectly: the real IHDR bytes `00 00 07 80` and `00 00 04 38` were reported
as 128 and 56 rather than 1920 and 1080. Inspection confirmed that
`Incident_20260815T024250499Z_v003` does not exist; the rejected wrapper remains
preserved at its exact hash above.

The v004 wrapper explicitly casts and parenthesizes every IHDR byte before each
shift. A standalone Windows PowerShell 5.1 regression proves both 1920 x 1080
and 1300 x 740 headers. V004 passed that preflight and launched one retry. Its
bridge successfully made both `FSceneViewport` and the actual player viewport
report 1920 x 1080, but the native UI PNG remained 1300 x 740. Engine source
confirms the cause: `FSlateApplication::TakeScreenshotCommon` sizes the capture
from `ArrangedWidget.Geometry.GetDrawSize()`, so changing only the scene
backbuffer cannot change the UI screenshot dimensions.

## Preserved third-attempt arranged-geometry incident

The exact v004 retry remains immutable under
`Saved/Audits/OneFactory/v001/ActualPlayerPIE/Runs/20260815T031021499Z`.
Its live receipt SHA-256 is
`E981B74B9D740EAEBA52CF6EC234FB48F9755DCD5D50B8D2E9604ECC6252505D`;
its runner summary SHA-256 is
`1F091680D688933ECEAD17AC7FC8E1F6B0BCCC3BE676085E1B402AA1E2B87CC9`;
and its Unreal stdout SHA-256 is
`22C4BCA1F56577975E4452506A0C1E95324302AA3D0595B5C700F6BC5C7DA606`.
The first three images are genuine 1920 x 1080 captures. The visible-UMG image
is preserved exactly at SHA-256
`7DBD3120806F76763A78B92E6AA93F215C3E3F3137011F7909EF0ED017AE5DE8`
and the rejected 1300 x 740 arranged Slate size. The receipt proves native UMG
visible, both old viewport checks at 1920 x 1080, the unchanged map hash, and
zero protected changes.

The failed v004 recovery root is also immutable. Its pre-retry evidence has
SHA-256 `A12AEE0D655F689126803F272EAC543C933BD470CCE045AB13E0BF93CA9481F5`
and its failure summary has SHA-256
`F689F33B4C411EB06553AAC6D14765042626C7F8426CC9DDD75B7A5BC925AD82`.

V005 pins all three failed runs, every second- and third-run screenshot, the
rejected v003 wrapper, the complete failed v004 recovery root, corrected tools,
protected maps and save anchors. It refuses any drift or existing v005 root,
invokes the corrected normal runner exactly once, and accepts only a genuine
restricted native 1920 x 1080 `SViewport` screenshot with visible UMG and
explicit `post_processing: false` evidence. It never alters prior evidence.

## Exact future one-use recovery command

Run this only after explicit launch authorization and after confirming no
Unreal/build process is active:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\recover_one_factory_actual_player_pie_ui_resolution_incident_20260815T031021499Z_v005.ps1" -ExpectedRecoverySha256 01961B7047FF3A80046BA37BDA36480DEDE239181C430F63D47E75AC0E706815
```

Do not invoke the normal runner separately for this incident.  The recovery
wrapper owns the single allowed corrected retry and passes the frozen runner
self-hash itself.

On a truthful PASS, evidence will be under the same UTC stamp in:

- `Saved/Audits/OneFactory/v001/ActualPlayerPIE/Runs/<stamp>/`
- `Saved/ValidationScreenshots/OneFactory/v001/ActualPlayerPIE/<stamp>/`

The run summary independently embeds the runner/validator hashes, process
arguments and exit codes, all four screenshot paths/hashes/bytes/dimensions,
the required-check inventory, 7/8/268 evidence, protected snapshots and exact
map hash.  A failed run remains preserved under its fresh stamp; it is never
silently overwritten or promoted.
