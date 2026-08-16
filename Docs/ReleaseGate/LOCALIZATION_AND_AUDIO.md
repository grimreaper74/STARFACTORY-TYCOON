# Localization and audio

## Current truth

- Line Boss has **no voice acting**. Do not list English or any other “full audio”
  language on a store page.
- The management HUD currently draws many hard-coded English `FString`/`TEXT`
  labels in
  [`LBControlRoomHUD.cpp`](../../Source/LineBossCarFactory/LBControlRoomHUD.cpp).
- No localization target/culture staging is present in the checked-in config.
- Vendor and PR-005 audio files are candidates; their presence is not a final
  mix, licence confirmation, subtitle implementation or package proof.

Voice acting is not required for the core management experience. Clear text,
state-driven machine audio, readable alarms and optional captions are the
priority. Synthetic or recorded voices can be evaluated later, but must not be
promised until rights, consent, disclosure, casting consistency, localization
cost and a packaged mix are approved.

## Language target

Build localization support now, then ship only languages that have completed
linguistic and in-context QA.

| Stage | UI/subtitle target | Status |
|---|---|---|
| Foundation | English source strings and localization-ready architecture | **Not complete** |
| Early Access priority | English, German, French, Spanish, Polish, Simplified Chinese, Brazilian Portuguese | Planned recommendation |
| Next wave | Japanese, Korean, Italian, Czech, Dutch, Turkish | Planned recommendation |

Seven polished translations are preferable to a long list of unreviewed machine
translations. Language count is not a quality metric.

## Localization architecture gate

- Replace player-facing `FString`/`TEXT` literals with gatherable `FText`,
  `LOCTEXT`/string-table keys and named format arguments.
- Keep stable IDs separate from translated display names.
- Do not bake essential text into textures or 3D meshes; use decals/widgets with
  localized alternatives where necessary.
- Support text expansion, wrapping and resizable panels; test German/Polish long
  strings and CJK font coverage.
- Use locale-aware numbers, money, units, date/time and plural rules.
- Provide a glossary for press, weld, paint, assembly, takt, OEE, stillage, FLT,
  AGV, starved, blocked, fault and maintenance terms.
- Localize input hints from the active binding, not hard-coded key names.
- Preserve save/telemetry IDs across languages.
- Run screenshot/in-context QA on every page, alert, inspector, tutorial and
  placement error before enabling a culture in the package/store listing.

## Audio architecture gate

Every machine, robot, AGV and FLT should expose state-driven layers rather than a
single loop:

- powered idle / HVAC / hydraulic bed;
- start, controlled stop and emergency stop;
- moving mechanism or traction loop driven by real speed/load;
- process events (press stroke, spot/MIG weld, spray, dip, fan, conveyor);
- reverse/travel warning and proximity cues;
- beacon/alarm state with rate limiting and distance mixing;
- fault, maintenance/manual and recovery transitions.

Lights and sound must read the same authoritative state: green running, amber
waiting/starved, red fault/emergency, blue maintenance/manual. Provide visual
text/icon equivalents for important audio alarms and optional captions for
off-screen process events. Avoid constant alarm fatigue.

If voice is added later:

- keep all gameplay information in text/subtitles;
- use contracted actors or a voice service with explicit commercial rights and
  documented consent—never imitate a person without permission;
- record voice/model/service provenance and exact terms;
- disclose AI-generated player-consumed audio where applicable under the current
  store policy; and
- treat each voiced language as a separately QA'd audio claim.

