# Reboot checkpoint — 2026-08-03

This checkpoint was written immediately before the user-requested ASUS BIOS
update. Work remains in the canonical non-OneDrive repository only.

## Unreal state saved before reboot

- Accepted overall PR-004 integration baseline remains
  `/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006`.
- Accepted reusable-composition development baseline remains
  `/Game/LineBoss/Maps/LB_PressShop_PR004ReusableRobotCandidate_v016`.
- Rejected candidates remain rejected and were not promoted or used as an
  authoritative replacement baseline.
- Isolated v020 was generated at
  `/Game/LineBoss/Maps/LB_PressShop_PR004SurfaceForgeRobotCandidate_v020` and
  `/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v020`.
- v020 currently contains 27 duplicated static meshes processed through UE
  5.8 Geometry Script repair/compact operations, generated candidate simple
  convex collision on every duplicated mesh, four reusable tool Blueprints,
  35 CastIron-only Surface Forge material overrides, and a deterministic
  Cairnwell equipment-plate candidate.
- No v020 screenshot has been accepted and v020 is **not promoted**.
- Technical audit caught that the first v020 core Blueprint used `float` with
  `BlueprintEditorLibrary.get_basic_type_by_name`, which UE 5.8 silently
  converted to integer pins. Evidence:
  `Saved/Audits/blueprint_numeric_pin_types_v001.json`.
- The reproducible builder is patched to use UE pin type `real` (double).
  `Scripts/rebuild_press_shop_pr004_surfaceforge_robot_real_state_v020.py` is
  ready but was deliberately **not run before reboot**. It deletes/rebuilds
  only the generated v020 core Blueprint and v020 map, preserving the 27
  meshes, four tool Blueprints, materials, branding, v016 and all user files.

## PC stability finding and prepared firmware

- The active app crash was a real `codex.exe` access violation (`0xc0000005`).
  Multiple unrelated processes also faulted and Windows recorded repeated
  `PAGE_FAULT_IN_NONPAGED_AREA` (`0x50`) bugchecks.
- Hardware identified: Intel Core i9-14900K, ASUS ROG STRIX Z790-F GAMING WIFI,
  BIOS 2402 and live CPU microcode `0x125`.
- Intel currently recommends Intel Default Settings and BIOS microcode `0x12F`
  or later for 13th/14th Gen desktop Vmin Shift instability. ASUS BIOS 3201 is
  the current board firmware and supersedes the installed 2402.
- Official ASUS BIOS 3201 ZIP SHA-256 was verified as
  `5BC51ED81588A6DF5D9B06D4CE2D1725CF20ABDD12962D31335578F6699DAACC`.
- The extracted CAP was copied to the existing 3XS FAT32 USB drive as
  `D:\SZ790F.CAP`; its SHA-256 was verified after copying as
  `FA222BB2615AB7D7A45F3A53FD9BFAFD618EE9B6149A80F9EE18892C4BF14538`.
  Existing `Windows Key.txt` and `3XS Test Pictures` contents were preserved.
- The user explicitly requested pausing Unreal work and performing the update.

## Resume sequence

1. Complete ASUS EZ Flash 3 update to BIOS 3201 from `D:\SZ790F.CAP` without
   interrupting power.
2. Load BIOS defaults / Intel Default Settings after the update and save.
3. Run the motherboard's built-in MemTest86 from the BIOS Tool menu; record the
   result. This does not require another USB.
4. In Windows, verify BIOS 3201 and CPU microcode `0x12F` or newer before heavy
   Unreal work.
5. Run `Scripts/rebuild_press_shop_pr004_surfaceforge_robot_real_state_v020.py`.
6. Run independent v020 bindings, collision, transform, Blueprint compile,
   runtime and save/load gates.
7. Capture fresh v020 fixed-camera screenshots and inspect them against v016,
   v006 and the Pro references. Do not promote merely because technical gates
   pass.

## Post-update verification — 2026-08-03 08:35 Europe/London

- Steps 1, 2 and 4 above are complete.
- Windows read-back verified ASUS BIOS `3201` and Intel microcode `0x12F`
  (`2F 01 00 00`) after the fresh `08:33:35` boot.
- DDR5 is at the BIOS-default `4800 MHz` configuration.
- Immediate post-boot event review found zero WHEA-Logger events and zero
  Windows bugchecks.
- Step 3, the motherboard built-in MemTest86 run, remains the active hardware
  gate. Steps 5–7 remain deliberately pending; v020 is still not promoted.
