# v1031 Shipping handoff

Date: **2026-08-12**

## Outcome

`PlayerBuildable_v1031` is the first current-revision **Shipping** package. It
compiled, cooked, staged, packaged and archived successfully. It is the correct
player-facing validation lane; `PlayerBuildable_v1030` remains an internal
Development/automation package.

This is a build and listener-surface milestone, not a release-ready claim. The
packaged new-campaign, populated-factory, save/restart, accessibility and
performance journeys remain open.

## Package evidence

- UAT log:
  [`PlayerBuildable_v1031_Shipping_BuildCookRun.log`](../../Saved/Logs/PlayerBuildable_v1031_Shipping_BuildCookRun.log)
- Shipping-target build log:
  [`ShippingTarget_v1031_build.log`](../../Saved/Logs/ShippingTarget_v1031_build.log)
- Archive: `Builds/PlayerBuildable_v1031`
- Archive contents: **32 files, 1,438,734,648 bytes**
- Bootstrap executable:
  `Builds/PlayerBuildable_v1031/Windows/LineBossCarFactory.exe`
- Bootstrap SHA-256:
  `68B5A997BAAB259678CE6C1222E0D4DC39D35512CBCBF810E41CEFE3BD849FB4`
- Inner Shipping executable:
  `Builds/PlayerBuildable_v1031/Windows/LineBossCarFactory/Binaries/Win64/LineBossCarFactory-Win64-Shipping.exe`
- Inner executable SHA-256:
  `61CA92BA0B7C5A9774BFCC12CAF9936DDBAFB82B8812B731A3605134283D904C`
- Microsoft x64 and ARM64 VC++ redistributables are staged.

## Network-surface finding

The Windows Security firewall dialog visible over the v1031 game was **not
created by v1031 Shipping**. It was the still-open v1030 Development dialog.

- The dialog host and v1030 TCP/UDP block-rule events started at **03:38:53**.
- v1031 Shipping did not start until **04:12:45**.
- Five read-only samples found zero TCP listeners and zero UDP endpoints for
  both v1031 processes.
- Windows recorded no v1031 firewall event or active v1031 application rule.
- The Shipping binary lacks the Development Trace-control, UDP-bind and TCP
  Messaging diagnostic strings checked during the package gate.

The complete evidence and limitations are in
[`Shipping_Firewall_Runtime_Audit.md`](../../Saved/Audits/ReleaseGate/v1031/Shipping_Firewall_Runtime_Audit.md).
The screenshot showing the stale dialog is retained only as diagnostic evidence
under `Saved/Audits/ReleaseGate/v1031/firewall_runtime`.

Do not click **Allow**. The user may cancel the stale v1030 prompt in the
morning; it is not required by single-player gameplay or the file-based
Development automation bridge.

## Target/plugin boundary

- Editor-only: Unreal MCP, ToolsetRegistry, AllToolsets, Datasmith importers,
  editor validation/profiling tools and UDP Messaging used by Datasmith.
- Packaged runtime: no MCP, Datasmith, UDP Messaging or TCP Messaging.
- `TcpMessaging` is explicitly disabled.
- `UdpMessaging` is explicitly Editor-scoped so Datasmith's real dependency is
  described truthfully without leaking it into Shipping.
- Enhanced Input remains runtime-enabled.
- Interchange/InterchangeAssets remain runtime-enabled pending a separate
  cooked-asset metadata audit; they must not be scoped blindly.

## Next packaged gates

1. Cancel the stale v1030 firewall dialog manually, then relaunch v1031 with a
   fresh `-UserDir` and confirm no new prompt or endpoint.
2. Capture the mandatory factory identity/livery flow and first Build page at
   1280x720, 1920x1080 and 4K/UI scale.
3. Exercise actual placement with recognisable model ghost, invalid obstruction
   guidance, rotation and recovery.
4. Run a populated package journey through inbound, press, inspection, full
   stillage and physical FLT delivery to weld intake.
5. Save, exit the process, relaunch, load and complete the next gameplay event.
6. Exercise all seven management pages with mouse, keyboard and controller.
7. Capture representative CPU/GPU frame time, memory and navigation/pathing
   evidence before promoting v1031 beyond development milestone status.

