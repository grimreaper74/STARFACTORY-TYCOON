# Audio intake, 2026-09-02

The module had no audio at all (the reviewable-build plan calls it the
largest perceived-quality gain available, and the one thing code cannot
supply). This morning the owner sourced two free, commercially usable
libraries; this is their record. `Content/` and `SourceAssets/` are not
in git, so the manifests under `Saved/Audits/` and this note are the
evidence.

## 1. UI SFX Free Pack (Fab)

- Listing `a6ca37d8-2df5-42ac-905f-377e387b74ef`, Fab Standard License
  (free listing). Added by the owner through the Epic launcher; copied
  from the launcher vault cache (`UISFXFrebd0b22ed9626V1`) into
  `Content/UI_SFX_Free_Pack/` at the pack's own package path so its
  SoundWave and SoundCue references resolve.
- 38 WAV (button_press, cancel, ok, coins, highpitched, repair, slide,
  slide_loop, warning families) and 76 `.uasset`.
- Manifest with sha256 per file:
  `Saved/Audits/UISFX_Intake_2026_09_02/manifest_sha256.txt`.
- Status: **source candidate** until a cue is wired and heard in a
  packaged run.

## 2. Sonniss GDC 2026 Game Audio Bundle

- https://gdc.sonniss.com/ - five zips downloaded by the owner
  (about 6.5 GB), sha256 of each zip recorded in
  `SourceAssets/Audio/Sonniss_GDC2026/MANIFEST_zips_sha256.txt`;
  extracted beside it, one folder per vendor. Licence: royalty-free,
  commercial, no attribution, unlimited projects (the licence text
  ships in the bundle).
- Status: **source**. Nothing from it is in `Content/` yet. Anything
  promoted gets a manifest row with sha256, per
  `Docs/ReleaseGate/ASSET_PROVENANCE_AND_PROMOTION.md`.

## The eight sounds the game needs first

Crane travel loop, crane lift and set-down, drone work loop, order
arrives (lorry), contract accepted, ship departs, refusal, ambient hall.
The UI pack covers accepted/refusal/clicks; the crane, drone, lorry,
departure and ambience come from the Sonniss folders once catalogued.

## Picks from the catalogue (347 files, 127 vendors), not yet promoted

| Need | File (vendor) |
|---|---|
| Crane travel loop | `MACHInd_Crane Onboard Ride Squeaks Motors_CW.wav` (Victor Ermakov, Ship Repair Factory) |
| Crane lift / set-down | `MECHLtch_Click Deep Mechanism Latch Button Nearfield Thunk 02_ESM_HDLM.wav` (Epic Stock Media, HD Lock and Mechanism) |
| Drone work loop | `ROBTMvmt_Tower Deploy Hitech Robot Motor Dark Thump Servo Whine 04_ESM_TDG.wav` (Epic Stock Media) or the Sonik Sound Library toy quadcopter file |
| Order arrives (lorry) | `VEHFrght_Freight Truck Pass By 22_SNDBTS_PB-TTC2.wav` (SoundBits) |
| Contract accepted | `Interface Accept Glassy Snap.wav` (Cinematic Sound Design) or the UI pack `ok_*` |
| Ship departs | `AEROJet_Blast Off Clean_344 Audio_Air Designed.wav` (344 Audio) |
| Refusal | `Interface Deny Low Fat Dark.wav` (Cinematic Sound Design) or the UI pack `cancel_*` |
| Ambient hall | `AMBInd_Factory Hall Busy Alarm Machines Voices_CW.wav` (carries voices and an alarm - may be too busy) or `Dark Industrial Ambience.wav` (Cinematic Sound Design, Sci-Fi Drones) |

Promotion means: copy the WAV into `SourceAssets/Audio/Promoted/`, import as a
SoundWave under `Content/LineBoss/Audio/`, one manifest row with sha256 each,
and a MetaSound or cue that the code actually plays. Until a cue is heard in a
packaged run the status stays **source candidate**.

