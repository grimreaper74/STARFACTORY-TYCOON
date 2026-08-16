# Body Shop Experimental v001 release-validation tooling

The runtime/package lane does not mutate Source, Content, Config, the default map,
Press v913, the full restored Press map, campaign saves, or the legacy `LBBodyWeldLineActor`. Before running it,
the separately guarded visual-readability v003 patch is allowed to change exactly
the isolated Body Shop map and its existing cream material instance. Its fresh
validator binds both resulting hashes; no manually supplied replacement hash is
trusted.

Run the editor/runtime gate with exact fresh PASS receipt paths:

```powershell
& '.\Scripts\run_body_shop_release_validation_v001.ps1' `
  -MaterialReceipt 'Saved\Audits\BodyShop\Experimental_v001\presentation_materials_v002_native_robot_support_kit_validation_v004.json' `
  -NativeRobotValidationReceipt 'Saved\Audits\BodyShop\RobotNative_v001\UnrealImportLane\20260814T204134Z-19e41ca7\fresh_load_validation_receipt_v001.json' `
  -SupportKitValidationReceipt 'Saved\Audits\BodyShop\SupportKitNative_v002\UnrealImportLane_v003\20260814T223952Z-fa3434b0\fresh_load_validation_receipt_v003.json'
```

It refuses active Unreal/build processes, requires independently passing base
environment/material receipts plus
`visual_readability_v003_validation.json`, and requires the current map and cream
package hashes to equal that fresh receipt. It then hashes protected files,
optionally builds `LineBossCarFactoryEditor Win64 Development`, runs the complete
`LineBoss.BodyShop.Experimental` prefix, and executes actual-player PIE with saved
environment defaults. The PIE gate requires six commissioned cells, three complete
robots, eight vacuum contacts, two live spot-gun meshes on the authored weld slots,
exactly one active non-WIP `LB_BodyShop_ServiceDressing_v002` actor with native
HISM counts `6 / 3 / 3`, the exact native v002 full-stillage runtime getter,
non-mutating 100 cm/90-degree placement acceptance and invalid-placement rejection,
sampled articulated joints, quality pass/fail, starvation, blocked output, and one
logical visible skid/underbody assembly across save/reload. It captures the possessed
`LBBodyShopManagementPawn` view with `LBBodyShopPrototypeHUD`; it never creates a
transient camera or changes lights, grid visibility, or exposure during validation.

The reflected, non-mutating placement seam
`ValidateModulePlacementForValidation(DefinitionId, Transform, OutReason)` delegates
to the live build authority. The automation tests use it for the accepted placement,
rotation and invalid-overlap cases without duplicating placement rules in Python.

Development packaging is explicitly scoped to `/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001` and uses fresh `Builds/BodyShopExperimental_v001/Development_<UTC>` and staging paths:

```powershell
& '.\Scripts\package_body_shop_experimental_development_v001.ps1' `
  -ReleaseValidationSummary 'Saved\Audits\BodyShop\Experimental_v001\ReleaseValidation\<UTC>\release_validation_summary_v001.json'
```

The package runner records the exact current BuildCookRun invocation and log, then
generates direct UnrealPak IoStore CSV listings from both the fresh stage and its
fresh archive. A hashed invocation receipt ties every CSV one-to-one to the exact
`.utoc`/`.ucas` pair and rejects missing, repeated or extra evidence. It never
searches historical logs for asset-name mentions. The
manifest requires the map, articulated robot pieces, eight-cup tool, underbody
fixture, vision gate, PanelStillage mesh/material, skid, underbody, C-gun
mesh/material/textures and the exact two-master/twelve-instance `Materials_v002`
family in both listings. It also requires all 12 exact native support-kit v002
packages in both listings, with the v002 full stillage as the active Body
stillage. Stage and archive container hashes must match, and any
`__LegacyLODStaging` package or loose path fails the gate.

The current manifest also takes the final native-robot and native-support
validation receipts as explicit arguments. It binds their exact SHA values and
sibling authorities, the eight robot and 12 support package hashes, three LODs
per asset and aggregate triangle totals `2628 / 1964 / 1356` for robots and
`20408 / 7580 / 1780` for support. Packaged renderer validation keeps the core
target at exactly 25 components across 10 meshes; native service props affect
whole-scene totals without changing that core manifest.

Before BuildCookRun, packaging rechecks every protected hash recorded by the supplied
release summary and follows its visual-readability v003 receipt back to the exact
current map and cream-material hashes. A stale PASS receipt cannot authorize a newer
map, material, Press/config or campaign-save state. Both Press v913 and
`LB_PressShop_FullFactoryRestored_v001.umap` are protected, with the restored map
pinned to `D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5`.

After the manifest passes, the Development executable runs twice with a unique safe
token, a fresh `-UserDir` under that audit run and a token-derived
`-saveddirsuffix`. This prevents the validation process from overwriting an existing
editor or installed-game save even if a user already has the experimental slot. Run
1 starts the pilot, pauses at
one logical/visible `WELDING_UNDERBODY` WIP, writes only
`LineBoss_BodyShopExperimental_v001`, emits the exact tokened SAVE PASS marker and
exits zero. Run 2 restarts the executable, loads that save, proves the same exact WIP,
emits the tokened LOAD PASS marker and exits zero. The runner reads only those two
fresh engine logs, requires exactly one final marker per phase, rejects cross-phase
markers/fatals, verifies that load did not alter the save hash, and compares protected
Body Shop, Press v913, the full restored Press map, campaign, config and upstream release-receipt hashes. Shipping
is neither requested nor accepted by this lane.
