#pragma once

#include "CoreMinimal.h"
#include "ToolsetRegistry/ToolsetDefinition.h"

#include "LBSpacecraftDevToolset.generated.h"

/**
 * The project's own MCP toolset (owner, 2026-09-01: "make your own mcp
 * commands for the bridge to help development"). Registered with the
 * engine's ToolsetRegistry so the editor's loopback MCP server exposes
 * it next to the stock toolsets - reachable through call_tool with the
 * namespaced toolset name (confirm the exact name with list_toolsets).
 *
 * Every function is static and runs on the game thread (the registry
 * marshals). Every function returns a JSON string: {"success": true,
 * ...} or {"success": false, "error": "..."} - never a bare value, so
 * a client can always parse one shape.
 *
 * Why these tools exist: with only the generic surface
 * (execute_python_code, capture_image), every "what is the sim doing"
 * question during the 2026-09-01 overnight session cost a screenshot
 * round-trip or a headless relaunch. These read the authorities
 * directly.
 */
UCLASS(BlueprintType)
class ULBSpacecraftDevToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	/** The whole factory as one JSON document: money, stations and
	 *  their crews, commissioning and route, track, contracts, every
	 *  unit's stage and quality state, power budget, deliveries, and
	 *  the coordinator's last start refusal. Reads the live PIE
	 *  world's authorities; refuses with success=false when no PIE
	 *  session is running. */
	UFUNCTION(BlueprintCallable, meta = (AICallable),
		Category = "LineBoss|Dev")
	static FString GetSpacecraftFactoryStatus();

	/** Runs one console command in the live PIE world (the LB.* dev
	 *  commands especially - BuildLine, Start, Speed, Save, Load,
	 *  Enter, Watch, Screenshot, After). One call, no python quoting.
	 *  Returns {"success", "command", "handled"} - handled=false means
	 *  no command processor claimed it (typo or wrong build). */
	UFUNCTION(BlueprintCallable, meta = (AICallable),
		Category = "LineBoss|Dev")
	static FString RunSpacecraftConsoleCommand(const FString& Command);

	/** Geometry of the live PIE viewport so a caller can map pixels in
	 *  a captured frame to click coordinates: {"success", "localWidth",
	 *  "localHeight", "dpiScale", "absoluteX", "absoluteY"}. Slate
	 *  local units = frame pixels / dpiScale when the capture is at
	 *  native resolution. */
	UFUNCTION(BlueprintCallable, meta = (AICallable),
		Category = "LineBoss|Dev|Input")
	static FString GetPieViewportInfo();

	/** Synthesises a mouse move + press + release inside the PIE
	 *  viewport at viewport-LOCAL Slate coordinates (see
	 *  GetPieViewportInfo), through FSlateApplication - the same path
	 *  a real mouse takes, so UMG buttons, the floor click and the
	 *  ghost placement all see it. No OS cursor is touched, so a
	 *  person can keep using the machine. Button: "Left" (default),
	 *  "Right", "Middle". */
	UFUNCTION(BlueprintCallable, meta = (AICallable),
		Category = "LineBoss|Dev|Input")
	static FString SimulatePieClick(float X, float Y,
		const FString& Button = TEXT("Left"));

	/** What a click at viewport-local X,Y would land on, WITHOUT
	 *  clicking: the hit-test path leaf-first, each widget's type, its
	 *  absolute top/bottom, and the text of any text block on the
	 *  path or directly inside the leaf's button. Built for the
	 *  2026-09-02 mystery of a click that bought the row BELOW the one
	 *  the frame showed under the pointer. */
	UFUNCTION(BlueprintCallable, meta = (AICallable),
		Category = "LineBoss|Dev|Input")
	static FString ProbePieWidgetAt(float X, float Y);

	/** Moves the synthetic pointer to viewport-local coordinates
	 *  without clicking - hover states, and the placement ghost. */
	UFUNCTION(BlueprintCallable, meta = (AICallable),
		Category = "LineBoss|Dev|Input")
	static FString SimulatePieMouseMove(float X, float Y);

	/** Presses and releases a key in the PIE viewport (FKey name, e.g.
	 *  "W", "M", "Escape", "SpaceBar", "One"). HoldSeconds > 0 keeps it
	 *  down that long for pan/zoom keys - held on a timer, so the call
	 *  returns immediately and the release lands later. */
	UFUNCTION(BlueprintCallable, meta = (AICallable),
		Category = "LineBoss|Dev|Input")
	static FString SimulatePieKey(const FString& KeyName,
		float HoldSeconds = 0.f);

	/** Mouse wheel at viewport-local coordinates; positive Delta zooms
	 *  in on this game's camera, negative out. */
	UFUNCTION(BlueprintCallable, meta = (AICallable),
		Category = "LineBoss|Dev|Input")
	static FString SimulatePieWheel(float X, float Y, float Delta);

	/** Starts PIE in its own floating window at the given size instead
	 *  of the docked level viewport (which the stock StartPIE pins,
	 *  and whose letterbox the management UI cannot live in). Returns
	 *  immediately; poll GetPieViewportInfo until it reports the new
	 *  size. Stop with the stock EditorAppToolset StopPIE. */
	UFUNCTION(BlueprintCallable, meta = (AICallable),
		Category = "LineBoss|Dev|Input")
	static FString StartPieFloating(int32 Width = 1600, int32 Height = 900);
};
