# Press Shop full-factory restoration lane v001

`LB_PressShop_BuilderAuthorityCandidate_v438` is the selected recovery source. It is the best preserved coherent whole shop: four complete tagged train scopes (338 actors each), four detailed aggregate train visuals, a 558-actor inbound/front-end scope, one native build authority with four bays and four utility spines, embedded crane/AGV controllers, and previously passing whole-shop navigation evidence.

The clean player-buildable v913 map remains the default and is not replaced. The restored map is a separate recovery/reference level:

- Source: `/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438`
- Destination: `/Game/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001`
- Build: `Scripts/restore_press_shop_full_factory_v001.py`
- Independent validation: `Scripts/validate_press_shop_full_factory_restored_v001.py`

The build is deliberately one-shot and non-overwriting. It uses Unreal's asset API, refuses an existing destination or receipt, pins v438/v913/v249/v288 hashes, inventories the source, duplicates it, explicitly saves the duplicated `UWorld`, releases the Python `UWorld` reference, and proves every protected package is unchanged. A separate fresh Unreal process runs the independent validator, reloads the destination, and compares its exact canonical actor signature with v438. Keeping those phases separate avoids retaining a Python `UWorld` across `load_map()` garbage collection.

The authored factory does not depend on runtime spawning for its visible plant restoration: the trains, inbound equipment, authorities and controller actors are saved map content. PIE can still create transient workpieces/effects and must be tested separately before promotion.

No script changes the default map, Config, Source, existing maps, campaign saves, or promotion state.
