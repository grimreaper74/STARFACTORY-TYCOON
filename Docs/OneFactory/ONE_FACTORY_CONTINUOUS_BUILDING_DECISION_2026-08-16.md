# One continuous building — decision record, 2026-08-16

## The direction

The product owner set the direction in this session's own words: *"i wanted one
continues building like production line and car manufacturer starting at the
coils to the finnished car, so want it fully detailed so want that in"*, and
*"also everything, the crains"*. Asked whether to expand the press map or keep
separate buildings per shop, the owner left the call to the session.

**The call: one continuous building.** The Moorcross OneFactory map carries the
whole route — coil intake, press, panel stillages, body weld, paint, assembly,
dispatch — inside a single envelope, at the detail standard the owner approved
in the restored press shop screenshot.

## Why not expand the press map

`LB_PressShop_FullFactoryRestored_v001` is a protected authored input: it has
no gameplay stack (no runtime coordinator, no route, no HUD contract), its
coordinates collide with the Moorcross route, and every prior recovery
document treats it as read-only reference. Expanding it would fork the
gameplay implementation. Moorcross already runs the complete 57-station
journey in editor and package, so detail moves *to* the game, not the game to
the detail.

## How the detail comes in

The read-and-materialise pattern from the press recovery doc, applied to the
whole shop:

1. **Trains.** All four trains stand at the reference 2,251 cm spacing on the
   committed `OF_PRESS_TRAIN_001` datum, each rendered by the pinned v449
   single-mesh visual (commit `230e170`).
2. **Everything else.** A one-time, read-only editor pass extracted every
   non-train static-mesh actor of the restored map — the overhead crane
   (bridge girders, runway beams, columns, end trucks, trolley, 30T hoist,
   C-hook), 249 guard rails, lamps, pipework, trench grates, carrier rollers,
   HMI cabinets and the logistics corner — into a datum-relative manifest at
   `Content/LineBoss/Reference/RestoredShop/shop_manifest.json` (1,522
   actors; engine-primitive walls/floors dropped because Moorcross has its
   own). `ALBOneFactoryDevRestoredShopActor` materialises it around the press
   datum with the same +90° yaw mapping the trains use (commit `060a888`).

## Evidence

- Full-shop tour: **1,522 instances across 720 meshes, 0 unresolved mesh
  paths**; crane runway parallel to all four trains; body/paint/assembly
  bays unaffected. Captures: `Captures/20260816_15_FullShop_*.png`.
- `LineBoss` automation suite after the wiring: **275/275**.

## Open items carried forward

- The manifest records mesh + transform only — per-slot material overrides
  authored in the reference map are not yet carried, so instances render
  their meshes' default materials.
- Trains B–D are visual-only; making them playable is a versioned
  press-layout contract change.
- v449 remains the pinned train visual; promotion to an owned
  `DetailedPresentation_v001` root is recorded in the press release note.
